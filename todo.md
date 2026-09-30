# To do

Ideas and tracks for Fly vs. CyberSafe, roughly in order

## Modes

- [ ] **Board mode** — a separate mode with a fixed PIN that runs the real RP2040 firmware (via rp2040js) and shows a board or schematic where the LEDs light and blink as the fly acts
- [ ] **Connectome mode** — the real MaleCNS 2026 spiking connectome, a heavy local track that runs on a PC
- [ ] **Pure-neural model** — drive the neural searcher entirely from the spiking circuit (receptor adaptation plus an area-restricted-search neuron), with no if-else digit lock

## Features

- [ ] **Upload your own cyber-safe binary** — drop in a firmware image and the fly cracks its PIN by behaviour alone: no digit boxes, just a picture of the safe that reacts to the fly, and you download the decrypted contents as a zip
- [ ] **Continuous-plane searcher** — a fly that flies in any direction and rounds its position to sniff (tried once, it converged poorly on the discrete axis-structured field; revisit with a stronger neural search)

## Done

- [x] Interactive page: bacterium and neural searchers, editable PIN, 0-100 ms noise, continuous flight, dashed trail, confetti
- [x] DDLC theme with auto, light and dark; real fly sprite; research links; GitHub Pages files
