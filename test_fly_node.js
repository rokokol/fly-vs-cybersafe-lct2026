// Node tests for the browser fly engine (fly.js), mirroring the Python contract.
// Run: node test_fly_node.js
"use strict";
const assert = require("assert");
const F = require("./fly.js");

const TARGET = [3, 9, 5, 2];
let passed = 0;
function test(name, fn) { fn(); passed++; console.log("ok - " + name); }

test("matchingPrefix counts the leading run and stops at a mismatch", () => {
  assert.strictEqual(F.matchingPrefix([0, 0, 0, 0], TARGET), 0);
  assert.strictEqual(F.matchingPrefix([3, 9, 0, 0], TARGET), 2);
  assert.strictEqual(F.matchingPrefix([3, 9, 5, 2], TARGET), 4);
  assert.strictEqual(F.matchingPrefix([3, 0, 5, 2], TARGET), 1);
});

test("oracle measure is exact without noise", () => {
  const o = new F.Oracle(TARGET, 0);
  const rng = F.makeRng(1);
  assert.strictEqual(o.measure([3, 9, 0, 0], rng), 100);
  assert.strictEqual(o.measure([3, 9, 5, 2], rng), 200);
});

test("oracle noise centres on the true delay and never goes negative", () => {
  const o = new F.Oracle(TARGET, 20);
  const rng = F.makeRng(7);
  let sum = 0; const N = 5000; let minV = Infinity;
  for (let i = 0; i < N; i++) { const v = o.measure([3, 9, 0, 0], rng); sum += v; if (v < minV) minV = v; }
  assert.ok(minV >= 0, "reads went negative");
  assert.ok(Math.abs(sum / N - 100) < 3, "mean drifted: " + sum / N);
});

test("fly opens the safe across a wide noise range, thanks to averaging", () => {
  for (const noise of [0, 20, 50, 100]) {
    for (const seed of [1, 42, 1000]) {
      const r = F.hunt(TARGET, seed, noise, { maxSniffs: 40000 });
      const last = r.trace[r.trace.length - 1];
      assert.ok(last.accepted, `noise ${noise} seed ${seed} did not open`);
      assert.deepStrictEqual(last.candidate, TARGET);
    }
  }
});

test("recorded k and freeze are the true values, not the noisy read", () => {
  const r = F.hunt(TARGET, 3, 30);
  for (const s of r.trace) {
    assert.strictEqual(s.k, F.matchingPrefix(s.candidate, TARGET));
    assert.strictEqual(s.freeze_ms, s.k * F.STEP_MS);
    assert.strictEqual(s.accepted, s.k === 4);
  }
});

test("more noise buys more reads per sniff, not runaway moves", () => {
  const quiet = F.hunt(TARGET, 5, 0).repeats;
  const loud = F.hunt(TARGET, 5, 100).repeats;
  assert.strictEqual(quiet, 1);
  assert.ok(loud > quiet, "averaging did not scale with noise");
});

test("a hunt is deterministic for a given seed", () => {
  const a = F.hunt(TARGET, 99, 20).trace.map((s) => s.candidate.join(""));
  const b = F.hunt(TARGET, 99, 20).trace.map((s) => s.candidate.join(""));
  assert.deepStrictEqual(a, b);
});

console.log("\n" + passed + " tests passed");
