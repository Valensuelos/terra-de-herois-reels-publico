"""Renderiza vídeo MP4 próprio do portal, priorizando sempre seu áudio original."""
import json
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

LIMIT_VIDEO_BYTES = 95 * 1024 * 1024
WIDTH, HEIGHT = 1080, 1920
VIDEO_TOP = 403
VIDEO_BOTTOM = 1151

def allowed_url(url):
    u = urllib.parse.urlsplit(str(url or ''))
    if (u.scheme != 'https' or u.hostname not in ('terradeherois.com.br', 'www.terradeherois.com.br')
            or u.port not in (None, 443) or u.username or u.password or u.query or u.fragment
            or not u.path.lower().endswith('.mp4') or '/wp-content/uploads/' not in u.path
            or '..' in urllib.parse.unquote(u.path)):
        raise ValueError('MP4 deve estar no diretório de uploads HTTPS do Terra de Heróis.')
    return url

def download_video(url, dest='source.mp4'):
    url = allowed_url(url)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            raise ValueError('O servidor redirecionou o MP4; use URL canônica HTTPS.')
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={'User-Agent': 'Terra-Reels-Renderer/1.2'})
    total = 0
    with opener.open(req, timeout=90) as res, open(dest, 'wb') as fout:
        size = res.headers.get('Content-Length')
        if size and int(size) > LIMIT_VIDEO_BYTES:
            raise ValueError('Vídeo de origem maior que 95 MB.')
        while True:
            data = res.read(1024*1024)
            if not data:
                break
            total += len(data)
            if total > LIMIT_VIDEO_BYTES:
                raise ValueError('Vídeo de origem maior que 95 MB.')
            fout.write(data)
    if total < 4096:
        raise ValueError('Arquivo de vídeo não foi recebido corretamente.')
    return dest

def _probe_ffmpeg_output(output):
    """Metadados essenciais a partir da saída do FFmpeg (sem ffprobe)."""
    has_video = bool(re.search(r'^\s*Stream #\S+.*Video:', output, re.MULTILINE))
    has_audio = bool(re.search(r'^\s*Stream #\S+.*Audio:', output, re.MULTILINE))
    duration_match = re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)', output)
    duration = 0.0
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return duration, has_video, has_audio


def probe_video(path):
    """Utiliza ffprobe quando disponível; caso contrário lê o cabeçalho com ffmpeg."""
    if shutil.which('ffprobe'):
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration:stream=codec_type', '-of', 'json', path],
            text=True, capture_output=True, timeout=30, check=True)
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        has_video = any(s.get('codec_type') == 'video' for s in streams)
        has_audio = any(s.get('codec_type') == 'audio' for s in streams)
        duration = float(data.get('format', {}).get('duration', 0))
    else:
        result = subprocess.run(['ffmpeg', '-hide_banner', '-i', path],
                                text=True, capture_output=True, timeout=30)
        duration, has_video, has_audio = _probe_ffmpeg_output(result.stderr)
    if not has_video or not (3 <= duration <= 3600):
        raise ValueError('Vídeo inválido, sem duração válida ou maior que uma hora.')
    return duration, has_audio


def extract_photo(source, target='source-poster.jpg'):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                    '-ss', '0.5', '-i', source, '-frames:v', '1', target],
                   check=True, timeout=40)
    img = Image.open(target).convert('RGBA')
    img.load()
    return img

def make_overlay(frame='frame.png', target='overlay.png'):
    """Preserva o cabeçalho e os painéis; abre janela para vídeo em movimento."""
    im = Image.open(frame).convert('RGBA')
    if im.size != (WIDTH, HEIGHT):
        raise ValueError('A arte precisa ter 1080 x 1920 pixels.')
    dr = ImageDraw.Draw(im)
    dr.rectangle((0, VIDEO_TOP, WIDTH, VIDEO_BOTTOM), fill=(0, 0, 0, 0))
    # Recoloca a divisão curva do cabeçalho por cima do vídeo.
    dr.polygon([(0,399),(0,445),(160,420),(510,439),(820,433),
                (1080,397),(1080,384),(0,384)], fill='#082764')
    dr.line([(0,420),(260,428),(540,438),(850,429),(1080,410)],
            fill='#00dafa', width=7, joint='curve')
    # Transição da área de vídeo para o selo editorial.
    for y in range(973, VIDEO_BOTTOM + 1, 2):
        a = min(230, int(230*((y-973)/(VIDEO_BOTTOM-973))**1.65))
        dr.rectangle((0, y, WIDTH, min(VIDEO_BOTTOM, y+1)),
                     fill=(1,12,42,a))
    dr.polygon([(20,1077),(513,1077),(487,1159),(5,1159)], fill='#061435')
    dr.polygon([(25,1072),(509,1072),(483,1148),(3,1148)], fill='#ffd91e')
    ft = None
    for candidate in (
        '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf',
        'DejaVuSansCondensed-BoldOblique.ttf', 'DejaVuSans-Bold.ttf'
    ):
        try:
            ft = ImageFont.truetype(candidate, 47)
            break
        except OSError:
            pass
    if ft is None:
        ft = ImageFont.load_default(size=47)
    dr.text((44,1090), 'ÚLTIMAS NOTÍCIAS', font=ft, fill='#041b47', stroke_width=1)
    for x in (522,564,606):
        dr.polygon([(x,1088),(x+24,1088),(x-4,1140),(x-28,1140)], fill='#04e6f5')
    im.save(target)
    return target


def render_video(source='source.mp4', frame='frame.png', target='reel.mp4',
                 seconds=28, music=True):
    duration, has_audio = probe_video(source)
    duration = min(45.0, max(3.0, float(seconds)), duration)
    overlay = make_overlay(frame)
    inputs = ['-i', source, '-loop', '1', '-framerate', '20', '-i', overlay]
    if has_audio:
        audio_map = '0:a:0'
        print('Vídeo com áudio original: Breaking News desativada.')
    else:
        if music:
            from soundtrack import make_music
            inputs += ['-i', make_music(int(max(20, duration)))]
        else:
            inputs += ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100']
        audio_map = '2:a:0'
        print('Vídeo sem áudio: usando trilha Breaking News.' if music else 'Vídeo sem áudio: faixa silenciosa.')
    graph = (
        f'[0:v]scale={WIDTH}:{VIDEO_BOTTOM-VIDEO_TOP}:force_original_aspect_ratio=increase,'
        f'crop={WIDTH}:{VIDEO_BOTTOM-VIDEO_TOP},setsar=1,'
        'eq=contrast=1.08:brightness=0.012:saturation=1.11,'
        'unsharp=5:5:0.45:3:3:0.0,'
        f'pad={WIDTH}:{HEIGHT}:0:{VIDEO_TOP}:color=black,format=rgba[base];'
        '[1:v]format=rgba[ui];'
        '[base][ui]overlay=0:0:format=auto:shortest=1,format=yuv420p[outv]'
    )
    args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + inputs + [
        '-filter_complex', graph, '-map', '[outv]', '-map', audio_map,
        '-t', str(round(duration, 2)), '-r', '20', '-c:v', 'libx264',
        '-preset', 'fast', '-crf', '21', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '2',
        '-movflags', '+faststart', '-shortest', target,
    ]
    subprocess.run(args, check=True, timeout=600)
    filesize = Path(target).stat().st_size
    if not (15000 <= filesize <= 45*1024*1024):
        raise ValueError('Reels gerado excede limite de 45 MB do WordPress.')
    with open(target, 'rb') as f:
        if f.read(12)[4:8] != b'ftyp':
            raise ValueError('Cabeçalho inválido de arquivo MP4.')
    return filesize
