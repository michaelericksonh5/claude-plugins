# Project Context and Learning Loop

The skill gets *better at your specific projects* over time. Each project (a game, a SKU, a season's worth of symbols) has its own `PROJECT_CONTEXT.json` that captures conventions, preferred defaults, and patterns learned from feedback. The skill reads this on every invocation and uses it to make better default choices — without needing a manual rewrite of the skill itself.

This file documents the schema, the workflow, the feedback hooks, and how the four moving parts fit together.

## The four moving parts

```
1. PROJECT_CONTEXT.json     →  per-project knobs the skill reads on invocation
2. LEARNING_LOG.jsonl        →  append-only history of builds + feedback
3. PATTERNS.md               →  human/Claude-readable distillation of the log
4. preferred_defaults block  →  the distilled patterns rolled back into the context
```

**Cycle.** Build → Log → Feedback → Log → Distill → Update context → Next build uses the learnings.

## When to bootstrap a project context

The skill auto-detects the context by walking up from the layer directory. If there's no `PROJECT_CONTEXT.json` in the project, the skill runs with global defaults — same as today.

To start collecting context for a project, run:

```
python scripts/project_context.py init <project_root> --name "Santa Pop / 4451"
```

Or pass `--bootstrap-context` to `build_spine_package.py` and it'll create one automatically next to the layer dir if missing.

## Schema (PROJECT_CONTEXT.json)

```json
{
  "schema": "spine_slot_animation_project_context_v1",
  "project_name": "Santa Pop / 4451",
  "game_id": "4451",
  "studio_id": "h5g",
  "spine_version": "4.3.04",
  "doc_dimensions": {"width": 178, "height": 178},
  "fps": 24,
  "naming": {
    "hp_pattern": "HP{rank}",
    "lp_pattern": "LP{rank}",
    "jackpot_tier_order": ["GRAND", "MAJOR", "MINOR", "MINI"]
  },
  "role_overrides": {
    "HP3_special": "special_feature_symbol"
  },
  "preferred_defaults": {
    "controls": {
      "hp_symbol": {"bounce_strength": 1.4, "land_duration_scale": 1.15, "motion_strength": 1.2}
    },
    "flags": {
      "composite_expressions": false,
      "render_qa_frames": true,
      "enable_ik": false,
      "enable_events": false,
      "enable_transform_constraints": false
    }
  },
  "motion_profile_fit": {
    "hp_symbol": {"translate_px_max": 3.0, "rotate_deg_max": 5.0, "scale_max": 1.04}
  },
  "feedback_summary": {
    "successful_builds": 12,
    "revised_builds": 5,
    "common_revisions": [{"control": "bounce_strength", "occurrences": 5}]
  },
  "history": {
    "log_path": "LEARNING_LOG.jsonl",
    "patterns_path": "PATTERNS.md",
    "last_distilled": "2026-05-17T16:30:00Z",
    "bootstrapped_at": "2026-04-10T09:00:00Z"
  }
}
```

**Hand-edit guidance.**

- `project_name`, `game_id`, `studio_id`, `naming`, `role_overrides`, `doc_dimensions`: user-owned. The distiller never touches these.
- `preferred_defaults`, `feedback_summary`, `history.last_distilled`: auto-updated by `distill_patterns.py --update-context`. Hand-editing them is fine but they'll be overwritten the next time you distill.
- `motion_profile_fit`: hand-edited from real-export evidence (e.g., the H5G `compiler_motion_profiles/latest_exact_motion_profile.json`).

## How the skill uses the context

When `build_spine_package.py` runs:

1. Walks up from `--layer-dir` until it finds a `PROJECT_CONTEXT.json` (or accepts `--project-context-path` explicit override).
2. Applies preferred-default flags that the user *didn't* set on the CLI (e.g., if the context says `render_qa_frames: true` and the user didn't pass `--render-qa-frames`, it gets enabled).
3. Loads `preferred_defaults.controls[<family>]` and uses it as the *base* controls dict. Anything the user passes via `--controls` *overrides* the context defaults, so the user always has the final say.
4. Records the build in `LEARNING_LOG.jsonl` along with the resolved controls, flags, validation status, and which context defaults were applied.
5. If the build failed validation, also logs a `validation_failure` entry so recurring issues surface in the distillation.

To skip context entirely on a one-off build, pass `--no-context`.

## The learning log

`LEARNING_LOG.jsonl` is append-only. Each line is one JSON object. The schema is `spine_slot_animation_learning_log_entry_v1`. Event types:

- `build` — emitted by `build_spine_package.py` on every run.
- `feedback` — emitted by `capture_feedback.py` when the user accepts / revises / rejects a build.
- `validation_failure` — emitted by `build_spine_package.py` when the package failed strict validation.
- `context_update` — reserved for tooling that mutates the context outside the build flow.

The log is the source of truth. The context's `feedback_summary` is a derived view; you can always re-derive it by running `distill_patterns.py` again.

## Feedback capture

After a build, the user decides what to do:

```
# Looks good, ship it
python scripts/capture_feedback.py <project_root> --build <out_dir> --accept

# Wanted something different
python scripts/capture_feedback.py <project_root> --build <out_dir> --revise \
    --controls '{"bounce_strength": 1.4}' --note "art lead wanted more bouncy"

# Don't use as a basis for learning
python scripts/capture_feedback.py <project_root> --build <out_dir> --reject \
    --note "WebGL seam; needs --composite-expressions"
```

The disposition matters:

- **accepted** — the build's `controls_applied` becomes evidence for the distilled defaults.
- **revised** — the user's revisions are logged separately; recurring revisions surface in PATTERNS.md as "Recurring revisions (user asks for these often)".
- **rejected** — the build is excluded from the distilled defaults entirely.

Skill-side: when Claude is invoked and a recent build hasn't been graded yet, the right behavior is to ask the user what they thought (accept/revise/reject) before starting a new build.

## Distillation

`distill_patterns.py` walks the log and produces:

- **PATTERNS.md** — human-readable summary: total builds, accepted vs revised counts, median controls per family across accepted builds, flags commonly enabled (≥50% of builds), recurring revisions, recurring validation failures.
- **PROJECT_CONTEXT.json updates** (with `--update-context`) — rolls median controls into `preferred_defaults.controls[<family>]` and commonly-enabled flags into `preferred_defaults.flags`.

The distillation uses *median* (not mean) of accepted-build controls because a couple of extreme outliers shouldn't shift the default. It only emits values that differ from `1.0` by more than `0.05` — close-to-default values stay omitted so the JSON doesn't fill up with noise.

**When to run distillation.** After every ~5 builds with feedback, or any time the user wants to "promote" current learnings. The skill can also auto-suggest a distill when the log has new feedback entries since the last `history.last_distilled` timestamp.

## How this scales across projects

Each project is independent: `PROJECT_CONTEXT.json` lives at the project root, the log lives next to it. Two different games can have wildly different `preferred_defaults` and the skill will use the right one based on which `--layer-dir` you pass.

**Cross-project knowledge transfer** (planned, not bundled today): when a new project bootstraps, the skill could read sibling projects' contexts and seed initial defaults from family-level averages. For now, each project starts fresh with `bounce_strength: 1.0` etc. and earns its defaults through feedback.

## Integration with Claude's memory system

Claude's auto-memory (project, feedback, user-preference memory types) sits *alongside* the project context, not inside it. The right split:

- **`PROJECT_CONTEXT.json`** is project-scoped knobs the skill itself reads on every invocation. Versioned with the project's files.
- **Claude's memory** is conversation-scoped facts that span projects: "this user prefers terse responses," "the studio is currently on Spine 4.3.04," "this user dislikes when I propose hand-editing JSON."

A future iteration could have `capture_feedback.py` optionally write a memory entry when a strong pattern emerges (e.g., "every HP build for this user gets revised to bouncier; remember that across conversations").

## A worked example

Day 1: bootstrap.

```
python scripts/project_context.py init ~/santa_pop --name "Santa Pop / 4451"
python scripts/build_spine_package.py --layer-dir ~/santa_pop/HP3 --family hp_symbol --rank 3 \
    --doc-width 178 --doc-height 178 --out-dir ~/santa_pop/HP3_out_v1
# Art lead says "too restrained, want a bouncier feel"
python scripts/capture_feedback.py ~/santa_pop --build ~/santa_pop/HP3_out_v1 --revise \
    --controls '{"bounce_strength": 1.4, "land_duration_scale": 1.15, "motion_strength": 1.2}' \
    --note "art lead wanted bouncier"
```

Day 1, build 2:

```
echo '{"bounce_strength": 1.4, "land_duration_scale": 1.15, "motion_strength": 1.2}' > ~/santa_pop/bouncy.json
python scripts/build_spine_package.py --layer-dir ~/santa_pop/HP3 --family hp_symbol --rank 3 \
    --doc-width 178 --doc-height 178 --controls ~/santa_pop/bouncy.json --out-dir ~/santa_pop/HP3_out_v2
python scripts/capture_feedback.py ~/santa_pop --build ~/santa_pop/HP3_out_v2 --accept
```

End of day: distill.

```
python scripts/distill_patterns.py ~/santa_pop --update-context
# Now PROJECT_CONTEXT.json says:
#   preferred_defaults.controls.hp_symbol = {"bounce_strength": 1.4, "land_duration_scale": 1.15, "motion_strength": 1.2}
```

Day 2: HP4 needs to be built. The skill reads the context, finds the learned defaults for `hp_symbol`, and produces a bouncier HP4 by default. No manual flags needed.

```
python scripts/build_spine_package.py --layer-dir ~/santa_pop/HP4 --family hp_symbol --rank 4 \
    --doc-width 178 --doc-height 178 --out-dir ~/santa_pop/HP4_out_v1
# Output line: "applied family defaults from context: {'motion_strength': 1.2, 'land_duration_scale': 1.15, 'bounce_strength': 1.4}"
```

The skill got smarter about this project without anyone editing the skill.

## What this is and isn't

**Is:**

- Per-project knobs the skill auto-reads.
- An append-only feedback log.
- A distillation pass that rolls accepted controls into defaults.
- A way for the skill to ship better outputs over time on the projects you actually work on.

**Isn't:**

- A training loop on the skill itself. The skill's *code* is unchanged; only the context's knobs evolve.
- A statistical model. Distillation uses simple median + frequency counts, not ML.
- A cross-conversation memory for Claude. Use Claude's auto-memory for facts that span projects.
- A replacement for human review. Accepted/revised/rejected dispositions are explicit user signals; nothing gets baked into defaults without a user action.

## Boundaries

- **The log records inputs and outcomes, not source pixels.** PSDs and PNGs stay in source-art directories; the log only stores their *paths*.
- **`PROJECT_CONTEXT.json` is the source of truth for project knobs.** If two contexts disagree (e.g., a sibling project context found higher up the directory tree), the closest one to the layer dir wins. `--project-context-path` is the explicit override.
- **`PATTERNS.md` is read-only output.** Don't hand-edit it; it gets regenerated on every distill.
- **The skill never modifies the log itself.** Only `learning_log.py` writes to it. Even distillation only *reads* the log.

That's the system. Build, give feedback, distill, build again with smarter defaults.
