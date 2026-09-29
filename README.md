# Fly vs. Safe

A fruit fly opens a hardware safe by smell — it follows the safe's own timing leak to the PIN, then a fixed key decrypts the hidden volume

## What it is

The target is a USB "cyber-safe" built on a Raspberry Pi RP2040 (LCT 2026, Positive Technologies track)

Its PIN check leaks a gradient: the firmware freezes its outputs 50 ms for each matching leading digit, then stops at the first wrong one

A fruit fly cannot reason about a PIN, but it is very good at climbing an odour gradient by run-and-tumble: fly straight while the smell grows, tumble into a new heading when it drops

So this project treats the leaked delay as an odour and lets a plain chemotaxis agent smell its way to the code

## How the fly wins

Each PIN maps to a cell on a 100x100 field: the first two digits give the column, the last two give the row

The matching-prefix length is the odour at that cell, so the field holds a plume that rises toward the real PIN

The fly follows that plume. It is far dumber than a targeted side-channel search, yet the leak alone lets it crack the code in about 80 tries, against 10000 blind ones

The PIN gate and the storage cipher are independent: the PIN opens the USB gate, a fixed firmware key opens the data. So the volume decrypts offline from a flash dump, with no PIN at all

A real timing read is not exact: it carries jitter. The demo can add adjustable measurement noise to the leaked delay, and the fly then smells a noisy gradient

Small jitter barely helps the safe. Larger jitter only makes the fly work harder — it still opens the safe, but needs many more sniffs — so noise alone is a weak defence

> [!NOTE]
> This is not a brain simulation. The fly is a run-and-tumble chemotaxis agent, not a connectome. The point is that one real side channel lets even a fly-grade searcher win

## Run it

```bash
python3 -m unittest test_oracle test_fly test_firmware   # the suite
python3 run_demo.py --noise 20                            # hunt + decrypt with jitter, writes out/trace.json
python3 build_html.py                                     # build the animation, writes out/fly_safe.html
```

Then open `out/fly_safe.html` in a browser to watch the fly hunt the PIN and the safe open, and drag the noise slider to see the jitter slow it down

## What is inside

| File | Role |
| --- | --- |
| `oracle.py` | the timing-oracle model — matching prefix and the 50 ms leak |
| `fly.py` | the run-and-tumble chemotaxis agent |
| `firmware.py` | the recovered PIN reference and the storage cipher |
| `run_demo.py` | run the hunt and the decrypt, write the trace |
| `template.html`, `build_html.py` | build the self-contained animation page |
| `data/backup_full.bin` | the 2 MiB flash dump of the safe |
| `test_*.py` | the test suite |

## Provenance

The PIN, the cipher constants, and the decrypted volume are the real values recovered from the device by the report vectors of the LCT 2026 study

The competition is over, so these values are published here as a teaching demo
