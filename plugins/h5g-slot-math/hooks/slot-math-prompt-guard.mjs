#!/usr/bin/env node

import fs from "node:fs";

const input = fs.readFileSync(0, "utf8");
let payload = {};

try {
  payload = input.trim() ? JSON.parse(input) : {};
} catch {
  process.exit(0);
}

const prompt = String(payload.prompt || "").toLowerCase();

const specificTerms = [
  "slot math",
  "game math",
  "math model",
  "math proof",
  "rmg",
  "real money game",
  "real money gaming",
  "rtp",
  "return to player",
  "par sheet",
  "par-sheet",
  "monte carlo",
  "test harness",
  "slotengine",
  "slot engine",
  "slotenginegui",
  "slot engine gui",
  "math commons",
  "reel strip",
  "reel strips",
  "virtual stop",
  "visible window",
  "paytable",
  "pay table",
  "hit frequency",
  "win frequency",
  "volatility",
  "variance",
  "standard deviation",
  "expected value",
  " ev ",
  "payout",
  "payouts",
  "odds",
  "rng",
  "weighted table",
  "symbol weight",
  "scatter",
  "wild",
  "free spins",
  "free spin",
  "retrigger",
  "hold and spin",
  "hold-and-spin",
  "loot link",
  "wys",
  "collector",
  "jackpot",
  "progressive",
  "dependent probability",
  "dependent probabilities",
  "certification",
  "certification docs",
  "jurisdiction"
];

const broadMathTerms = [
  "math",
  "probability",
  "probabilities",
  "simulation",
  "simulate",
  "verify",
  "test it",
  "calculate"
];

const h5gContextTerms = [
  "slot",
  "slots",
  "h5g",
  "high 5",
  "casino",
  "game",
  "games",
  "rmg",
  "reel",
  "pay",
  "bonus",
  "feature",
  "jackpot"
];

const hasSpecificTerm = specificTerms.some((term) => prompt.includes(term));
const hasBroadMathContext =
  broadMathTerms.some((term) => prompt.includes(term)) &&
  h5gContextTerms.some((term) => prompt.includes(term));

if (!hasSpecificTerm && !hasBroadMathContext) {
  process.exit(0);
}

const additionalContext = [
  "H5G slot math guardrail active.",
  "When discussing math, RTP, RMG, odds, payouts, reels, simulations, PAR sheets, or certification: invoke the H5G Slot Math skills naturally.",
  "Use h5g-slot-math:probability-model before producing numbers, h5g-slot-math:dependency-audit for independence/dependence risks, h5g-slot-math:rtp-verification for Monte Carlo/Test Harness/SlotEngineGUI evidence, and h5g-slot-math:internal-h5g-evidence for RMG/H5G process gates.",
  "Define the probability model before numbers; default to dependent until independence is proven; stop if source data is missing; use exact enumeration/state modeling when tractable; treat Monte Carlo as verification only; report probability basis, results, verification, and blockers."
].join(" ");

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext
  }
}));

