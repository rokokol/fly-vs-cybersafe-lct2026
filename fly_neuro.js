// Browser mode A: a tiny spiking neural circuit that drives the hunt
//
// This is NOT the fly connectome. It is a small klinokinesis circuit, the real
// motif bacteria and worms use: sense the CHANGE in odour, then run when it rises
// and tumble when it falls. A few leaky integrate-and-fire (LIF) neurons decide
// run vs tumble; the commit-on-gain / recoil-on-loss are strong sensory reflexes.
// The odour is the safe's leaked delay (see fly.js). PIN = odour is a metaphor
//
// The full, real MaleCNS 2026 connectome simulation is the separate PC track
(function (root, factory) {
  const dep = (typeof module !== "undefined" && module.exports) ? require("./fly.js") : root.FlySim;
  const out = factory(dep);
  if (typeof module !== "undefined" && module.exports) module.exports = out;
  else root.FlyNeuro = out;
})(typeof self !== "undefined" ? self : this, function (FlySim) {
  "use strict";
  const { STEP_MS, GRID, PIN_LEN, makeRng, matchingPrefix, Oracle, repeatsFor } = FlySim;

  // one LIF neuron step; returns 1 on spike, resets when it fires
  function lifStep(state, input, tau, dt) {
    state.v += dt * (-state.v / tau + input);
    if (state.v >= 1) { state.v = 0; return 1; }
    return 0;
  }

  // run the decide-circuit for one sniff: given the odour change, count spikes of
  // the run and tumble motor neurons over a short window
  function circuit(dINorm, cells) {
    const dt = 1, window = 20, tau = 10;
    const on = Math.max(0, dINorm), off = Math.max(0, -dINorm);
    let runSpikes = 0, tumbleSpikes = 0, runRate = 0, tumbleRate = 0;
    for (let t = 0; t < window; t++) {
      // mutual inhibition through the last step's rates
      const runIn = 1.6 * on - 0.9 * tumbleRate;
      const tumbleIn = 1.6 * off + 0.35 - 0.9 * runRate;  // 0.35 = baseline tumble drive
      const r = lifStep(cells.run, Math.max(0, runIn), tau, dt);
      const s = lifStep(cells.tumble, Math.max(0, tumbleIn), tau, dt);
      runSpikes += r; tumbleSpikes += s;
      runRate = 0.7 * runRate + 0.3 * r;
      tumbleRate = 0.7 * tumbleRate + 0.3 * s;
    }
    return {
      on: on, off: off,
      run: runSpikes / window, tumble: tumbleSpikes / window,
      wantTumble: tumbleSpikes > runSpikes,
    };
  }

  function xy(c) { return [c[0] * 10 + c[1], c[2] * 10 + c[3]]; }

  function huntNeuro(reference, seed, noiseMs, opts) {
    opts = opts || {};
    const maxSniffs = opts.maxSniffs || 30000;
    const repeats = opts.repeats || repeatsFor(noiseMs);
    const noisy = noiseMs > 0;
    const ora = new Oracle(reference, noiseMs);
    const rng = makeRng(seed || 1);
    const meas = makeRng(((seed || 1) ^ 0x9E3779B9) >>> 0);
    const cells = { run: { v: 0 }, tumble: { v: 0 } };
    let base = 0;  // adapted odour baseline (receptor adaptation)

    function observe(c) {
      const k = matchingPrefix(c, reference);
      let sum = 0;
      for (let r = 0; r < repeats; r++) sum += ora.measure(c, meas);
      const avg = sum / repeats;
      const kEst = noisy ? Math.min(PIN_LEN, Math.max(0, Math.round(avg / STEP_MS))) : k;
      return { accepted: k === PIN_LEN, trueK: k, kEst: kEst, measured: avg };
    }
    function randPin() { const c = [0, 0, 0, 0]; for (let i = 0; i < PIN_LEN; i++) c[i] = Math.floor(rng() * GRID); return c; }
    function frame(sniff, c, k, bestK, accepted, event, measured, neuro) {
      const p = xy(c);
      return {
        sniff: sniff, candidate: c.slice(), x: p[0], y: p[1],
        k: k, freeze_ms: k * STEP_MS, measured_ms: Math.round(measured * 10) / 10,
        best_k: bestK, accepted: accepted, event: event, neuro: neuro,
      };
    }

    let cand = randPin();
    let o = observe(cand);
    let bestEst = o.kEst, prevEst = o.kEst, sniffNo = 1;
    base = o.measured;
    const startNeuro = { on: 0, off: 0, run: 0, tumble: 0, wantTumble: false, odor: o.measured / (4 * STEP_MS), base: base / (4 * STEP_MS) };
    const trace = [frame(1, cand, o.trueK, bestEst, o.accepted, o.accepted ? "found" : "start", o.measured, startNeuro)];
    if (o.accepted) return { trace: trace, repeats: repeats };

    let pos = Math.floor(rng() * PIN_LEN), step = rng() < 0.5 ? -1 : 1;
    while (sniffNo < maxSniffs && !trace[trace.length - 1].accepted) {
      let propose, event;
      if (bestEst === 0 && rng() < 0.15) { propose = randPin(); event = "leap"; }
      else if (noisy && rng() < 0.06) { propose = randPin(); event = "leap"; }
      else { propose = cand.slice(); propose[pos] = (propose[pos] + step + GRID) % GRID; event = "run"; }

      sniffNo++;
      const e = observe(propose);
      // the circuit senses the change in odour estimate since the last sniff
      const dINorm = (e.kEst - prevEst);
      const c = circuit(dINorm, cells);
      base = 0.8 * base + 0.2 * e.measured;

      if (e.accepted) { cand = propose; bestEst = PIN_LEN; event = "found"; }
      else if (e.kEst > bestEst) { cand = propose; bestEst = e.kEst; event = "lock"; }
      else if (e.kEst < bestEst) { pos = Math.floor(rng() * PIN_LEN); step = rng() < 0.5 ? -1 : 1; event = "tumble"; }
      else {
        cand = propose;  // drift on the plateau
        if (c.wantTumble) { pos = Math.floor(rng() * PIN_LEN); step = rng() < 0.5 ? -1 : 1; event = "tumble"; }
      }
      prevEst = e.kEst;
      const neuro = { on: c.on, off: c.off, run: c.run, tumble: c.tumble, wantTumble: c.wantTumble, odor: e.measured / (4 * STEP_MS), base: base / (4 * STEP_MS) };
      trace.push(frame(sniffNo, propose, e.trueK, bestEst, e.accepted, event, e.measured, neuro));
    }
    return { trace: trace, repeats: repeats };
  }

  return { huntNeuro: huntNeuro, circuit: circuit };
});
