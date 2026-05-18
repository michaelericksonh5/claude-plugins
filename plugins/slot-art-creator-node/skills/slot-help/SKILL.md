---
name: slot-help
description: >-
  Welcome / orientation for the slot-art-creator-node plugin. Shows the 15 commands at a glance — the 11-step numbered workflow (`/slot-step-00` through `/slot-step-10`) plus the four non-numbered utilities (`/slot-setup` for API-key configuration, `/slot-help` for orientation, `/slot-tutorial` for a guided end-to-end walkthrough, `/slot-compare` for readonly side-by-side review). Routes users to the right starting point based on their situation: `/slot-setup` for first-time installs without keys, `/slot-tutorial` for new users who want a guided tour with a worked example, `/slot-step-00` if they have a GDD on Drive, `/slot-step-01` for fresh concepts without a GDD. Use this whenever a user asks "where do I start?", "what does this plugin do?", "how does this work?", "what's the workflow?", "what commands are available?", "show me what's available", "help", "I need help", "I'm lost", "list the slot commands", "what can this plugin do", "show me the menu", "what's next?", or types `/slot` without a specific step number. Also use it when a user seems confused about which step to run next mid-workflow. Prefer `/slot-tutorial` over this skill when the user wants a teaching experience with a worked example rather than a one-page command menu.
---

# Welcome — slot-art-creator-node

This is the orientation skill. Use it to bring a new (or returning) user
up to speed on how the plugin works in under 60 seconds, then route them
to the right next step.

## Workflow

### Step 1 — Check setup state

Before showing the workflow, confirm the user has API keys set. Read
`~/.h5g-slot-art-creator/.env` (Windows: `%USERPROFILE%\.h5g-slot-art-creator\.env`).

- **If neither `GEMINI_API_KEY` nor `FAL_KEY` is set:**
  Skip the workflow tour and route them to `/slot-setup` first — without
  keys, nothing else works.

- **If at least one key is set:** continue to Step 2.

(For Cowork users, the `.env` file may not be the source of truth — keys
can live in the plugin's env-var UI. If the `.env` isn't there or is
empty but they're on Cowork, just continue to Step 2 and trust they've
configured the UI; first generation call would surface a missing-key
error if not.)

### Step 2 — Show the workflow

Present this welcome message:

```
slot-art-creator-node — High 5 Games slot art pipeline

The workflow is 11 numbered steps. Run them in order, or jump around as
needed — each one knows what state the project should be in and will
tell you if you've skipped a prerequisite.

  /slot-setup       First-time API key configuration (run once)
  /slot-help        This orientation (you can always come back here)
  /slot-tutorial    Guided end-to-end tour using a worked example
                    (DRY by default — costs nothing; opt into LIVE if you
                    want it to actually generate the sample game)
  /slot-compare     Side-by-side review of iterations, asset sets, or
                    two projects — readonly, helps you pick a winner

  /slot-step-00     Pull a Game Design Document from Drive (optional — skip if pitching fresh)
  /slot-step-01     Lock the game brief: theme, palette, style, tier plan, symbol manifest
  /slot-step-02     Generate master key art — becomes the visual style anchor
  /slot-step-03     Generate individual reel symbols — HP, MP, LP, Wild, Scatter,
                    Bonus, Jackpot, Blocker, WYS family (coins / portals), SF family
                    (feature tokens), Loot Link, pay-multiplier variants, pachinko
                    pieces, and compound prefixes (BWY, WJP, WDWY, SFWY, ...).
                    JP tier ordering is per-game — read brief.jackpot_tier_names.
  /slot-step-04     Full symbol contact sheet (IDEATION before /slot-step-03 or ASSEMBLE after)
  /slot-step-05     Background scenes — base, free-spins, bonus, pick-me, wheel
  /slot-step-06     UI surfaces + bonus wheels + in-game avatars — bezel, HUD, paytable,
                    banners, buttons, lobby tile, logo; full bonus-wheel graphics for
                    jackpot / bonus / multiplier / pick-em modes; plus animated character
                    avatars (0–5 per game)
  /slot-step-07     UI reskin (optional — adapt an existing layout to a new theme)
  /slot-step-08     Final cross-asset audit — RED/YELLOW/GREEN sign-off report
  /slot-step-09     Upscale approved 2K assets to 4K for production
  /slot-step-10     Multi-aspect variants of an approved asset (1:1, 16:9, 9:16, etc.)

Where to start:
  - First time on this plugin?  Run /slot-setup (keys), then /slot-tutorial for a guided tour.
  - Have a GDD already?         Run /slot-step-00 to seed the project from it.
  - Pitching a fresh concept?   Run /slot-step-01 to lock the brief.
  - Multiple iterations to      Run /slot-compare — readonly side-by-side
    pick between?               with rubric-grounded scoring.
  - Want to use a chat-pasted   The MCP server has nb2_stage_image — I'll
    image as a reference?       handle that automatically when needed.

Project memory persists across sessions and conversation compaction —
restart Claude, switch machines, get compacted, and your project picks
up where you left off (see shared/project_memory.md).
```

### Step 3 — Read the situation and route

After showing the welcome, ask the user where they're starting from:

- "Are you brand new to this plugin and want a guided tour first?
  → run `/slot-tutorial` for an end-to-end walkthrough with a worked
  example (DRY by default; no API credits unless you opt in)."
- "Do you have a Game Design Document for an existing game, or are you
  pitching a fresh concept?"
- "Or did you want to see what one of the steps does in more detail?"

Based on their answer, suggest the right next slash command. Don't run
it for them — let them invoke it themselves so they learn the workflow.

## When NOT to use this skill

- If the user is already mid-workflow and asks a substantive question
  about the current step, answer the question directly. Don't dump the
  full workflow tour on them.
- If they ask "what does /slot-step-03 do specifically", that's a
  documentation question, not an orientation request. Read the actual
  step's SKILL.md frontmatter and summarize.
- If they're already past Step 2 (project exists, has approved assets),
  this skill's primary value diminishes. Show a shorter "where you are
  in the workflow" version: read `project.json.current_step` and
  `project.json.next_step` and surface those.

## What this skill does NOT do

- It doesn't modify any state. Pure orientation.
- It doesn't generate art, run validation, or call MCP tools (other than
  reading the .env file for the setup check).
- It doesn't replace `/slot-setup` — those are distinct concerns
  (keys vs. workflow knowledge).

## References

- `shared/project_memory.md` — state model, startup protocol
- `shared/nb2_prompting.md` — prompt playbook (referenced by every step)
- `shared/qa_preflight.md` — the per-asset and cross-asset QA model
- Each `slot-step-NN/SKILL.md` — detailed per-step instructions
