// Fly chemotaxis engine for the browser, mirroring fly.py / oracle.py
//
// The web toy runs the hunt live so a noise slider can be continuous. This is a
// second implementation of the Python engine on purpose; it is covered by its
// own node tests (test_fly_node.js) against the same contract. See the README
//
// The safe leaks 50 ms per matching leading PIN digit. A real read carries
// Gaussian jitter, so the fly averages several reads per sniff: the jitter falls
// as sqrt(N), which keeps the number of moves small while the number of reads is
// the real cost that grows with noise
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) module.exports = factory();
  else root.FlySim = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const STEP_MS = 50, GRID = 10, PIN_LEN = 4, RUN_LIMIT = 12;
  const LEAP_PROB = 0.15, ESCAPE_PROB = 0.06;

  // small seedable PRNG so a hunt is reproducible from its seed
  function makeRng(seed) {
    let a = (seed >>> 0) || 1;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function gauss(rng) {  // Box-Muller
    let u = 0, v = 0;
    while (u === 0) u = rng();
    while (v === 0) v = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  function matchingPrefix(entered, reference) {
    let n = 0;
    for (let i = 0; i < PIN_LEN; i++) { if (entered[i] !== reference[i]) break; n++; }
    return n;
  }

  function Oracle(reference, noiseMs) {
    this.reference = reference;
    this.noiseMs = noiseMs || 0;
  }
  Oracle.prototype.sniff = function (c) {
    const k = matchingPrefix(c, this.reference);
    return { accepted: k === PIN_LEN, k: k };
  };
  Oracle.prototype.freezeMs = function (c) {
    return matchingPrefix(c, this.reference) * STEP_MS;
  };
  Oracle.prototype.measure = function (c, rng) {
    const t = this.freezeMs(c);
    if (this.noiseMs <= 0) return t;
    return Math.max(0, t + gauss(rng) * this.noiseMs);
  };

  // reads to average per sniff, so the estimate stays reliable as noise grows
  function repeatsFor(noiseMs) {
    if (noiseMs <= 0) return 1;
    return Math.min(400, Math.max(1, Math.ceil((noiseMs / 15) ** 2)));
  }

  function xy(c) { return [c[0] * 10 + c[1], c[2] * 10 + c[3]]; }

  function frame(sniff, c, k, bestK, accepted, event, measured) {
    const p = xy(c);
    return {
      sniff: sniff, candidate: c.slice(), x: p[0], y: p[1],
      k: k, freeze_ms: k * STEP_MS, measured_ms: Math.round(measured * 10) / 10,
      best_k: bestK, accepted: accepted, event: event,
    };
  }

  function hunt(reference, seed, noiseMs, opts) {
    opts = opts || {};
    const maxSniffs = opts.maxSniffs || 30000;
    const repeats = opts.repeats || repeatsFor(noiseMs);
    const noisy = noiseMs > 0;
    const ora = new Oracle(reference, noiseMs);
    const rng = makeRng(seed || 1);
    const meas = makeRng(((seed || 1) ^ 0x9E3779B9) >>> 0);

    function observe(c) {
      const s = ora.sniff(c);
      let sum = 0;
      for (let r = 0; r < repeats; r++) sum += ora.measure(c, meas);
      const avg = sum / repeats;
      const kEst = noisy ? Math.min(PIN_LEN, Math.max(0, Math.round(avg / STEP_MS))) : s.k;
      return { accepted: s.accepted, trueK: s.k, kEst: kEst, measured: avg };
    }
    function randPin() {
      const c = [0, 0, 0, 0];
      for (let i = 0; i < PIN_LEN; i++) c[i] = Math.floor(rng() * GRID);
      return c;
    }

    let cand = randPin();
    let o = observe(cand);
    let bestEst = o.kEst, sniffNo = 1;
    const trace = [frame(1, cand, o.trueK, bestEst, o.accepted, o.accepted ? "found" : "start", o.measured)];
    if (o.accepted) return { trace: trace, repeats: repeats };

    let pos = Math.floor(rng() * PIN_LEN), step = rng() < 0.5 ? -1 : 1, runLen = 0;
    while (sniffNo < maxSniffs && !trace[trace.length - 1].accepted) {
      let propose, event;
      if (bestEst === 0 && rng() < LEAP_PROB) { propose = randPin(); event = "leap"; }
      else if (noisy && rng() < ESCAPE_PROB) { propose = randPin(); event = "leap"; }
      else { propose = cand.slice(); propose[pos] = (propose[pos] + step + GRID) % GRID; event = "run"; }

      sniffNo++;
      const e = observe(propose);
      if (e.accepted) { cand = propose; bestEst = PIN_LEN; event = "found"; }
      else if (e.kEst > bestEst) { cand = propose; bestEst = e.kEst; runLen = 0; event = "lock"; }
      else if (e.kEst === bestEst) {
        cand = propose; runLen++;
        if (runLen >= RUN_LIMIT) { pos = Math.floor(rng() * PIN_LEN); step = rng() < 0.5 ? -1 : 1; runLen = 0; }
      } else { pos = Math.floor(rng() * PIN_LEN); step = rng() < 0.5 ? -1 : 1; runLen = 0; event = "tumble"; }

      trace.push(frame(sniffNo, propose, e.trueK, bestEst, e.accepted, event, e.measured));
    }
    return { trace: trace, repeats: repeats };
  }

  function field(reference) {
    const rows = [];
    for (let y = 0; y < 100; y++) {
      const row = [];
      for (let x = 0; x < 100; x++) {
        row.push(matchingPrefix([Math.floor(x / 10), x % 10, Math.floor(y / 10), y % 10], reference));
      }
      rows.push(row);
    }
    return rows;
  }

  return {
    STEP_MS: STEP_MS, GRID: GRID, PIN_LEN: PIN_LEN,
    makeRng: makeRng, matchingPrefix: matchingPrefix, Oracle: Oracle,
    repeatsFor: repeatsFor, hunt: hunt, field: field, xy: xy,
  };
});
