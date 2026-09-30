# To do

Tracks and ideas for Fly vs. CyberSafe, roughly in order

## Modes

- [ ] **Board mode** — a separate mode with a fixed PIN that runs the real RP2040 firmware (via rp2040js) and shows a board or schematic where the LEDs light and blink as the fly acts. The user will supply board photos
- [ ] **Connectome mode** — the real MaleCNS 2026 spiking connectome, a heavy local track that runs on a PC (data: flyconnectome/2025malecns, FlyWire codex, a Shiu-style spiking model)
- [ ] **Pure-neural model** — drive the neural searcher entirely from the spiking circuit (receptor adaptation plus an area-restricted-search neuron), with no if-else digit lock. Risk: on this discrete axis-structured field a purely emergent search may converge unreliably, so measure it before shipping
- [ ] **Continuous-plane searcher** — a fly that flies in any direction and rounds its position to sniff. A first attempt converged poorly on the discrete field; revisit with a stronger neural search

## Features

- [ ] **Upload your own cyber-safe binary** — drop in a firmware image and the fly cracks its PIN by behaviour alone: no digit boxes, just a picture of the safe that reacts to the fly, and you download the decrypted contents as a zip

## Follow-ups

- [ ] Enable Enforce HTTPS in Settings once the GitHub Pages DNS check passes and the certificate is issued
- [ ] Confirm the exact source photo of the side sprites (`assets/fly-side-b.png`, `assets/fly-side-c.png`) so ASSETS.md credits each one precisely
- [ ] Decide on a code license (add a LICENSE file); the repository is unversioned by choice

## Done

- [x] Interactive page: bacterium and neural searchers, editable PIN, 0-100 ms noise with averaging, continuous flight, fading dashed trail, dissolving markers, confetti
- [x] DDLC palette with auto, light and dark; the field follows the theme
- [x] Fonts: Departure Mono for data and the title, IBM Plex Mono for the UI, IBM Plex Sans for prose
- [x] Real fly sprite plus a README sprite gallery, credited in ASSETS.md
- [x] Research links, searcher schematics, header icons, GitHub link
- [x] Python reference engine and tests, browser-engine node tests, CI workflow, changelog
- [x] Public repo and GitHub Pages at fly.rokokol.art
