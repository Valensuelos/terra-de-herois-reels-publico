"""Carrega a trilha licenciada de armazenamento privado do portal."""
import base64
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024
HOSTS = ('terradeherois.com.br', 'www.terradeherois.com.br')


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirecionamento da trilha não permitido.')


def _request(url, auth):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in HOSTS
            or parsed.port not in (None, 443) or parsed.username
            or parsed.password or parsed.fragment or parsed.query
            or not parsed.path.lower().endswith('.mp3')):
        raise ValueError('URL privada da trilha inválida.')
    if not auth or ':' not in auth or not auth.split(':', 1)[0]:
        raise ValueError('Autenticação da trilha não configurada.')
    token = base64.b64encode(auth.encode('utf-8')).decode('ascii')
    return urllib.request.Request(url, headers={
        'Authorization': 'Basic ' + token,
        'User-Agent': 'Terra-Reels-Renderer/1.3',
    })


def prepare_music(seconds, filename):
    """Retorna False sem configuração; falhas são tratadas pelo chamador."""
    url = os.environ.get('ANR_SOUNDTRACK_URL', '').strip()
    if not url:
        return False
    auth = os.environ.get('ANR_SOUNDTRACK_AUTH', '')
    req = _request(url, auth)
    duration = max(3.0, min(45.0, float(seconds)))
    fade_start = max(0.0, duration-1.2)
    opener = urllib.request.build_opener(_NoRedirect)
    with tempfile.TemporaryDirectory(prefix='anr-music-') as tmp:
        source = Path(tmp)/'source.mp3'
        target = Path(tmp)/'music.wav'
        with opener.open(req, timeout=15) as response:
            data = response.read(MAX_BYTES+1)
        if not 1024 <= len(data) <= MAX_BYTES:
            raise ValueError('Tamanho inválido da trilha.')
        source.write_bytes(data)
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
            '-stream_loop', '-1', '-i', str(source), '-map', '0:a:0',
            '-t', str(duration),
            '-af', f'volume=0.72,afade=t=in:d=0.20,afade=t=out:st={fade_start:.3f}:d=1.20',
            '-ac', '2', '-ar', '44100', '-c:a', 'pcm_s16le', str(target)
        ], check=True, timeout=45, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Path(filename).write_bytes(target.read_bytes())
    return True
