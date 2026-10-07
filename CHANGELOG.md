# Changelog

Notable changes to Fly vs. CyberSafe. The project is unversioned, so entries are grouped by date, newest first

## 2026-10-07

- The page is a full-window app in the pixel style of easy-bitmap: a header bar, square cards with hard shadows, controls on the left and readouts on the right
- The field grows with the window, up to its full height
- Glows and confetti on the field are dithered pixels, and a dithered cloud follows the pointer in the background
- Departure Mono is the interface font; IBM Plex Sans stays for prose, and IBM Plex Mono is gone
- Pixel icons for the theme switch and the title
- The progress bar under the field is a scrubber: drag it to rewind or skip the hunt, with a move counter beside it
- The target mark is smaller and alive: a dithered odour cloud that breathes, drifts and shimmers around the target cell

## 2026-09-30

- Initial public release
- Interactive page: two live searchers (bacterium if-else, neural spiking circuit), an editable target PIN, a 0-100 ms measurement-noise slider with averaging, continuous flight with a fading dashed trail, dissolving markers, and confetti on success
- DDLC palette with an auto, light and dark theme; the field follows the theme
- Fonts: Departure Mono for data and the title, IBM Plex Mono for the UI, IBM Plex Sans for prose
- A real fruit-fly sprite cut from a licensed photo, with credits in ASSETS.md
- README with the searcher schematics and links to the research; a For the curious card on the page
- Python reference engine and tests, browser-engine node tests, and a CI workflow
- Hosted on GitHub Pages at fly.rokokol.art
- The colours come from a vendored copy of ddlc-palette, kept current by a weekly workflow, instead of values written into the page; the field, the heat map, the trail and the confetti read them too
- A Telegram link beside the GitHub one
