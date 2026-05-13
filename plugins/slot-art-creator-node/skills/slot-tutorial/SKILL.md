---
name: slot-tutorial
description: Guided walkthrough of the slot-art-creator-node plugin from start to finish. Walks the user through the 00→10 numbered workflow using a concrete sample game brief, showing what each step produces, what state changes, and what gates have to pass before moving on — without spending API credits unless the user opts in. Default mode is DRY (read-only tour with worked examples and live state from the user's active project if any). LIVE mode actually invokes each step against a sample brief and generates real assets with the user's keys. Use this for first-time users learning the plugin, for returning users coming back after a long gap, for new H5G hires who need a structured walkthrough, or anyone who says "show me how this works", "give me a tutorial", "walk me through the workflow", "teach me", "I'm new — can I see an example?", "what does each step actually produce?", or asks for an end-to-end demo. Prefer this over /slot-help when the user wants a teaching experience instead of just a one-page menu.
---

# Slot Tutorial — Guided Workflow Tour

`/slot-help` shows the menu. This skill **teaches the workflow** by
walking through it with a concrete example, step by step, with a
mid-tour decision point so the user can either keep touring (free) or
flip into live mode and actually generate the sample game (costs API
credits).

The tutorial is structured so a new user finishes it knowing:
- What each numbered step does and when to run it
- What "locking the brief" / "locking the key art" actually means in
  terms of `project.json` state
- Where files land on disk
- Which gates each step enforces and what they catch
- How the model-family routing works (NB2 vs gpt-image-2) and when
  each one wins
- How project memory survives across sessions

## Modes

| Mode | What happens | Cost |
|---|---|---|
| **DRY (default)** | Tour the workflow with a worked example. Read each `slot-step-NN/SKILL.md`, summarize the inputs/outputs/gates, show sample state diffs, but never call MCP generation tools. | Zero API credits. |
| **LIVE (opt-in)** | Actually invoke each step against the sample brief. Generates real assets in a sandboxed tutorial project folder. User keeps the outputs. | Real cost — typically ~$2–$5 for the full tour depending on which model family runs. |

Start in DRY mode. Offer to flip to LIVE only after the user has seen
Step 1 and 2 and confirmed they want to spend credits on the tour. If
they say "go live from the start", honor it — they know what they're
asking for.

## Startup protocol

1. Check if the user has API keys set
   (`~/.h5g-slot-art-creator/.env` — `GEMINI_API_KEY`, `FAL_KEY`,
   `OPENAI_API_KEY`). If **none** are set:
   - In DRY mode, that's fine — keep going, just note "you can still
     do the tour; flipping to LIVE later will require `/slot-setup`".
   - If the user explicitly asks for LIVE mode and has no keys, stop
     and route them to `/slot-setup`.
2. Check if there's an active project
   (`~/.h5g-slot-active-project.json`). If yes, ask whether they want
   the tour to:
   - **Use the active project for examples** — read its `project.json`
     and show real state diffs. Recommended for returning users who
     want a refresher.
   - **Use a fresh sandbox project** — create
     `<PROJECT_BASE>/tutorial_<username>/` and treat it as a clean
     slate. Recommended for first-time users so they don't risk
     touching real work.

   If no active project exists, default to the sandbox path silently
   in DRY mode (no folder is actually created — DRY is read-only).
   In LIVE mode, create the sandbox folder before any generation call.

## The sample game

Use this brief throughout the tutorial. It's intentionally compact —
the goal is to teach the workflow, not to design a real game.

```yaml
game_name:        "Sun & Moon Sanctuary"
mood:             "mystical balanced"
theme_summary:    "A celestial temple where day and night deities trade
                   power across the spin — warm gold suns rule high
                   pays, cool blue moons rule low pays, and a phoenix
                   wild flips the balance."
style_lock:       "stylized semi-realistic slot game art"
palette_leads:
  primary:        "warm gold and burning crimson"
  accents:        "cool indigo and silver moonlight"
  forbidden_on_lp: "warm gold, amber, crimson"
grid:             "5x4"
tier_plan:
  hp_count: 2
  mp_count: 2
  lp_count: 6
  lp_family: "card royals"
  specials: ["wild", "scatter", "bonus"]
wild:             "WILD wordmark wrapped in electric cyan phoenix
                   feathers — categorically different from the suns
                   and moons in both shape and color"
scatter:          "circular badge — SCATTER label inside a radiant
                   gold sun sigil"
avatars:
  - Avatar1:      "Sun deity — golden-skinned figure in flowing
                   crimson robes, radiant halo behind the head,
                   cheers on day wins"
  - Avatar2:      "Moon deity — silver-skinned figure in deep indigo
                   robes, crescent crown, calm presiding presence
                   over night-themed bonuses"
```

(Many real games ship with zero avatars; *Sun & Moon Sanctuary* uses
two to make the tutorial show off the avatar workflow. Adapt to your
own brief — if a game has no avatars, skip the avatar walkthrough.)

Carry this through every step of the tour. The user sees a single
coherent example from brief to delivery instead of a dozen disconnected
fragments.

## Workflow

### Step 1 — Set expectations

Open with one paragraph: "This is a hands-on tour of the 00→10
workflow. I'll walk through each step with the *Sun & Moon Sanctuary*
example, show you exactly what each step produces and what state it
locks, and at the end you'll have a working mental model of how the
plugin moves a game from concept to delivery. We're in DRY mode by
default — no API credits get spent. I'll offer to flip to LIVE after
Step 2."

Then ask: "Ready, or want a different example game?" If they want a
different example, take their input and substitute into the sample
brief above. Don't get stuck designing the example — accept one
sentence ("dragons in a jade temple") and infer reasonable values.

### Step 2 — Tour /slot-setup and /slot-help

These are the two non-numbered skills. Read their `SKILL.md` files
briefly and summarize:

- `/slot-setup` — runs once per machine to configure API keys for the
  three providers (Google Gemini, fal.ai, OpenAI). The user never
  pastes keys in chat; they go directly into a config file.
- `/slot-help` — orientation menu the user can return to any time.

Confirm to the user that **either** Gemini *or* fal.ai is sufficient
for the NB2 workflow; OpenAI's gpt-image-2 is an optional second model
family that wins on text-heavy assets (paytables, logos). Show them
which keys are present in their actual `.env`.

### Step 3 — Decision point: keep touring DRY, or flip to LIVE

Show the cost / benefit table:

```
DRY (default)
  ✓ Zero API credits
  ✓ Real state diffs from your project.json
  ✓ See every prompt, every gate, every state transition
  ✗ No actual generated images — sample is described, not rendered

LIVE (opt-in)
  ✓ All of the above PLUS real generated assets in your tutorial folder
  ✓ You keep the outputs — they live in <project_root>/ like any project
  ✗ Real cost — roughly $2–$5 for the full tour
  ✗ Requires at least one of GEMINI_API_KEY / FAL_KEY (OPENAI optional)
```

Ask explicitly: "DRY or LIVE for the rest of the tour?" Record the
answer and carry it through.

### Step 4 — Walk through /slot-step-00 (GDD Connect)

For each numbered step from here through Step 10, follow this 5-part
pattern. The pattern is what gives the tutorial its teaching shape —
do not skip parts.

**Pattern (apply to every step):**

1. **Read the step's `SKILL.md` frontmatter description.** Show the
   user the first sentence — that's the one-line summary.
2. **Name the inputs.** What does this step require to already be in
   `project.json` or on disk? Trace each prerequisite to the step
   that produced it.
3. **Show the gate.** Every generation step (02–07) has pre- and
   post-generation gates. List the 3–4 most important checks in plain
   language. Explain *why* each one exists — not just "what it does".
4. **Show the state diff.** Read `shared/project_memory.md` "asset
   record shape" and show a 3–5 line diff of what fields change in
   `project.json` after this step locks. For non-locking steps
   (like /slot-step-00 which seeds the brief), show what gets created.
5. **In LIVE mode only: actually run it.** Build the prompt from the
   *Sun & Moon Sanctuary* sample, route to the correct MCP tool, and
   pass the canonical references. In DRY mode, describe what the
   prompt would look like but don't call any MCP tool.

For step 00 specifically:

- **Inputs:** Drive integration enabled in Claude settings + a GDD
  file accessible to the user. **Optional step** — if pitching fresh,
  skip directly to /slot-step-01.
- **Gate:** Drive MCP tools detected at startup; if missing, the step
  refuses to run and routes the user to enable Drive or skip to 01.
- **State diff:** Creates `project_root`, writes `project.json` with
  `gdd_source` populated, writes a partial `game_brief.json`.
- **DRY:** "We'd skip this step for *Sun & Moon Sanctuary* — it's a
  fresh pitch, no GDD to load."
- **LIVE:** Same — skip this step in the tour unless the user supplies
  a real GDD URL.

### Step 5 — Walk through /slot-step-01 (Game Brief)

Same 5-part pattern:

- **Inputs:** None hard-required. May read seed data from /slot-step-00
  if it ran first.
- **Gate:** Style lock must match one phrase from `shared/nb2_prompting.md`
  §9.4; palette must be named colors (no hex); LP family must be one
  family (not mixed); style_anchor.text must be 60–90 words. The skill
  refuses to persist until the user explicitly says "lock it".
- **State diff:**
  ```diff
  + project.json.brief = { full structured brief }
  + project.json.style_anchor.text = "<60–90-word block>"
  + project.json.current_step = "brief_locked"
  + project.json.next_step = "/slot-step-02"
  + game_brief.json (human-readable mirror)
  ```
  Show the user `shared/project_memory.md` → "`style_anchor` field
  contract" if they ask why text and key_art_path both live under
  `style_anchor`.
- **DRY:** Show the *Sun & Moon Sanctuary* `style_anchor.text` block
  built from the sample brief above. This is the single most important
  artifact from this step — every later prompt prepends it verbatim.
- **LIVE:** Actually invoke `/slot-step-01` with the sample brief and
  let it write `project.json` to the tutorial project folder.

### Step 6 — Walk through /slot-step-02 (Key Art)

- **Inputs:** Locked brief from Step 01.
- **Gate (pre):** style_lock present verbatim; no UI elements; one
  hero subject; three-layer composition. **Gate (post):** style match,
  no UI bleed-through, single focal subject, palette aligned.
  Auto-iterates up to 2 retries on BLOCK findings before surfacing
  to the user.
- **State diff (on approval):**
  ```diff
  + project.json.assets.key.iterations += ["Key_Art/Key_Art_001.png", ...]
  + project.json.assets.key.approved = "Key_Art/Key_Art_003.png"   (e.g.)
  + project.json.style_anchor.key_art_path = "Key_Art/Key_Art_003.png"
  + project.json.style_anchor.locked_at = "<ISO timestamp>"
  + project.json.current_step = "key_art_locked"
  ```
  Highlight that `style_anchor.key_art_path` is the field every
  downstream skill reads to pass the key art as a reference image.
- **DRY:** Show the master prompt assembled from the sample brief
  and `slot-step-02/KEY_ART_TEMPLATE.md`. Don't generate.
- **LIVE:** Generate 1–2 iterations, let the user pick one, lock it.

### Step 7 — Walk through /slot-step-03 (Symbols)

- **Inputs:** Locked key art (`style_anchor.key_art_path` set).
- **Gate (pre):** Tier-specific checks from the per-prefix template
  files. **LP discipline** is the high-stakes one: zero instances of
  `gold`/`amber`/`warm`/`detailed`/`ornate`/`rich`/`glowing` in any
  LP prompt. **Gate (post):** Background color matches tier rule, LP
  has no warm trim, wild palette breaks the set, silhouette readable
  at thumbnail. Auto-iterates up to 2 retries.
- **State diff (per symbol approved):**
  ```diff
  + project.json.assets.symbols.HP1.iterations += ["Symbol_Art/HP1_001.png", ...]
  + project.json.assets.symbols.HP1.approved = "Symbol_Art/HP1_002.png"  (e.g.)
  + project.json.current_step = "symbols_in_progress"
  ```
- **Family routing:** Pull from the prefix table in
  `slot-step-03/SKILL.md` — the user should see which template
  routes which prefix (HP, MP, LP, WD/WD2+, SC/SW, WY, BO, BAG/MOJ,
  COL/ACT/HOT_*, SF, BL, JP1–JP6, D2_/D3_/SPLIT_/MULT_, BALL/PEG/BUCKET).
  This is the moment where new users realize the plugin handles way
  more than just "HP/MP/LP".
- **DRY:** Show the HP1 prompt for *Sun & Moon Sanctuary* assembled
  from `HP_TEMPLATE.md`. Don't generate.
- **LIVE:** Generate HP1 and LP1 only (not the full 13-symbol set) —
  that's enough to teach the gate behavior without blowing the budget.

### Step 8 — Walk through /slot-step-04 (Symbol Sheet)

- **Inputs:** Locked key art. Mode auto-detected from how many
  symbols have `.approved` set: <50% → IDEATION, ≥50% → ASSEMBLE.
- **Gate (pre):** Each cell's tier phrase is stated, LP cells include
  the "no gold or warm trim" clause, wild breaks category, cell count
  matches the brief's manifest size. **Gate (post):** Tier gradient
  reads at a glance, no LP gold, wild stands out.
- **State diff:**
  ```diff
  + project.json.assets.sheet.iterations += ["Symbol_Sheets/Sheet_001.png", ...]
  + project.json.assets.sheet.approved = "Symbol_Sheets/Sheet_002.png"
  + project.json.current_step = "sheet_locked"
  ```
  Explicitly note: there is **no** `game_brief.json.symbol_sheet_path`
  field — that was the old v0 location and is no longer read by any
  skill. Sheets live in `project.json.assets.sheet`.
- **DRY:** Show the ideation-mode prompt with all 13 *Sun & Moon
  Sanctuary* cells described, plus the explanation of how Mode A and
  Mode B differ in their `references` array (ideation passes only
  the key art; assemble passes key art + every approved symbol).
- **LIVE:** Generate a single ideation sheet from the brief alone
  (no individual symbols needed) so the user sees the full set in
  one shot.

### Step 9 — Walk through /slot-step-05 (Backgrounds)

- **Inputs:** Locked key art; approved sheet helpful but not required.
- **Gate:** Bottom 30% dark for UI, reel zone dimmed, three-layer
  composition, BG palette recedes behind symbol palette ("the reel is
  the hero" — `shared/art_principles.md` §1 #7).
- **State diff:**
  ```diff
  + project.json.assets.backgrounds.base.iterations += ["Backgrounds/BG_base_001.png", ...]
  + project.json.assets.backgrounds.base.approved = "Backgrounds/BG_base_001.png"
  + project.json.current_step = "backgrounds_in_progress"
  ```
- **DRY:** Show the 9:16 portrait prompt with the four hard rules
  spelled out.
- **LIVE:** Generate the base background only (skip free-spins /
  bonus / pick-me / wheel for the tour).

### Step 10 — Walk through /slot-step-06 (UI Surfaces + Avatars)

- **Inputs:** Locked key art, approved sheet, approved background.
- **Routing:** This is where users first meet the **NB2 vs
  gpt-image-2** decision. Show them the routing table from
  `slot-step-06/SKILL.md` Step 4:
  - `paytable` and `logo_<lockup>` prefer `gpt2_generate` when
    `OPENAI_API_KEY` is set — gpt-image-2 renders text correctly,
    NB2 hallucinates letters in stylized fonts. **gpt-image-2 outputs
    at up to 2K (2048px on the long edge) — do not request 4K from
    this model family; use nb2_upscale after 2K for a genuine 4K.**
  - `bezel`, `hud`, `bonus_screen`, `multiplier_xN`, `lobby_tile`,
    `avatar_<id>` stay on NB2.
- **This step also generates in-game avatars** (the player-facing
  animated characters that react to wins). For *Sun & Moon Sanctuary*,
  the brief implies two avatars — a sun deity and a moon deity. Some
  games have zero avatars; some have up to five. Avatars follow
  **character-design discipline** (idle pose, neutral, character-zone
  scale) rather than chrome discipline — see `AVATAR_TEMPLATE.md`.
- **Per-surface folder routing:** each surface lands in its own
  category folder (`Bezels/`, `HUD/`, `Paytables/`, `Win_Banners/`,
  `Bonus_Screens/`, `Wheels/`, `Multipliers/`, `Logos/`,
  `Lobby_Tiles/`, `Avatars/`). The skill picks the right `output_dir`
  from the surface name; the user doesn't have to remember.
- **Bonus wheels (when the brief has a wheel mechanic):** route
  `wheel_<variant>` (jackpot / bonus / multiplier / pickem) to
  `WHEEL_TEMPLATE.md`. Output is a complete single graphic — outer
  frame + slices + hub + pointer in one PNG — landing in `Wheels/`,
  not per-slice files. Slice tier colors follow the same pay
  spectrum as symbols (cool lows → warm highs → gold jackpot); the
  jackpot wheel's slice labels must match `brief.jackpot_tier_names`
  exactly. `Sun & Moon Sanctuary` has no jackpot tiers so this
  surface stays empty in the tutorial; mention it as the path a
  jackpot-style game would take.
- **Gate:** UI must rank below symbols in brightness; bezel center
  must be transparent (would otherwise cover reels); banner numeral
  is the focal point; avatars sit between HP and MP intensity.
- **State diff (per surface approved):**
  ```diff
  + project.json.assets.ui.bezel.iterations += ["Bezels/Bezel_001.png", ...]
  + project.json.assets.ui.bezel.approved = "Bezels/Bezel_001.png"
  + project.json.assets.avatars.Avatar1.iterations += ["Avatars/Avatar1_001.png", ...]
  + project.json.assets.avatars.Avatar1.approved = "Avatars/Avatar1_001.png"
  + project.json.current_step = "ui_in_progress"
  ```
- **DRY:** Show the bezel prompt and (separately) the gpt2_generate
  paytable prompt so the user sees the chrome-vs-text contrast.
  Optionally show the AVATAR_TEMPLATE idle-pose prompt for the
  Sun & Moon Sanctuary sun deity so they see character-design
  discipline.
- **LIVE:** Generate the bezel only (skip avatars in the tour unless
  the user opts in — they're a step the brief may not include).

### Step 11 — Walk through /slot-step-07 (UI Reskin, optional)

- **Inputs:** Locked key art, an existing UI mock to reskin
  (user-provided path).
- **When to use:** Reusing a proven UI layout across a reskinned
  game, or matching a partner's reference UI. For from-scratch UI,
  Step 06 is correct.
- **Routing:** Same two-tool decision as Step 06 — `gpt2_edit` when
  the source UI has visible text labels, `nb2_edit` for pure chrome.
- **Gate:** 8-axis layout-preservation rubric (control count,
  positions, proportions, typographic hierarchy, spacing, theme
  application, material consistency, decorative motifs).
- **DRY:** Show the 5-part bracketed-block prompt structure from
  `RESKIN_TEMPLATE.md` — preservation block first, surface-changes
  block second.
- **LIVE:** Skip in the tour unless the user has a real source UI
  to reskin.

### Step 12 — Walk through /slot-step-08 (Final Audit)

- **Inputs:** A complete (or near-complete) set in scope.
- **Output:** A written `QA_NNN.md` report graded RED / YELLOW /
  GREEN, saved to `{project_root}/QA_NNN.md`.
- **Gate:** Auto-RED escalations dominate — any LP shows
  gold/amber/warm, HP and LP have the same warmth, export BG has a
  gradient instead of flat solid, wild uses the same palette as the
  set, any symbol unreadable at 64px, style varies between two
  symbols in the same set, LP family is mixed.
- **DRY:** Walk through what a GREEN report looks like vs a RED one
  for the sample game. Explain how `next_step` is set:
  GREEN → `/slot-step-09`; YELLOW/RED → the specific design skill
  that owns the failing assets (so the audit doesn't just complain,
  it routes the user back to the fix).
- **LIVE:** Run the audit against whatever was generated in the
  LIVE tour so far. Honest GREEN/YELLOW/RED, not a participation
  trophy.

### Step 13 — Walk through /slot-step-09 (Upscale)

- **Inputs:** An approved 2K asset to upscale. Typically run after
  Step 08 passes GREEN.
- **Gate:** 8-axis preservation rubric (identity, pose, render
  style, palette, detail parity, background, micro-quality, framing).
  3 attempts max per asset (initial + 2 retries) — if all 3 fail,
  the source is the problem, not the prompt.
- **DRY:** Show the 6-part preservation template from
  `UPSCALE_TEMPLATE.md`. Explain why NB2 wants to regenerate rather
  than upscale and why this prompt structure forces it into
  upscale mode.
- **LIVE:** Upscale `Symbol_Art/HP1_002.png` only — cheapest demonstration. Output lands at `Symbol_Art/HP1_002_upscl_x2.png`.

### Step 14 — Walk through /slot-step-10 (Smart Resize)

- **Inputs:** An approved asset to produce in multiple aspect ratios.
- **Routing:** Two-way decision based on which key is set:
  - `FAL_KEY` set? → `nb2_smart_resize` routes to fal.ai NB Pro
    (single API call to the purpose-built endpoint — preferred)
  - Gemini-only? → `nb2_smart_resize` routes to Gemini and does a
    local pngjs center-crop per target (works fully; just more calls)
- **No gpt-image-2 path for resize.** A `gpt2_smart_resize` tool was
  prototyped in earlier 1.5.x releases but removed in v1.5.3 — its
  output quality wasn't verified against the well-tested fal.ai
  path. For text-heavy sources, either generate the new aspect ratio
  fresh at 2K with `gpt2_generate`, or accept that text may need to
  be re-composited at runtime.
- **Gate:** Per-aspect inline review — subject preserved, palette
  consistent, no awkward crops.
- **State diff:**
  ```diff
  + project.json.assets.<slot>.resized += [
  +   {"aspect": "1:1",  "dimensions": "2048x2048", "path": "Key_Art/Key_Art_001_resize_2048_2048.png"},
  +   {"aspect": "16:9", "dimensions": "3840x2160", "path": "Key_Art/Key_Art_001_resize_3840_2160.png"}
  + ]
  + project.json.current_step = "delivery_complete"
  ```
- **DRY:** Show the recomposition prompt and the three-target
  marketing trio (`1:1`, `16:9`, `9:16`).
- **LIVE:** Resize `Key_Art/Key_Art_001.png` to the marketing trio (1:1, 16:9, 9:16). Three output files land back in `Key_Art/` with `_resize_<W>_<H>` suffixes.

### Step 15 — Close the tour

Show a summary:

```
✓ Tutorial complete.

You toured: /slot-setup, /slot-help, and /slot-step-00 through
/slot-step-10. The sample game "Sun & Moon Sanctuary" {was described /
was generated in <tutorial_project_root>}.

Where to go next:
  - Start a real project:    /slot-step-01 (fresh) or /slot-step-00 (GDD)
  - See the workflow menu:   /slot-help
  - Compare iterations:      /slot-compare
  - Audit an existing set:   /slot-step-08

Project memory persists across Claude restarts and conversation
compaction — restart, switch machines, get compacted, your project
keeps its state. See shared/project_memory.md for the model.
```

If LIVE mode ran, also tell them how to delete the tutorial project
folder if they want a clean slate before starting a real project.

## Pacing

This tour is **17 steps long** (1 setup + 2 utility + 11 numbered
workflow + 1 conclusion + 2 prerequisite checks). At a relaxed pace
that's 20–30 minutes of reading.

**Always pause and ask "ready to continue?" between major phases.**
The natural pause points are:
- After Step 3 (mode decision — DRY vs LIVE)
- After Step 6 (key art — the visual foundation is in place)
- After Step 8 (symbol sheet — the visual identity is decided)
- After Step 12 (audit — production discipline starts to bite)

Don't dump all 17 steps in one wall of text. The tutorial fails if the
user skims and learns nothing.

## What this skill does NOT do

- **Does not replace `/slot-help`.** Help is a one-page menu;
  tutorial is a teaching experience. They serve different needs.
- **Does not modify the user's active project in DRY mode.** Read-only
  inspection of `project.json` is allowed; writes are not.
- **Does not skip safety gates in LIVE mode.** LIVE actually runs each
  step's gate logic — if the brief is incomplete, /slot-step-02 will
  refuse to generate just like in real use. The tutorial respects
  every gate; that's part of what it's teaching.
- **Does not hide cost.** LIVE mode shows the estimated cost before
  every generation call and offers to skip any single step.
- **Does not auto-approve.** Even in LIVE mode, the user explicitly
  approves each iteration before state advances. The tutorial is
  *demonstrating* the approval flow, not bypassing it.

## Hard rules

- **DRY by default.** Never spend API credits without explicit consent.
- **Use the sample brief.** Don't invent a new example every time; the
  *Sun & Moon Sanctuary* brief is the canonical tutorial example so
  outputs are comparable across users.
- **Cite the source SKILL.md.** Every claim in the tour traces to a
  specific section of a real `slot-step-NN/SKILL.md` or shared doc.
  This is a teaching tool — vague summaries that don't reference the
  source are net-negative because they let bugs in the tutorial drift
  the user away from the real contract.
- **Respect the readonly contract in DRY mode.** Reading the user's
  active `project.json` for examples is fine. Writing anywhere is not.
- **Stop and ask between phases.** Don't run all 17 steps end-to-end
  without checking the user is still with you.

## References

- `slot-help/SKILL.md` — the menu this skill complements
- `slot-setup/SKILL.md` — what runs before any of this
- `slot-step-00` through `slot-step-10` — the workflow being taught
- `shared/project_memory.md` — state model the tour explains
- `shared/nb2_prompting.md` — prompt structure the tour cites
- `shared/gpt_image2_prompting.md` — the second model family the tour
  introduces in Step 10 (UI surfaces)
- `slot-compare/SKILL.md` — companion utility for picking between
  iterations; referenced at the close of the tour
