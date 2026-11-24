"""Regressões do resumo e da trilha, sem acesso ao portal."""
import array
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from approved_skin import _draw_summary, make_official_frame
from soundtrack import make_music, SAMPLE_RATE


class EditorialAssetsTest(unittest.TestCase):
    def test_summary_uses_four_lines_and_stays_inside_panel(self):
        canvas = Image.new('RGB', (1080, 1920), '#052451')
        original = canvas.copy()
        rows = _draw_summary(ImageDraw.Draw(canvas), 'Notícia importante para os moradores. ' * 20)
        self.assertEqual(len(rows), 4)
        self.assertTrue(rows[-1].endswith('…'))
        x0, y0, x1, y1 = ImageChops.difference(canvas, original).getbbox()
        self.assertGreaterEqual(x0, 262)
        self.assertLessEqual(x1, 1054)
        self.assertGreaterEqual(y0, 1509)
        self.assertLessEqual(y1, 1719)
        self.assertGreater(y1, 1677)

    def test_official_frame_removes_balloon_and_preserves_footer(self):
        skin = Image.new('RGBA', (1080, 1920), '#09306b')
        draw = ImageDraw.Draw(skin)
        draw.rectangle((0, 410, 1079, 1146), fill=(0, 0, 0, 0))
        draw.rectangle((0, 1731, 1079, 1919), fill='#ffdf22')
        photo = Image.new('RGBA', (1080, 737), '#4c8db2')
        meta = {'template_url': 'test', 'title': 'Teste', 'summary': 'Resumo curto.'}
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp)/'frame.png')
            self.assertTrue(make_official_frame(meta, path, photo,
                            lambda url: skin, lambda value, limit: value[:limit]))
            with Image.open(path) as rendered:
                self.assertEqual(rendered.getpixel((262, 1700)), (9, 48, 107))
                self.assertEqual(rendered.getpixel((815, 1700)), (9, 48, 107))
                self.assertEqual(rendered.getpixel((500, 1820)), (255, 223, 34))

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
