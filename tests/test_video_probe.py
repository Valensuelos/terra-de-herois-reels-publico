"""Testes do reconhecimento de áudio original sem utilitário ffprobe."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import video_media


SAMPLE = """
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'source.mp4':
  Metadata:
    major_brand     : isom
  Duration: 00:00:29.32, start: 0.000000, bitrate: 856 kb/s
  Stream #0:0[0x1](und): Video: h264 (Main), yuv420p, 1280x720, 30 fps
  Stream #0:1[0x2](por): Audio: aac (LC), 44100 Hz, stereo, fltp
"""
VIDEO_ONLY = SAMPLE.replace(
    '  Stream #0:1[0x2](por): Audio: aac (LC), 44100 Hz, stereo, fltp\n', ''
)


class ProbeVideoTests(unittest.TestCase):
    def test_audio_and_duration(self):
        self.assertEqual(video_media._probe_ffmpeg_output(SAMPLE),
                         (29.32, True, True))

    def test_video_without_audio(self):
        self.assertEqual(video_media._probe_ffmpeg_output(VIDEO_ONLY),
                         (29.32, True, False))

    @patch('video_media.shutil.which', return_value=None)
    @patch('video_media.subprocess.run')
    def test_ffmpeg_fallback_when_ffprobe_absent(self, run, _):
        run.return_value = SimpleNamespace(stderr=SAMPLE, returncode=1)
        self.assertEqual(video_media.probe_video('source.mp4'), (29.32, True))
        self.assertEqual(run.call_args.args[0][:3], ['ffmpeg', '-hide_banner', '-i'])

    @patch('video_media.shutil.which', return_value=None)
    @patch('video_media.subprocess.run')
    def test_rejects_invalid_video(self, run, _):
        run.return_value = SimpleNamespace(stderr='Invalid data found', returncode=1)
        with self.assertRaises(ValueError):
            video_media.probe_video('source.mp4')


if __name__ == '__main__':
    unittest.main()
