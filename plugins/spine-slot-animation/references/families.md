# Recipe Families

The 15 implementable Spine slot animation families, plus 2 review-gated families. Each family is a contract: purpose, naming, source-layer requirements, generated animations, controls, and pitfalls. Use this file to classify an asset and look up the contract before compiling.

## Table of contents

1. [hp_symbol — High-Pay Symbol](#hp_symbol--high-pay-symbol)
2. [mp_symbol — Medium-Pay Symbol](#mp_symbol--medium-pay-symbol)
3. [lp_symbol — Low-Pay Symbol](#lp_symbol--low-pay-symbol)
4. [wild_symbol — Wild Symbol](#wild_symbol--wild-symbol)
5. [scatter_symbol — Scatter Symbol](#scatter_symbol--scatter-symbol)
6. [bonus_symbol — Bonus Symbol](#bonus_symbol--bonus-symbol)
7. [bo_special_symbol — BO / Special Symbol](#bo_special_symbol--bo--special-symbol)
8. [jackpot_symbol — Jackpot Symbol](#jackpot_symbol--jackpot-symbol)
9. [special_feature_symbol — Special Feature Symbol](#special_feature_symbol--special-feature-symbol)
10. [value_symbol — Value / WYS Symbol](#value_symbol--value--wys-symbol)
11. [winframe_explode — WinFrame / Explode](#winframe_explode--winframe--explode)
12. [meter — Meter](#meter--meter)
13. [transition — Transition](#transition--transition)
14. [celebration — Celebration](#celebration--celebration)
15. [avatar — Avatar](#avatar--avatar)
16. [Review-gated families](#review-gated-families)
17. [Motion amplitude tiers](#motion-amplitude-tiers)

---

## Classification

Three signals together identify a family:

1. **Filename / layer-name prefix** (`HP1`, `JP_GRAND`, `WD1_idle`, `MeterCollect`). Strongest single signal when the asset is named.
2. **Role map** (when an H5G or equivalent symbol role map exists). Records role assignments per game.
3. **Layer composition**. A symbol with `*_head` + `*_eyes_blink` + `*_<character>_laugh` is almost always `hp_symbol` or `special_feature_symbol`. A symbol with `*_J` or `*_K` is `lp_symbol`. A folder of `State<N>` PNGs is `avatar` or `meter`.

Never classify by visual style alone. A premium-looking King card is still `lp_symbol` if the role map says low-pay. Character-looking HP/special/wild art is NOT `avatar` unless it requires persistent state across spins.

For automated classification, run `scripts/classify_family.py` against the layer names. It returns the family key, a confidence score, and the evidence (matched patterns, prefixes, layer composition hints).

---

## `hp_symbol` — High-Pay Symbol

**Purpose:** Premium / high-pay symbol presentation. Restrained win pulse, long shimmer idle, short land settle. Ranked from `HP1` (highest) downward.

**Naming contract:** `HP<rank>`, `HP<rank>idle`, `HP<rank>land`, `HP<rank>win`. Rank is 1-based and typically ends at the lowest premium (often `HP4`).

**Required layers:** `symbol_body.png` (proof) or, for layered character HPs, `*_head`, `*_BG`, `*_frame`.

**Optional layers:** `symbol_shadow.png`, `symbol_highlight.png`, `glow.png`, `sparkle.png`, `back_frame.png`, `front_frame.png`, `glass.png`. For character HPs: `*_head_eyes_blink`, `*_<character>_laugh`, `*_hand_L`, `*_hand_R`, `*_<character>_hat_top`, `*_frame_glow`, `*_arm_*`.

**Generated animations (proof scaffold):** `HP<rank>`, `HP<rank>idle`, `HP<rank>land`.

**Generated animations (layered character):** `idle` (4 s), `breathe` (2 s), `land` (0.4 s), `win` (2 s) on a shared timeline. Win composition for a Ho-Ho-Ho character is described in `references/spine_42_contract.md`.

**Controls:** `bounce_strength`, `land_duration_scale`, `idle_duration_scale`, `glow_intensity`, `sparkle_intensity`, `premium_intensity`, `motion_strength`, `feature_active_intensity`.

**Pitfalls:**
- Don't classify by visual style alone — use the role map.
- Don't treat the proof scaffold as a final production HP template.
- Stay restrained in motion amplitude (1–3 px translate, 2–6° rotate, ≤ 1.04 scale).

---

## `mp_symbol` — Medium-Pay Symbol

**Purpose:** Middle paytable symbols between LP and HP intensity.

**Naming contract:** `MP<rank>`, `MP<rank>idle`, `MP<rank>land`.

**Required layers:** symbol body. **Optional:** shadow, highlight, sheen.

**Generated animations:** `MP<rank>`, `MP<rank>idle`, `MP<rank>land` (proof).

**Controls:** as `lp_symbol`, scaled up slightly.

**Pitfalls:** Boundary between LP and MP and between MP and HP is studio-specific. When unsure, consult the role map.

---

## `lp_symbol` — Low-Pay Symbol

**Purpose:** Letter and numeric symbols (A / K / Q / J / 10 / 9). Single layer, gentle motion.

**Naming contract:** `LP<rank>`, `LP<rank>idle`, `LP<rank>land`. Convention: LP1 = A, LP2 = K, LP3 = Q, LP4 = J, LP5 = 10, LP6 = 9.

**Required layers:** symbol body. **Optional:** shadow, highlight, sheen.

**Generated animations:** `LP<rank>`, `LP<rank>idle`, `LP<rank>land` (proof). Conservative motion: small scale pulse, optional sheen sweep.

**Controls:** `idle_duration_scale`, `land_duration_scale`, `sheen_intensity` (when sheen slot exists).

**Pitfalls:** Don't add character-style motion to letters. Single scale pulse + slot color sheen is the right idle.

---

## `wild_symbol` — Wild Symbol

**Purpose:** Substitution symbol with shimmer / sparkle emphasis.

**Naming contract:** `WD<rank>`, `WD<rank>idle`, `WD<rank>land`. Or `WILD*`.

**Required layers:** symbol body. **Optional:** shimmer, sparkle, glow, sheen.

**Generated animations:** `WD<rank>`, `WD<rank>idle`, `WD<rank>land` (proof). Shimmer sweep on idle, decisive land impact.

**Controls:** `shimmer_intensity` (compiler-dependent; falls back to `sparkle_intensity`), `sparkle_intensity`, `land_duration_scale`.

---

## `scatter_symbol` — Scatter Symbol

**Purpose:** Trigger symbol with pop emphasis on land.

**Naming contract:** `SC<rank>`, `SC<rank>idle`, `SC<rank>land`, `SC<rank>smart`.

**Required layers:** symbol body. **Optional:** trigger emphasis layers, sheen.

**Generated animations:** `SC1`, `SC1idle`, `SC1land`, `SC1smart` (proof). Scatter-trigger pop, readable emphasis, compact land.

**Controls:** `pop_intensity` (compiler-dependent; falls back to `motion_strength`), `land_duration_scale`.

---

## `bonus_symbol` — Bonus Symbol

**Purpose:** Bonus feature trigger. Stronger feature glow and active pulse than baseline.

**Naming contract:** `BO<rank>`, `BO<rank>idle`, `BO<rank>land`, `BO<rank>smart`.

**Required layers:** symbol body. **Optional:** feature glow, active-state layer.

**Generated animations:** `BO1`, `BO1idle`, `BO1land`, `BO1smart` (proof).

**Controls:** `feature_active_intensity`, `glow_intensity`.

**Pitfall:** `bonus_symbol` and `bo_special_symbol` share naming. Use `bo_special_symbol` when art warrants BO-tier intensity (stronger win motion).

---

## `bo_special_symbol` — BO / Special Symbol

**Purpose:** BO-tier special symbol with stronger win motion than baseline bonus.

**Naming contract:** Same as `bonus_symbol` (`BO<rank>`, etc.).

**Required + optional layers:** as `bonus_symbol`.

**Generated animations:** `BO1`, `BO1idle`, `BO1land`, `BO1smart` (proof) with BO-tier amplitudes.

**Controls:** `feature_active_intensity`, `glow_intensity`, `motion_strength`, `premium_intensity`.

---

## `jackpot_symbol` — Jackpot Symbol

**Purpose:** Tiered jackpot reveals. Conventional tier order: `JP1` GRAND, `JP2` MAJOR, `JP3` MINOR, `JP4` MINI.

**Naming contract:** `JP<tier>`, `JP<tier>idle`, `JP<tier>land`, `JP<tier>smart`. Or `JackpotN`, `Tier<N>`.

**Required layers:** star or badge body. **Optional:** tier text overlay, sheen, glow.

**Generated animations:** `JP1`, `JP1idle`, `JP1land`, `JP1smart` (proof). Premium pulse, shine sweep, jackpot-weighted glow.

**Controls:** `premium_intensity`, `glow_intensity`, `shine_intensity` (compiler-dependent; falls back to `sparkle_intensity`).

---

## `special_feature_symbol` — Special Feature Symbol

**Purpose:** Triggers a feature mode (free spins, expanding wilds, etc.).

**Naming contract:** `SF<rank>`, `SF<rank>idle`, `SF<rank>land`, `SF<rank>smart`.

**Required layers:** symbol body. **Optional:** feature glow, active-state layer, sparkle.

**Generated animations:** `SF1`, `SF1idle`, `SF1land`, `SF1smart` (proof).

**Controls:** `feature_active_intensity`, `glow_intensity`.

---

## `value_symbol` — Value / WYS Symbol

**Purpose:** "Win Your Stake" / cash-on-reels symbols carrying a printed value (`$5`, `$100`, etc.).

**Naming contract:** `WYS<rank>`, `WYS<rank>idle`, `WYS<rank>land`. Or `WY*`, `CASH*`.

**Required layers:** body. **Optional:** value text overlay, sheen.

**Generated animations:** `WYS1`, `WYS1idle`, `WYS1land` (proof). Readable value pop, restrained motion.

**Controls:** `pop_intensity` (compiler-dependent; falls back to `motion_strength`), `idle_duration_scale`.

**Pitfall:** Text legibility matters. Avoid motion that obscures the printed value during readable beats. Keep idle scale ≤ 1.04.

---

## `winframe_explode` — WinFrame / Explode

**Purpose:** Decorative frame that pulses or explodes during a win.

**Naming contract:** `WinFrame`, `WinFrameidle`, `WinFrameExplode`.

**Required layers:** frame border. **Optional:** explode VFX.

**Generated animations:** `WinFrame`, `WinFrameidle`, `WinFrameExplode` (proof, single-layer).

**Pitfall:** This family is for STANDALONE frame VFX, not for the decorative back-frame of an HP/JP/etc. symbol. A static back-frame is part of its symbol's family. If the user calls a back-frame a "winframe", redirect.

---

## `meter` — Meter

**Purpose:** Progress meter UI element with multiple state stops.

**Naming contract:** `MeterIdle`, `State1Collect`, `State2Collect`, ..., `State5Collect`.

**Required layers:** base bar + state-stop pairs. **Optional:** segment fills.

**Generated animations:** `MeterIdle`, `State1Collect` through `State5Collect` (proof, single-layer).

**Pitfall:** Generic bar / fill art without explicit `State<N>Collect` animations is review-required, not auto-meter. The deterministic meter compiler is single-layer proof — stateful behavior (live fill animation, accumulation) is gated.

---

## `transition` — Transition

**Purpose:** Screen / state transitions (free-spins entry, bonus exit, etc.).

**Naming contract:** `intro`, `outro`, `FB_Transition`, `SB_Transition`.

**Required layers:** transition frames. **Optional:** mask layers, camera anchors.

**Generated animations:** `intro`, `TransitionIdle`, `outro`, `FB_Transition`, `SB_Transition` (proof, single-layer).

---

## `celebration` — Celebration

**Purpose:** Tier or jackpot win celebrations.

**Naming contract:** `grandJackpot`, `celebration_loop`, `tier_1`, `tier_2`, `tier_3`, `celebration_fx_1`, `burst`.

**Required layers:** tier value + burst FX.

**Generated animations:** representative single-layer celebration proofs.

**Controls:** `premium_intensity`, `motion_strength` (energetic tier).

---

## `avatar` — Avatar

**Purpose:** Persistent stateful character that reacts across spins.

**Naming contract:** `State0Idle`, `State0to1`, `State1Awarded`, `State1Close`, `State1Idle`, `State1to2`, `State2Awarded`, `State2Close`, ...

**Required layers:** character + state-machine frames.

**Generated output:** representative state idle / transition / awarded / close beats (proof, single-layer) plus `avatar_state_manifest.json`. The manifest records `default_state`, states, transitions, awarded/close beats, deterministic event names (`avatar/state_<n>_awarded`, `avatar/state_<n>_close`, `avatar/state_<from>_to_<to>`), expression/physics/IK support status, preview/art-approval flags, and `runtime_consumer_verified: false`.

**Pitfall:** Character-looking HP / special / wild art is NOT `avatar` unless it requires persistent state across spins. Reserve `avatar` for true state-machine acting content. Persistent state, event listeners, and state advancement remain game-runtime integration work; the manifest does not prove runtime consumption. If unsure, choose `hp_symbol` or `special_feature_symbol`.

---

## Review-gated families

These two families exist in the taxonomy but have no deterministic compiler template. Do not auto-classify into them; require human triage.

### `blocker_or_bonus_symbol` — Row Blocker / BL UI Gameplay Element

Locked-row mechanic with locked / break / unlock / reveal states. Naming typically `BL<rank>` or `Blocker*`. No deterministic compiler template yet. If the user has BL art, flag it for review and discuss what locked / unlock / reveal states their game needs before any compile is attempted.

### `non_symbol_or_unknown`

Anything that doesn't match the 15 implementable families. Surface the asset, list the layer names, and ask the user to classify. Do not guess.

---

## Motion amplitude tiers

Motion intensity scales with symbol importance. These are the *upper bounds* — gentle ranges within tiers are always acceptable.

| Tier | Translate | Rotate | Scale | Example families |
|---|---|---|---|---|
| Restrained | 1–3 px | 2–6° | ≤ 1.04 | `hp_symbol`, `mp_symbol`, `lp_symbol` |
| Medium | 3–5 px | 4–8° | ≤ 1.06 | `wild_symbol`, `scatter_symbol`, `value_symbol` |
| Energetic | 5–10 px | 6–12° | ≤ 1.10 | `bo_special_symbol`, `bonus_symbol`, `jackpot_symbol`, `special_feature_symbol`, `celebration` |

When the reference implementation has fitted per-role amplitudes from real human-authored Spine exports (e.g., the H5G `compiler_motion_profiles/latest_exact_motion_profile.json`), the compiler uses those values and falls back to this tier table when no fitted reference exists. Don't override the fitted values with these tier ranges; they're a floor / ceiling, not a target.

---

## Cross-family controls

A few controls apply across most families:

- `bounce_strength` (0.0–2.0) — scales land y-impact and x squash/overshoot magnitude.
- `land_duration_scale` (0.25–3.0) — scales land settle timing.
- `idle_duration_scale` (0.25–3.0) — scales idle loop duration.
- `motion_strength` (0.0–2.0) — scales pulse magnitude; combines with `bounce_strength` on land.
- `glow_intensity` (0.0–2.0) — scales glow slot alpha when glow exists.
- `sparkle_intensity` (0.0–2.0) — scales sparkle slot alpha when sparkle exists.
- `premium_intensity` (0.0–2.0) — scales lit / glass alpha; combines with glow / sparkle / win pulse.
- `feature_active_intensity` (0.0–2.0) — scales smart / feature-active loop intensity for families that emit a smart loop (BO/SF/JP/SC).

A control that targets a missing slot becomes a no-op (recorded as `unsupported_noop_controls` in `validation_report.json`). That's fine — emit the control and let the compiler decide whether it applies.

For the full control schema and natural-language mappings, read `references/controls.md`.
