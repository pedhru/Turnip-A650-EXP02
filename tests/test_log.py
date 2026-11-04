import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from analyze_log import analyze


class LogAnalyzerTests(unittest.TestCase):
    def test_counts_relevant_messages(self):
        result = analyze('I Turnip starting\nE Vulkan VK_ERROR_DEVICE_LOST\nF fatal signal 11\n')
        self.assertEqual(result['matches']['driver_library'], 1)
        self.assertEqual(result['matches']['device_lost'], 1)
        self.assertEqual(result['matches']['fatal'], 1)

    def test_empty_file(self):
        result = analyze('')
        self.assertEqual(result['total_lines'], 0)
        self.assertFalse(result['matches'])
