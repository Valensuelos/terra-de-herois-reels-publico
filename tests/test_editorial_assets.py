"""Regressões do endereço e da nova trilha, sem acesso ao portal."""
import array
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from approved_skin import _draw_site_address
from soundtrack import make_music, SAMPLE_RATE


class EditorialAssetsTest(unittest.TestCase):
    def test_address_stays_inside_balloon(self):
        rect = (262, 1677, 815, 1724)
        canvas = Image.new('RGB', (1080, 1920), '#052451')
        original = canvas.copy()
        _draw_site_address(ImageDraw.Draw(canvas), rect)
        bounds = ImageChops.difference(canvas, original).getbbox()
        self.assertIsNotNone(bounds)
        x0, y0, x1, y1 = bounds
        self.assertGreaterEqual(x0, rect[0]+16)
        self.assertLessEqual(x1, rect[2]-16)
        self.assertGreaterEqual(y0, rect[1]+6)
        self.assertLessEqual(y1, rect[3]-6)
        self.assertLessEqual(abs((x0+x1)-(rect[0]+rect[2])), 5)
        self.assertLessEqual(abs((y0+y1)-(rect[1]+rect[3])), 5)

    def test_music_pcm_duration_and_headroom(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp)/'music.wav')
            self.assertEqual(make_music(20, path), path)
            with wave.open(path, 'rb') as source:
                self.assertEqual(source.getnchannels(), 1)
                self.assertEqual(source.getsampwidth(), 2)
                self.assertEqual(source.getframerate(), SAMPLE_RATE)
                self.assertEqual(source.getnframes(), 20*SAMPLE_RATE)
                pcm = array.array('h', source.readframes(source.getnframes()))
            if sys.byteorder != 'little':
                pcm.byteswap()
            self.assertGreater(max(map(abs, pcm)), 1000)
            self.assertLess(max(map(abs, pcm)), 32767)
            self.assertLess(max(map(abs, pcm[-220:])), 300)
