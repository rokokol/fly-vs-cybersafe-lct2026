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
OUT_DIR = HERE / "out"
LOCAL_OUT = OUT_DIR / "fly_safe.html"      # full document, opens by double-click
ARTIFACT_OUT = OUT_DIR / "artifact.html"   # bare fragment, for publishing as an artifact
PLACEHOLDER = "__TRACE_JSON__"
BODY_MARK = '<div class="wrap">'
NOISE_LEVELS = [0, 10, 20, 30]  # ms of measurement jitter, chosen by the slider


def wrap_standalone(fragment):
    """Wrap the artifact fragment in a full HTML document for local use

    The template is authored as an artifact fragment (no document skeleton). For a
    file opened straight from disk we add the doctype, head and body, and split the
    fragment so its meta, title, link and style sit in the head
    """
    cut = fragment.index(BODY_MARK)
    head, body = fragment[:cut], fragment[cut:]
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        f"{head}</head>\n<body>\n{body}</body>\n</html>\n"
    )


def build(dump, levels=NOISE_LEVELS):
    template = TEMPLATE.read_text()
    if PLACEHOLDER not in template:
        raise SystemExit(f"template is missing the {PLACEHOLDER} placeholder")
    data = run_demo.build_dataset(dump, levels)
    fragment = template.replace(PLACEHOLDER, json.dumps(data, separators=(",", ":")))
    standalone = wrap_standalone(fragment)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_OUT.write_text(standalone)
    ARTIFACT_OUT.write_text(fragment)
    return standalone, fragment, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    args = parser.parse_args()
    standalone, fragment, data = build(args.dump)
    runs = ", ".join(f"{r['noise_ms']}ms:{r['sniffs']}sniffs(seed {r['seed']})"
                     for r in data["runs"])
    print(f"local  : {LOCAL_OUT}  ({len(standalone):,} bytes) - open in a browser")
    print(f"artifact fragment: {ARTIFACT_OUT}  ({len(fragment):,} bytes)")
    print(f"runs: {runs}")


if __name__ == "__main__":
    main()
