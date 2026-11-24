"""Valida a integração sem acessar o portal nem usar música licenciada."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from licensed_music import _request, prepare_music

class LicensedMusicTest(unittest.TestCase):
    def test_unconfigured(self):
        with patch.dict(os.environ, {'ANR_SOUNDTRACK_URL': ''}):
            self.assertFalse(prepare_music(28, 'unused.wav'))

    def test_auth_and_origin(self):
        req = _request('https://terradeherois.com.br/private/shield.mp3', 'user:pass')
        self.assertEqual(req.get_header('Authorization'), 'Basic dXNlcjpwYXNz')
        for url in ('http://terradeherois.com.br/private/shield.mp3',
                    'https://other.example/shield.mp3',
                    'https://terradeherois.com.br.evil.example/shield.mp3'):
            with self.assertRaises(ValueError):
                _request(url, 'user:pass')
        with self.assertRaises(ValueError):
            _request('https://terradeherois.com.br/private/shield.mp3', '')

    def test_public_m4a_from_portal(self):
        req = _request('https://terradeherois.com.br/wp-content/uploads/2026/11/music.m4a', '')
        self.assertIsNone(req.get_header('Authorization'))
        for url in ('https://other.example/wp-content/uploads/music.m4a',
                    'https://terradeherois.com.br/wp-content/uploads/../music.m4a',
                    'https://terradeherois.com.br/wp-content/uploads/music.exe'):
            with self.assertRaises(ValueError):
                _request(url, '')
