"""Testes locais para a qualidade fotográfica (sem WordPress ou tokens)."""
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from photo_quality import prepare_photo


class PhotoQualityTests(unittest.TestCase):
    def sample(self, width=1200, height=800):
        image = Image.new('RGB', (width, height), '#7f8fa4')
        draw = ImageDraw.Draw(image)
        draw.rectangle((100, 100, width//2, height-100), fill=(60, 98, 132))
        draw.rectangle((width//2, 100, width-100, height-100), fill=(166, 135, 86))
        return image

    def test_size_alpha_and_source_unchanged(self):
        original = self.sample()
        original_pixel = original.getpixel((50, 50))
        result = prepare_photo(original, (1080, 737))
        self.assertEqual(result.size, (1080, 737))
        self.assertEqual(result.mode, 'RGBA')
        self.assertEqual(result.getchannel('A').getextrema(), (255, 255))
        self.assertEqual(original.getpixel((50, 50)), original_pixel)

    def test_contrast_increases_moderately(self):
        original = self.sample()
        baseline = ImageOps.fit(original, (1080, 737), method=Image.Resampling.LANCZOS)
        enhanced = prepare_photo(original, (1080, 737)).convert('RGB')
        before = ImageStat.Stat(baseline.convert('L')).stddev[0]
        after = ImageStat.Stat(enhanced.convert('L')).stddev[0]
        self.assertGreater(after, before)
        self.assertLess(after / before, 1.3)

    def test_small_photo_upscales_without_exception(self):
        result = prepare_photo(self.sample(280, 220), (1080, 737))
        self.assertEqual(result.size, (1080, 737))


if __name__ == '__main__':
    unittest.main()
