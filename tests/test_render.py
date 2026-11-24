"""Verificações locais que não usam WordPress nem credenciais."""
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render


class RenderUnitTest(unittest.TestCase):
    def test_site_url(self):
        self.assertEqual(render.ensure_site('https://terradeherois.com.br/'),
                         'https://terradeherois.com.br')
        with self.assertRaises(ValueError):
            render.ensure_site('http://terradeherois.com.br')
        with self.assertRaises(ValueError):
            render.ensure_site('https://terradeherois.com.br.evil.test')

    def test_image_domain(self):
        self.assertEqual(
            render.ensure_media_url('https://terradeherois.com.br/wp-content/uploads/photo.jpg'),
            'https://terradeherois.com.br/wp-content/uploads/photo.jpg')
        with self.assertRaises(ValueError):
            render.ensure_media_url('https://127.0.0.1/secret')
        with self.assertRaises(ValueError):
            render.ensure_media_url('http://terradeherois.com.br/uploads/image.jpg')

    def test_content_wrap(self):
        canvas = Image.new('RGB', (render.WIDTH, render.HEIGHT))
        painter = render.ImageDraw.Draw(canvas)
        lines = render.wrapped_lines(painter, 'Notícia ' * 120, render.font(40), 700, 3)
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[-1].endswith('…'))

    def test_create_frame(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / 'frame.png')
            photo = Image.new('RGBA', (1400, 900), '#4c8db2')
            meta = {'title': 'Teste de reportagem do portal',
                    'summary': 'Resumo curto para o Reels.'}
            render.make_frame(meta, path=path, photo=photo)
            with Image.open(path) as img:
                self.assertEqual(img.size, (1080, 1920))


if __name__ == '__main__':
    unittest.main()
