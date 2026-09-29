#!/usr/bin/env python3
"""Tests for the fly chemotaxis agent"""
import statistics
import unittest

import oracle
from fly import Fly

TARGETS = [(3, 9, 5, 2), (0, 0, 0, 0), (9, 9, 9, 9), (1, 4, 7, 3)]


class HuntTests(unittest.TestCase):
    def test_reaches_each_target(self):
        for target in TARGETS:
            for seed in (1, 42, 1000):
                trace = Fly(oracle.Oracle(target), seed=seed).hunt()
                last = trace[-1]
                self.assertTrue(
                    last["accepted"],
                    msg=f"fly failed to open target {target} with seed {seed}",
                )
                self.assertEqual(tuple(last["candidate"]), target)
                # only the final sniff is the opened PIN
                self.assertEqual(sum(s["accepted"] for s in trace), 1)

    def test_recorded_readings_are_real_oracle_output(self):
        # the animation replays these frames, so each must be a true sniff
        target = (3, 9, 5, 2)
        trace = Fly(oracle.Oracle(target), seed=7).hunt()
        for step in trace:
            cand = tuple(step["candidate"])
            k = oracle.matching_prefix(cand, target)
            self.assertEqual(step["k"], k)
            self.assertEqual(step["freeze_ms"], k * oracle.STEP_MS)
            self.assertEqual(step["accepted"], k == 4)

    def test_positions_decode_back_to_the_candidate(self):
        # the 2D field cell and the sniffed PIN cannot drift apart
        trace = Fly(oracle.Oracle((3, 9, 5, 2)), seed=3).hunt()
        for step in trace:
            x, y = step["x"], step["y"]
            self.assertEqual(
                (x // 10, x % 10, y // 10, y % 10), tuple(step["candidate"]),
            )

    def test_locked_prefix_never_regresses(self):
        # the fly keeps every digit it has confirmed; best odor only grows
        trace = Fly(oracle.Oracle((3, 9, 5, 2)), seed=5).hunt()
        best = [s["best_k"] for s in trace]
        self.assertEqual(best, sorted(best))
        self.assertEqual(best[-1], 4)

    def test_is_deterministic_per_seed(self):
        ora = oracle.Oracle((3, 9, 5, 2))
        a = [s["candidate"] for s in Fly(ora, seed=99).hunt()]
        b = [s["candidate"] for s in Fly(ora, seed=99).hunt()]
        self.assertEqual(a, b)
        c = [s["candidate"] for s in Fly(ora, seed=123).hunt()]
        self.assertNotEqual(a, c)


class NoiseTests(unittest.TestCase):
    TARGET = (3, 9, 5, 2)

    def test_still_opens_under_modest_noise(self):
        for seed in (1, 42, 1000, 7):
            trace = Fly(oracle.Oracle(self.TARGET, noise_ms=10), seed=seed).hunt()
            self.assertTrue(trace[-1]["accepted"], msg=f"seed {seed} did not open")
            self.assertEqual(tuple(trace[-1]["candidate"]), self.TARGET)

    def test_measured_read_equals_true_delay_without_noise(self):
        for step in Fly(oracle.Oracle(self.TARGET), seed=3).hunt():
            self.assertEqual(step["measured_ms"], step["k"] * oracle.STEP_MS)

    def test_noise_wanders_the_read_from_the_true_delay(self):
        trace = Fly(oracle.Oracle(self.TARGET, noise_ms=25), seed=3).hunt()
        self.assertTrue(
            any(s["measured_ms"] != s["k"] * oracle.STEP_MS for s in trace),
            msg="noise never changed a read",
        )

    def test_noise_costs_the_fly_more_sniffs(self):
        # the leak still wins, but jitter makes the hunt work harder
        seeds = range(30)
        quiet = statistics.median(len(Fly(oracle.Oracle(self.TARGET), seed=s).hunt())
                                  for s in seeds)
        loud = statistics.median(
            len(Fly(oracle.Oracle(self.TARGET, noise_ms=20), seed=s).hunt())
            for s in seeds)
        self.assertGreater(loud, quiet)

    def test_noisy_hunt_is_deterministic_per_seed(self):
        a = [s["candidate"] for s in Fly(oracle.Oracle(self.TARGET, noise_ms=20), seed=5).hunt()]
        b = [s["candidate"] for s in Fly(oracle.Oracle(self.TARGET, noise_ms=20), seed=5).hunt()]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
