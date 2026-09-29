#!/usr/bin/env python3
"""Tests for the firmware facts: the PIN reference and the storage cipher

These pin the reverse-engineered constants against the real flash dump. A wrong
constant makes the sniffed PIN wrong or the decrypted volume unreadable
"""
import unittest
from pathlib import Path

import firmware
import run_demo

DUMP = Path(__file__).resolve().parent / "data" / "backup_full.bin"


class ExtractPinTests(unittest.TestCase):
    def test_reads_the_real_reference(self):
        self.assertEqual(firmware.extract_pin(DUMP), "3952")


class DecryptStorageTests(unittest.TestCase):
    def test_sector_zero_is_a_fat12_boot_sector(self):
        plain = firmware.decrypt(DUMP)
        self.assertEqual(plain[0:3], bytes([0xEB, 0x3C, 0x90]))  # x86 jump
        self.assertEqual(plain[3:11], b"MSDOS5.0")               # OEM name
        self.assertEqual(plain[510:512], bytes([0x55, 0xAA]))    # boot signature


class VolumeContentsTests(unittest.TestCase):
    def test_root_lists_the_prize_with_its_long_name(self):
        files = run_demo.root_files(firmware.decrypt(DUMP))
        self.assertIn("your_prize.zip", files)

    def test_summary_highlights_the_zip(self):
        summary = run_demo.decrypt_summary(DUMP)
        self.assertEqual(summary["artifact"], "your_prize.zip")
        self.assertTrue(summary["is_zip"])


if __name__ == "__main__":
    unittest.main()
