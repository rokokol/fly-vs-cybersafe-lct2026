#!/usr/bin/env python3
"""Tests for the page build: the favicon"""
import base64
import re
import unittest

import build_html


class FaviconTests(unittest.TestCase):
    def setUp(self):
        self.svg = build_html.favicon_svg()
        self.sprite = build_html.FAVICON_SPRITE.read_bytes()

    def find(self, pattern):
        match = re.search(pattern, self.svg)
        if match is None:
            self.fail(f"{pattern} not in the favicon")
        return match

    def side(self):
        _, _, w, h = map(float, self.find(r'viewBox="([^"]+)"').group(1).split())
        return w, h

    def test_canvas_is_square(self):
        # a browser stretches a non-square icon to its square tab slot
        w, h = self.side()
        self.assertEqual(w, h)

    def test_sprite_is_centred_at_its_own_size(self):
        width, height = build_html.png_size(self.sprite)
        side, _ = self.side()
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', self.find(r"<image [^>]*>").group(0)))
        self.assertEqual((float(attrs["width"]), float(attrs["height"])), (width, height))
        self.assertEqual(float(attrs["x"]) * 2 + width, side)
        self.assertEqual(float(attrs["y"]) * 2 + height, side)

    def test_embeds_the_sprite_unchanged(self):
        uri = self.find(r'href="data:image/png;base64,([^"]+)"').group(1)
        self.assertEqual(base64.b64decode(uri), self.sprite)

    def test_page_links_the_favicon(self):
        page = build_html.wrap_standalone(build_html.BODY_MARK)
        self.assertIn(f'<link rel="icon" href="{build_html.FAVICON_OUT.name}" type="image/svg+xml">', page)


class BrandTests(unittest.TestCase):
    def test_title_mark_is_the_favicon_sprite(self):
        fragment, _ = build_html.render(build_html.DEFAULT_DUMP)
        brand = re.search(r'<h1 class="brand">(.*?)</h1>', fragment, re.S)
        if brand is None:
            self.fail("no brand heading in the page")
        src = build_html.FAVICON_SPRITE.relative_to(build_html.HERE).as_posix()
        self.assertRegex(brand.group(1), rf'<img [^>]*src="{re.escape(src)}"')
        self.assertNotIn("<svg", brand.group(1))


if __name__ == "__main__":
    unittest.main()
