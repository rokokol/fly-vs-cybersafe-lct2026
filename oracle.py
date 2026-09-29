#!/usr/bin/env python3
"""Timing-oracle model of the safe PIN check

The safe compares the entered PIN with a stored reference one digit at a time.
It holds its outputs frozen for 50 ms per matching leading digit, then stops at
the first wrong digit. That delay leaks the length of the matching prefix. This
module models that leak. It does not run the firmware
"""

STEP_MS = 50  # the safe freezes 50 ms per matching leading digit


def matching_prefix(entered, reference):
    """Return the length of the matching leading run (0..len)

    The count stops at the first differing digit, so a digit that matches after
    a wrong one does not add to it
    """
    count = 0
    for a, b in zip(entered, reference):
        if a != b:
            break
        count += 1
    return count


class Oracle:
    """The safe seen as a black box: enter a PIN, read the leaked delay

    A real read of the freeze delay is not exact: it carries measurement jitter.
    noise_ms is the standard deviation of that jitter in milliseconds; measure()
    adds it. sniff() and freeze_ms() stay exact, as the ground truth
    """

    def __init__(self, reference, noise_ms=0.0):
        self.reference = tuple(reference)
        self.noise_ms = float(noise_ms)

    def sniff(self, candidate):
        """Return (accepted, matching_prefix_length) for a candidate PIN"""
        k = matching_prefix(candidate, self.reference)
        return (k == len(self.reference), k)

    def freeze_ms(self, candidate):
        """Return the exact leaked freeze delay in milliseconds for a candidate"""
        return matching_prefix(candidate, self.reference) * STEP_MS

    def measure(self, candidate, rng):
        """Return a noisy read of the freeze delay in milliseconds (never below 0)

        With noise_ms == 0 the read is exact. Otherwise it is the true delay plus
        Gaussian jitter drawn from rng, clamped at zero
        """
        true_delay = self.freeze_ms(candidate)
        if self.noise_ms <= 0:
            return float(true_delay)
        return max(0.0, true_delay + rng.gauss(0.0, self.noise_ms))
