// Node tests for the neural mode-A engine. Run: node test_fly_neuro_node.js
"use strict";
const assert = require("assert");
const F = require("./fly.js");
const N = require("./fly_neuro.js");

const TARGET = [3, 9, 5, 2];
let passed = 0;
function test(name, fn) { fn(); passed++; console.log("ok - " + name); }

test("the circuit runs when odour rises and tumbles when it falls", () => {
  const up = N.circuit(1, { run: { v: 0 }, tumble: { v: 0 } });
  const down = N.circuit(-1, { run: { v: 0 }, tumble: { v: 0 } });
  assert.ok(up.run > up.tumble, "rising odour should favour running");
  assert.ok(down.tumble > down.run, "falling odour should favour tumbling");
  assert.strictEqual(down.wantTumble, true);
});

test("the neural fly opens the safe across a wide noise range", () => {
  for (const noise of [0, 20, 50, 100]) {
    for (const seed of [1, 42, 1000]) {
      const r = N.huntNeuro(TARGET, seed, noise, { maxSniffs: 40000 });
      const last = r.trace[r.trace.length - 1];
      assert.ok(last.accepted, `noise ${noise} seed ${seed} did not open`);
      assert.deepStrictEqual(last.candidate, TARGET);
    }
  }
});

test("every frame carries real neuron state and true k", () => {
  const r = N.huntNeuro(TARGET, 3, 30);
  for (const s of r.trace) {
    assert.strictEqual(s.k, F.matchingPrefix(s.candidate, TARGET));
    assert.ok(s.neuro && typeof s.neuro.run === "number" && typeof s.neuro.tumble === "number");
    assert.ok(s.neuro.run >= 0 && s.neuro.run <= 1);
  }
});

test("a neural hunt is deterministic per seed", () => {
  const a = N.huntNeuro(TARGET, 99, 20).trace.map((s) => s.candidate.join(""));
  const b = N.huntNeuro(TARGET, 99, 20).trace.map((s) => s.candidate.join(""));
  assert.deepStrictEqual(a, b);
});

console.log("\n" + passed + " tests passed");
