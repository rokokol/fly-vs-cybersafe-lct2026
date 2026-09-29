#!/usr/bin/env python3
"""Build the self-contained interactive page from the template

The page runs the search live in the browser, so it embeds only the static facts
(the device PIN and the real decrypt result) and inlines the two JS engines. It
writes index.html (a full document for local use and GitHub Pages) and
out/artifact.html (a bare fragment for publishing as an artifact)
"""
import argparse
import base64
import json
from pathlib import Path

import firmware
import oracle
import run_demo

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"
DEFAULT_DUMP = HERE / "data" / "backup_full.bin"
INDEX_OUT = HERE / "index.html"
ARTIFACT_OUT = HERE / "out" / "artifact.html"
ASSETS = HERE / "assets"
BODY_MARK = '<div class="wrap">'


def sprite_data_uris():
    """Return the fly sprite frame(s) as data URIs, or [] so the cartoon is used

    The page uses the single clean sprite (fly.png); the flap frames stay on disk
    for the README gallery
    """
    single = ASSETS / "fly.png"
    if single.exists():
        frames = [single]
    else:
        frames = sorted(ASSETS.glob("fly_*.png"))
    return ["data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii") for p in frames]


def wrap_standalone(fragment):
    """Wrap the artifact fragment in a full HTML document for local use and Pages"""
    cut = fragment.index(BODY_MARK)
    head, body = fragment[:cut], fragment[cut:]
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        f"{head}</head>\n<body>\n{body}</body>\n</html>\n"
    )


def build(dump):
    template = TEMPLATE.read_text()
    pin = firmware.extract_pin(dump)
    decrypt = run_demo.decrypt_summary(dump)
    fragment = (
        template
        .replace("__FLY_JS__", (HERE / "fly.js").read_text())
        .replace("__NEURO_JS__", (HERE / "fly_neuro.js").read_text())
        .replace("__DECRYPT_JSON__", json.dumps(decrypt, separators=(",", ":")))
        .replace("__STEP_MS__", str(oracle.STEP_MS))
        .replace("__FLY_SPRITES__", json.dumps(sprite_data_uris()))
        .replace("__PIN__", pin)
    )
    for token in ("__FLY_JS__", "__NEURO_JS__", "__PIN__", "__DECRYPT_JSON__", "__STEP_MS__", "__FLY_SPRITES__"):
        if token in fragment:
            raise SystemExit(f"placeholder {token} still present")
    standalone = wrap_standalone(fragment)
    INDEX_OUT.write_text(standalone)
    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_OUT.write_text(fragment)
    return standalone, fragment, pin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    args = parser.parse_args()
    standalone, fragment, pin = build(args.dump)
    print(f"index.html      : {INDEX_OUT} ({len(standalone):,} bytes) — open in a browser / GitHub Pages")
    print(f"artifact.html   : {ARTIFACT_OUT} ({len(fragment):,} bytes) — publish as an artifact")
    print(f"embedded PIN    : {pin} (editable in the page)")


if __name__ == "__main__":
    main()
