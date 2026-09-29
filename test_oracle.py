#!/usr/bin/env python3
"""Tests for the timing-oracle model"""
import random
import unittest

import oracle


class MatchingPrefixTests(unittest.TestCase):
    def test_counts_the_leading_run(self):
        ref = (3, 9, 5, 2)
        self.assertEqual(oracle.matching_prefix((0, 0, 0, 0), ref), 0)
        self.assertEqual(oracle.matching_prefix((3, 0, 0, 0), ref), 1)
        self.assertEqual(oracle.matching_prefix((3, 9, 0, 0), ref), 2)
        self.assertEqual(oracle.matching_prefix((3, 9, 5, 0), ref), 3)
        self.assertEqual(oracle.matching_prefix((3, 9, 5, 2), ref), 4)

    def test_a_later_match_does_not_resume_the_run(self):
        # the firmware stops at the first wrong digit, so a match after it is lost
        self.assertEqual(oracle.matching_prefix((3, 0, 5, 2), (3, 9, 5, 2)), 1)


class OracleTests(unittest.TestCase):
    def test_sniff_reports_acceptance_and_prefix(self):
        ora = oracle.Oracle((3, 9, 5, 2))
        self.assertEqual(ora.sniff((3, 9, 5, 0)), (False, 3))
        self.assertEqual(ora.sniff((3, 9, 5, 2)), (True, 4))

    def test_freeze_is_the_leaked_delay(self):
        # the safe holds its outputs frozen 50 ms per matching leading digit
        ora = oracle.Oracle((3, 9, 5, 2))
        self.assertEqual(ora.freeze_ms((0, 0, 0, 0)), 0)
        self.assertEqual(ora.freeze_ms((3, 9, 0, 0)), 2 * oracle.STEP_MS)
        self.assertEqual(ora.freeze_ms((3, 9, 5, 2)), 4 * oracle.STEP_MS)


class MeasureTests(unittest.TestCase):
    def test_no_noise_reads_the_exact_delay(self):
        ora = oracle.Oracle((3, 9, 5, 2), noise_ms=0)
        rng = random.Random(0)
        self.assertEqual(ora.measure((0, 0, 0, 0), rng), 0.0)
        self.assertEqual(ora.measure((3, 9, 0, 0), rng), 100.0)
        self.assertEqual(ora.measure((3, 9, 5, 2), rng), 200.0)

    def test_noise_centres_on_the_true_delay_and_never_goes_negative(self):
        ora = oracle.Oracle((3, 9, 5, 2), noise_ms=20)
        rng = random.Random(1)
        samples = [ora.measure((3, 9, 0, 0), rng) for _ in range(5000)]
        self.assertTrue(all(s >= 0 for s in samples))
        mean = sum(samples) / len(samples)
        self.assertAlmostEqual(mean, 100.0, delta=3.0)

    def test_noise_actually_spreads_the_reads(self):
        ora = oracle.Oracle((3, 9, 5, 2), noise_ms=20)
        rng = random.Random(2)
        samples = [ora.measure((3, 9, 0, 0), rng) for _ in range(2000)]
        self.assertGreater(len(set(samples)), 100)


if __name__ == "__main__":
    unittest.main()
