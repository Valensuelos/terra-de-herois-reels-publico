#!/usr/bin/env python3
"""Renderizador de Reels Terra de Heróis.

Obtém metadados autenticados do WordPress, gera MP4 vertical H.264/AAC
(com áudio silencioso) e devolve o vídeo via HTTPS. Sem credenciais no código.
"""
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

WIDTH, HEIGHT = 1080, 1920
MAX_IMAGE_BYTES = 18 * 1024 * 1024
MAX_MP4_BYTES = 45 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 35_000_000
HEADERS = {'User-Agent': 'Terra-Reels-Renderer/1.0'}


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    """Não seguir redirecionamentos que poderiam perder Authorization."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('URL redirecionada. Informe a URL canônica HTTPS do WordPress.')


OPENER = urllib.request.build_opener(RejectRedirect)


def ensure_site(url):
    p = urllib.parse.urlsplit((url or '').strip())
    if (p.scheme != 'https' or not p.hostname or p.port not in (None, 443)
            or p.username or p.password or p.query or p.fragment
            or p.path not in ('', '/')):
        raise ValueError('ANR_SITE_URL deve ser a URL HTTPS canônica do portal, sem caminho.')
    if p.hostname.lower() not in ('terradeherois.com.br', 'www.terradeherois.com.br'):
        raise ValueError('ANR_SITE_URL não pertence ao Terra de Heróis.')
    return 'https://' + p.hostname.lower()


def ensure_media_url(url):
    p = urllib.parse.urlsplit(url or '')
    if (p.scheme != 'https' or not p.hostname or p.port not in (None, 443)
            or p.username or p.password or p.hostname.lower() not in
            ('terradeherois.com.br', 'www.terradeherois.com.br')):
        raise ValueError('Imagem fora do domínio autorizado do Terra de Heróis.')
    return url


def fetch(url, token=None, data=None, content_type=None, max_bytes=None):
    headers = dict(HEADERS)
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if content_type:
        headers['Content-Type'] = content_type
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method='POST' if data is not None else 'GET')
    with OPENER.open(req, timeout=90 if data is not None else 45) as res:
        if max_bytes is None:
            return res.read()
        declared = res.headers.get('Content-Length')
        if declared and int(declared) > max_bytes:
            raise ValueError('Arquivo maior que o limite permitido.')
        payload = res.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError('Arquivo maior que o limite permitido.')
        return payload


def image_from_url(url):
    data = fetch(ensure_media_url(url), max_bytes=MAX_IMAGE_BYTES)
    img = Image.open(io.BytesIO(data))
    img.load()
    if img.width * img.height > Image.MAX_IMAGE_PIXELS:
        raise ValueError('Imagem com dimensões excessivas.')
    return img.convert('RGBA')


def font(size, bold=False):
    filename = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/' + filename, size)


def safe_text(value, max_len=1000):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    return ''.join(c for c in text if c.isprintable())[:max_len]


def wrapped_lines(draw, value, fnt, max_width, limit):
    words = safe_text(value).split()
    lines, line = [], ''
    for word in words:
        candidate = (line + ' ' + word).strip()
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= max_width:
            line = candidate
            continue
        if line:
            lines.append(line)
            line = ''
        chunks = []
        while word:
            i = len(word)
            while i > 1 and draw.textbbox((0, 0), word[:i], font=fnt)[2] > max_width:
                i -= 1
            chunks.append(word[:i])
            word = word[i:]
        for chunk in chunks[:-1]:
            lines.append(chunk)
        line = chunks[-1] if chunks else ''
    if line:
        lines.append(line)
    if len(lines) > limit:
        lines = lines[:limit]
        trimmed = lines[-1]
        while trimmed and draw.textbbox((0, 0), trimmed + '…', font=fnt)[2] > max_width:
            trimmed = trimmed[:-1]
        lines[-1] = trimmed.rstrip() + '…'
    return lines


def write_lines(draw, text, y, fnt, count, fill, max_width=940, line_h=None):
    delta = line_h or int(fnt.size * 1.26)
    for index, line in enumerate(wrapped_lines(draw, text, fnt, max_width, count)):
        bounds = draw.textbbox((0, 0), line, font=fnt)
        x = (WIDTH - (bounds[2] - bounds[0])) // 2
        draw.text((x, y + index * delta), line, fill=fill, font=fnt,
                  stroke_width=2, stroke_fill='#06132d')


def make_frame(meta, path='frame.png', photo=None, logo=None):
    """Novo layout editorial sem alterar a interface da API WordPress."""
    from news_layout import make_news_frame
    return make_news_frame(meta, path, photo, logo, image_from_url,
                           safe_text, font, wrapped_lines, write_lines)

def render_mp4(frame='frame.png', path='reel.mp4', seconds=28):
    duration = max(20, min(45, int(seconds)))
    music = os.environ.get('ANR_MUSIC_ENABLED', 'true').strip().lower() not in (
        'false', '0', 'off', 'no')
    if music:
        from soundtrack import make_music
        audio_input = ['-i', make_music(duration)]
    else:
        audio_input = ['-f', 'lavfi', '-i',
                       'anullsrc=channel_layout=stereo:sample_rate=44100']
    args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
            '-loop', '1', '-framerate', '20', '-i', frame] + audio_input + [
            '-t', str(duration), '-c:v', 'libx264', '-preset', 'veryfast',
            '-crf', '26', '-pix_fmt', 'yuv420p', '-r', '20', '-c:a', 'aac',
            '-b:a', '112k', '-ar', '44100', '-ac', '2',
            '-movflags', '+faststart', '-shortest', path]
    subprocess.run(args, check=True, timeout=600)
    size = Path(path).stat().st_size
    if not (15000 <= size <= MAX_MP4_BYTES):
        raise ValueError('MP4 gerado com tamanho fora do limite (45 MB).')
    with open(path, 'rb') as f:
        if f.read(12)[4:8] != b'ftyp':
            raise ValueError('MP4 gerado não possui cabeçalho correto.')
    return size


def main():
    site = ensure_site(os.environ.get('ANR_SITE_URL', ''))
    token = os.environ.get('ANR_SHARED_SECRET', '')
    job_id = os.environ.get('ANR_JOB_ID', '')
    if len(token) < 24 or not re.fullmatch(r'[0-9]{1,10}', job_id):
        raise ValueError('Verifique ANR_SHARED_SECRET e o ID numérico do Reels.')
    endpoint = site + '/wp-json/anr/v1/job/' + job_id
    metadata = json.loads(fetch(endpoint, token=token, max_bytes=40_000))
    if int(metadata.get('id', 0)) != int(job_id):
        raise ValueError('O ID retornado pelo WordPress é diferente do solicitado.')
    make_frame(metadata)
    size = render_mp4(seconds=metadata.get('seconds', 28))
    print('Vídeo MP4 criado (bytes):', size)
    with open('reel.mp4', 'rb') as f:
        response = json.loads(fetch(endpoint + '/upload', token=token, data=f.read(),
                                    content_type='video/mp4', max_bytes=40_000))
    if response.get('ok') is not True:
        raise ValueError('O WordPress não confirmou o recebimento do MP4.')
    print('WordPress confirmou recebimento do MP4; status:', safe_text(response.get('state'), 60))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Falha no renderizador:', str(exc), file=sys.stderr)
        sys.exit(1)
