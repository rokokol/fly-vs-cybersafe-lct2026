#!/usr/bin/env python3
"""Build the self-contained animation page from the template and a fresh trace

The trace comes straight from run_demo.build_trace, so the page and the command
share one source of truth. The template carries a __TRACE_JSON__ placeholder that
this script fills with the trace JSON
"""
import argparse
import json
from pathlib import Path

import run_demo

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"
DEFAULT_DUMP = HERE / "data" / "backup_full.bin"
DEFAULT_OUT = HERE / "out" / "fly_safe.html"
PLACEHOLDER = "__TRACE_JSON__"
NOISE_LEVELS = [0, 10, 20, 30]  # ms of measurement jitter, chosen by the slider


def build(dump, out, levels=NOISE_LEVELS):
    template = TEMPLATE.read_text()
    if PLACEHOLDER not in template:
        raise SystemExit(f"template is missing the {PLACEHOLDER} placeholder")
    data = run_demo.build_dataset(dump, levels)
    html = template.replace(PLACEHOLDER, json.dumps(data, separators=(",", ":")))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return html, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    html, data = build(args.dump, args.out)
    runs = ", ".join(f"{r['noise_ms']}ms:{r['sniffs']}sniffs(seed {r['seed']})"
                     for r in data["runs"])
    print(f"built {args.out}  ({len(html):,} bytes)")
    print(f"runs: {runs}")


if __name__ == "__main__":
    main()
