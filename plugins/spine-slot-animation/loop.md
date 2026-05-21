# Loop Closure Plan

## Goal

Make loop behavior explicit and validated. A loop is not "good enough because it has a loop-like name"; the compiler must classify animation intent and prove looped timelines close without popping.

## Research Baseline

- `research/LAYERED_RIG_COMPILER_NOTES.md` defines `idle` as a 4.0s loop and `breathe` as a 2.0s loop kept loopable. It describes `land` as a 0.4s impact and `win` as a 2.0s feature beat.
- `research/FULL_DEEP_ANIMATION_BAKEOFF_FINDINGS.md` says the compiler feedback loop should use human-animation bakeoff results and that layered rigs should compose coordinated shared timelines for `idle`, `breathe`, `land`, and `win`.
- `research/CLAUDE_PROJECT_GUIDE.md` says proof packages must be proven by deterministic tools and validators, not claimed.
- `research/hp_symbol_proof_compiler.py` already has an idle-specific `validate_idle_loop` check for the proof compiler. The portable skill needs the same idea generalized across looped animations.
- `scripts/compose_animations.py` labels or structures `idle`, `breathe`, `smart`, `MeterIdle`, `TransitionIdle`, `WinFrameidle`, and `celebration_loop` as loops. `land`, `win`, collects, transitions, explodes, awarded, and close beats are one-shot or settle/transition animations.
- `scripts/bezier_curves.py` already preserves key times, source durations, and equal endpoints when applying Bezier curves. Loop closure should run after all timeline decoration so it catches final emitted JSON.

## Animation Intent Contract

Each emitted animation gets one loop intent:

- `setup`: rest/default animation with no performance loop.
- `loop`: must close. First and terminal state must match for every active bone/slot timeline.
- `settle_to_setup`: one-shot beat whose final keyed state must return to setup/baseline for keyed channels.
- `transition`: intentionally changes state or visibility; not loop-closed.
- `burst`: one-shot effect; not required to close unless separately marked.

Initial policy:

- `loop`: `*idle`, `*breathe`, `*smart`, `MeterIdle`, `TransitionIdle`, `WinFrameidle`, `celebration_loop`, `State<N>Idle`, `Avatar`.
- `settle_to_setup`: symbol `*land`, symbol `*win`, `State<N>Awarded`, and meter collect beats when their channels return to baseline.
- `transition`: `State<N>to<M>`, `State<N>Close`, `intro`, `outro`, `FB_Transition`, `SB_Transition`, `WinFrame`, `WinFrameExplode`.
- `burst`: `burst`, `celebration_fx_*`, `tier_*`, `grandJackpot` until product/runtime policy declares them looped.

## Implementation Phases

### Phase 1: Deterministic Loop Validator

Add `scripts/loop_validation.py` with:

- `classify_animation_intent(animation_name, family)` to return the intent above.
- `validate_animation_loops(skel, family)` to inspect final emitted Spine JSON.
- Channel-aware comparisons:
  - bone `translate`: `x`, `y`, baseline `0`.
  - bone `rotate`: `value`, baseline `0`.
  - bone `scale`: `x`, `y`, baseline `1`.
  - bone `shear`: `x`, `y`, baseline `0`.
  - slot `rgba`, `rgba2`, `alpha`, `attachment`, and `sequence` first/terminal state equality for `loop`.
- Tolerance for numeric float differences.
- A machine-readable report with `animations`, `loop_count`, `settle_count`, `issues`, and `status`.

### Phase 2: Compiler Integration

Wire the validator into `scripts/build_spine_package.py` after `assemble_skeleton_json()` and after Bezier/sequence/expression mutations are complete. Add:

- `animation_loop_validation` to `validation_report.json`.
- Top-level `animation_loop_intents`.
- Top-level `loop_validation_status`.
- Hard failure when the loop validator reports issues.

### Phase 3: Eval Coverage

Extend `tests/test_phase1_local_evals.py`:

- Positive: representative HP package reports `HP3idle` and `HP3breathe` as `loop` and `HP3land`/`HP3win` as `settle_to_setup`.
- Positive: `winframe_explode` reports `WinFrameidle` as `loop` and one-shots as transition/burst.
- Positive: avatar reports `State<N>Idle` and `Avatar` as loops.
- Guard: mutate an emitted idle endpoint and assert the validator reports a loop-closure issue.
- Guard: mutate a land/win final baseline and assert the validator reports a settle issue.

### Phase 4: GitHub Hygiene

Update `.gitignore` so GitHub does not collect local proof artifacts by accident:

- Ignore `generated/`.
- Keep source scripts, policies, docs, tests, and eval registry tracked.
- Keep `_workspace/` tracked for existing benchmark evidence unless the marketplace packaging step decides otherwise.

### Phase 5: Verification

Run:

```powershell
python scripts/run_local_evals.py
python scripts/build_runtime_acceptance_fixtures.py
npx -p playwright node scripts/runtime_acceptance_probe.mjs --packages-root generated/runtime_acceptance/packages
```

Expected:

- Local eval suite passes.
- Runtime acceptance probe still reports `verified_browser_runtime`.
- Representative packages have no loop-validation failures.

## Marketplace Gate

Do not publish stronger claims until:

- `loop_validation_status` is `ok` on representative packages.
- Browser runtime probe still passes.
- Skill docs say looped animations are validated, while one-shot win/land/transition beats are validated according to their settle/transition intent.
- GitHub ignores local generated proof outputs unless intentionally packaged.
