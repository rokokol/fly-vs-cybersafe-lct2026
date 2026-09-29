#!/usr/bin/env python3
"""A fly that opens the safe by smell

A fruit fly cannot reason about a PIN. It can do one thing very well: climb an
odour gradient by run-and-tumble. It runs in a straight line while the smell
grows, and tumbles into a new heading when the smell drops. See the README

The safe leaks a gradient: its PIN check freezes 50 ms per matching leading
digit (see oracle.py). So the matching-prefix length is an odour the fly can
smell, and plain chemotaxis walks it straight to the PIN. The fly is far dumber
than a targeted side-channel search, yet the leak alone lets it win

Each PIN maps to a cell on a 100x100 field: the first two digits give the column
x, the last two give the row y. The fly flies over that field
"""
import random

import oracle

GRID = 10          # values 0..9 for one PIN digit
PIN_LEN = 4        # a PIN is four digits
RUN_LIMIT = 12     # a run turns over at most this many cells before a tumble
LEAP_PROB = 0.15   # chance to relocate far while no odour has been found yet
ESCAPE_PROB = 0.06  # chance to relocate when noise may have locked a wrong digit
DEFAULT_MAX_SNIFFS = 20000


def candidate_to_xy(candidate):
    """Map a 4-digit PIN to its (x, y) cell on the field"""
    d0, d1, d2, d3 = candidate
    return d0 * 10 + d1, d2 * 10 + d3


class Fly:
    def __init__(self, oracle_, seed=0, max_sniffs=DEFAULT_MAX_SNIFFS):
        self.oracle = oracle_
        self.rng = random.Random(seed)
        # a separate stream for measurement jitter, so movement stays reproducible
        self.meas_rng = random.Random(seed ^ 0x9E3779B9)
        self.max_sniffs = max_sniffs

    def _tumble(self):
        """Pick a fresh heading: which digit to turn, and in which direction"""
        return self.rng.randrange(PIN_LEN), self.rng.choice((-1, 1))

    def _observe(self, candidate):
        """Sniff a candidate: ground-truth unlock plus the fly's noisy estimate

        Returns (accepted, true_k, k_estimate, measured_ms). The unlock is real:
        the safe opens only for the true PIN. The estimate is what the fly reads
        from the noisy freeze delay, and it can be wrong
        """
        accepted, true_k = self.oracle.sniff(candidate)
        measured = self.oracle.measure(candidate, self.meas_rng)
        if self.oracle.noise_ms <= 0:
            k_est = true_k
        else:
            k_est = min(PIN_LEN, max(0, round(measured / oracle.STEP_MS)))
        return accepted, true_k, k_est, measured

    def _frame(self, sniff_no, candidate, k, best_k, accepted, event, measured):
        x, y = candidate_to_xy(candidate)
        return {
            "sniff": sniff_no,
            "candidate": list(candidate),
            "x": x,
            "y": y,
            "k": k,
            "freeze_ms": k * oracle.STEP_MS,
            "measured_ms": round(measured, 1),
            "best_k": best_k,
            "accepted": accepted,
            "event": event,
        }

    def hunt(self):
        """Fly the field until the safe opens; return every sniff as a frame"""
        rng = self.rng
        noisy = self.oracle.noise_ms > 0
        candidate = [rng.randrange(GRID) for _ in range(PIN_LEN)]
        accepted, true_k, best_est, measured = self._observe(candidate)
        sniff_no = 1
        trace = [self._frame(sniff_no, candidate, true_k, best_est, accepted,
                             "found" if accepted else "start", measured)]
        if accepted:
            return trace

        pos, step = self._tumble()
        run_len = 0

        while sniff_no < self.max_sniffs and not accepted:
            if best_est == 0 and rng.random() < LEAP_PROB:
                # no odour yet: make a long random relocation to find the plume
                propose = [rng.randrange(GRID) for _ in range(PIN_LEN)]
                event = "leap"
            elif noisy and rng.random() < ESCAPE_PROB:
                # noise may have locked a wrong digit: relocate to stay ergodic
                propose = [rng.randrange(GRID) for _ in range(PIN_LEN)]
                event = "leap"
            else:
                # a run step: turn the current digit one notch along the heading
                propose = list(candidate)
                propose[pos] = (propose[pos] + step) % GRID
                event = "run"

            sniff_no += 1
            accepted, true_k, k_est, measured = self._observe(propose)

            if accepted:
                candidate, best_est, event = propose, PIN_LEN, "found"
            elif k_est > best_est:
                # stronger smell: commit and keep this heading (surge)
                candidate, best_est, run_len, event = propose, k_est, 0, "lock"
            elif k_est == best_est:
                # same smell: drift on across the plateau, but not forever
                candidate = propose
                run_len += 1
                if run_len >= RUN_LIMIT:
                    pos, step = self._tumble()
                    run_len = 0
            else:
                # smell dropped: recoil to the last good cell and reorient
                pos, step = self._tumble()
                run_len = 0
                event = "tumble"

            trace.append(self._frame(sniff_no, propose, true_k, best_est,
                                     accepted, event, measured))

        return trace
