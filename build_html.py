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
import re
import struct
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
FAVICON_SPRITE = ASSETS / "fly-side-a.png"
FAVICON_OUT = HERE / "favicon.svg"
BODY_MARK = '<div class="wrap">'


KIT_FONT = 'url("DepartureMono-Regular.woff2")'


def kit_css():
    """Return the vendored DDLC web kit, the one source of the page's colours and controls,
    with its font inlined as a data URI (SIL OFL, see ASSETS.md): the page is one file"""
    css = (ASSETS / "ddlc-ui.css").read_text()
    if KIT_FONT not in css:
        raise SystemExit(f"assets/ddlc-ui.css no longer names its font as {KIT_FONT}")
    font = base64.b64encode((ASSETS / "DepartureMono-Regular.woff2").read_bytes()).decode("ascii")
    return css.replace(KIT_FONT, f'url("data:font/woff2;base64,{font}")')


def kit_js():
    """Return the kit's theme button and canvas helpers as plain declarations for the page's
    one script. The vendored files are ES modules, and a module cannot be imported by a
    script inlined beside it, so the build drops each top-level export keyword. A literal
    </script in their comments would close the inline script early, so it is escaped"""
    sources = [(ASSETS / name).read_text() for name in ("ddlc-theme.js", "ddlc-cloud.js")]
    code = "\n".join(re.sub(r"^export ", "", source, flags=re.MULTILINE) for source in sources)
    return code.replace("</script", "<\\/script")


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


def png_size(data):
    """Return (width, height) from a PNG's IHDR chunk"""
    return struct.unpack(">II", data[16:24])


def favicon_svg():
    """Return the favicon: the side sprite centred on a square canvas at its own size

    A browser stretches a non-square icon to its square tab slot, and the standard
    library cannot resize a PNG, so the SVG canvas does the padding. It is a separate
    file rather than a data URI in the page, so the page does not carry the sprite twice
    """
    data = FAVICON_SPRITE.read_bytes()
    width, height = png_size(data)
    side = max(width, height)
    uri = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}">'
        f'<image href="{uri}" x="{(side - width) / 2:g}" y="{(side - height) / 2:g}" '
        f'width="{width}" height="{height}"/></svg>\n'
    )


def wrap_standalone(fragment):
    """Wrap the artifact fragment in a full HTML document for local use and Pages"""
    cut = fragment.index(BODY_MARK)
    head, body = fragment[:cut], fragment[cut:]
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        f'<link rel="icon" href="{FAVICON_OUT.name}" type="image/svg+xml">\n'
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
        .replace("__DDLC_UI__", kit_css())
        .replace("__DDLC_JS__", kit_js())
        .replace("__PIN__", pin)
    )
    for token in ("__FLY_JS__", "__NEURO_JS__", "__PIN__", "__DECRYPT_JSON__", "__STEP_MS__", "__FLY_SPRITES__", "__DDLC_UI__", "__DDLC_JS__"):
        if token in fragment:
            raise SystemExit(f"placeholder {token} still present")
    standalone = wrap_standalone(fragment)
    INDEX_OUT.write_text(standalone)
    FAVICON_OUT.write_text(favicon_svg())
    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_OUT.write_text(fragment)
    return standalone, fragment, pin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    args = parser.parse_args()
    standalone, fragment, pin = build(args.dump)
    print(f"index.html      : {INDEX_OUT} ({len(standalone):,} bytes) — open in a browser / GitHub Pages")
    print(f"favicon.svg     : {FAVICON_OUT} — linked by index.html")
    print(f"artifact.html   : {ARTIFACT_OUT} ({len(fragment):,} bytes) — publish as an artifact")
    print(f"embedded PIN    : {pin} (editable in the page)")


if __name__ == "__main__":
    main()
