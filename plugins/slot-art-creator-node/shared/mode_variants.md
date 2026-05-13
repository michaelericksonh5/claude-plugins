# Mode Variants — Per-Mode Symbol Renderings

Some slot games re-render specific reel symbols when the game enters
a non-base mode (free spins, bonus game, pick-em, wheel). The variant
is **not** a replacement — base-mode and mode-variant assets coexist
in the project, and the runtime swaps between them based on game
state. This doc defines which symbols can have mode variants, how
each tier's variant should differ from base, and how the plugin
generates and stores them.

If your game ships everything in base mode only (no per-mode
re-renders), this doc is informational — `/slot-step-03` defaults to
base mode and you can ignore mode arguments entirely.

---

## The five H5G modes

The modes recognized by the plugin (matches the storage schema in
`shared/project_memory.md` → "modes slot" + `shared/asset_naming.md`):

| Mode token | When it's active | Typical art deltas |
|---|---|---|
| `base` (default) | Normal play, paid spins on the main reels | The canonical rendering. No suffix on filenames. |
| `freespins` | Free-spins bonus round | Glow intensity bump on specials; optional saturation +5-10%; Wild often gets a "free-spins variant" badge or palette shift. |
| `bonus` | Dedicated bonus game (different mechanic, different visuals) | Full repaint allowed for Wild, Scatter, Bonus; specials sometimes get themed accent shifts. |
| `pickme` | Pick-em-style bonus where the player taps tiles | Specials may get a "selectable" treatment — slightly more luminous edge, hover-state-friendly contrast. |
| `wheel` | Bonus wheel sequence (jackpot wheel, multiplier wheel) | Rarely needs symbol variants — wheel art lives in `Wheels/` per `/slot-step-06`. Mode-variant symbols here are unusual; verify against the brief before generating. |

Filename convention: `<symbol_id>_<mode>_NNN.png`. Examples:
- `WD1_freespins_001.png` — free-spins wild variant
- `JP1_bonus_001.png` — bonus-mode jackpot variant
- `SF1_pickme_001.png` — pick-em SF variant

Base-mode files use the bare prefix (no mode token): `WD1_001.png`,
`JP1_001.png`. This stays consistent with `shared/asset_naming.md`.

---

## Per-tier delta rules (the recolor doctrine)

These rules determine which symbols can have mode variants and how
much they're allowed to diverge from base. They exist because
**player familiarity is the single most important UX property of a
slot symbol** — if the LP1 card in free spins looks different from
the LP1 card in base, the player loses the visual handle they were
just trained on.

### LP (low-pay) — never recolor

LP symbols (LP1 through LP6+) must be **identical across all modes**.
Do not generate `LP1_freespins`, `LP1_bonus`, etc. LP is the player's
visual baseline — recoloring it destroys readability and confuses
small-screen recognition.

If the brief explicitly asks for mode-variant LP (rare — usually a
mistake), push back: ask whether the design intent is really to
recolor LP, or if they meant to recolor only the specials. Producing
mode-variant LP is an automatic RED in `/slot-step-08`.

### MP (mid-pay) — never recolor

Same rule as LP. MP1, MP2 stay identical across modes. The same
player-familiarity argument applies.

### HP (high-pay) — glow bump only, no repaint

HP symbols (HP1, HP2, HP3+) can have **glow-intensity variants** in
free spins or bonus modes, but the underlying subject, palette, and
silhouette must stay the same. Allowed deltas:

- Specular highlight intensity +15-25%
- Saturation +5-10% (slightly more vivid)
- Rim light slightly stronger (the "lit from behind" feel)
- An optional "free-spins glow" particle motif around the figure

NOT allowed:
- Repaint to a different color family
- Different pose, expression, or subject orientation
- Background change (still flat solid black)
- Subject swap (HP1 stays HP1 — not a transformation)

Use `nb2_edit` (NOT `nb2_generate`) for HP mode variants. The base-
mode approved HP1 goes in as the `source`, and the prompt instructs
NB2 to apply the glow delta while preserving everything else. This
is "tier-discipline shifts" in the routing decision tree below.

### Wild — glow bump in free spins; full repaint allowed in bonus

Wild can diverge more than HP because wild is allowed to be the most
visually exciting symbol. In free spins, treat it like HP — glow
bump via `nb2_edit`. In bonus mode (a different game mode entirely),
a full repaint via `nb2_generate` is acceptable if the brief calls
for it (e.g. "the bonus-mode wild is a phoenix flame instead of a
phoenix"). Use `nb2_generate` for full repaints, `nb2_edit` for
glow bumps.

### Scatter and Bonus trigger — palette shift in bonus mode, not free spins

`SC`, `BO`, and `WY*`-as-scatter symbols sometimes get a palette
shift when the bonus role activates differently in the bonus mode.
Free-spins variants of these are rare — the scatter usually doesn't
appear during free spins (it's the trigger to enter them). If the
brief calls for one, use `nb2_edit` with a glow/palette shift only.

### Jackpot tiles (JP1-JP6) — typically static across modes

Jackpot tile renderings are the most static across modes. The
metallic medallion look is a "premium" signal that should remain
recognizable wherever it appears. Don't generate mode variants
unless the brief explicitly designs the jackpot to look different
per mode (very rare — usually a sign of bonus-mode jackpot tier
mapping changes, not visual changes).

### WYS family (`WY`, `WYS`, `BWY`, `SFWY`) — case-by-case

The WYS family contains both LP-equivalent symbols (e.g. WYSIWYG
collectors that pay like specials) and HP-equivalent symbols (e.g.
`HP-equivalent payout` role). Apply the rule that matches the WYS
member's role per `brief.symbol_manifest[].mechanic`:

- WYS role acting as LP-equivalent (collector, scatter trigger,
  bonus trigger) → never recolor (same as LP)
- WYS role acting as HP-equivalent (hold-and-spin coin paying as
  HP) → glow bump only (same as HP)
- WYS role acting as Wild (`bonus trigger + coin payout` etc.) →
  glow bump in free spins, repaint allowed in bonus (same as Wild)

When in doubt, default to "no recolor". Overproducing mode variants
is more expensive (in time AND in player confusion) than producing
none.

### SF family (`SF`, `SFWY`, `WDSF`) — case-by-case, same as WYS

Same logic: apply the rule for the SF member's role from the brief's
`mechanic` field. Most SF roles act like specials → glow bump only.
A `bonus-game trigger` SF role behaves like Bonus trigger → palette
shift in bonus mode, not free spins. A `mystery transform` SF role
stays static across modes (the transform happens at runtime, not as
a separate render).

### Compound prefixes (BWY, WJP, WDWY, WDSF, MUWD, MUWDBO)

Apply the rule of the **dominant** family per
`shared/symbol_vocabulary.md`. E.g. `BWY` (WYS-dominant + bonus
overlay) follows the WYS rule. `WJP` (Wild-dominant) follows the
Wild rule. `WDSF` (Wild-dominant) follows Wild.

---

## Recolor budget — per-game upper limit

Across an entire game, **at most 3-4 symbols should have mode
variants**. Most games ship 0-2 mode variants total. Recoloring
more than 4 symbols across modes:

- Inflates production cost without proportional UX gain
- Confuses players who are still learning the symbol set
- Makes the QA matrix combinatorially harder

Typical patterns from the H5G catalog (per `shared/symbol_vocabulary.md`):

| Game pattern | Mode variants typically generated |
|---|---|
| Free-spins-only game (no bonus mode) | 0-1 variants (sometimes the Wild gets a free-spins glow) |
| Free-spins + bonus mode | 1-3 variants (Wild + maybe HP1 in free spins; bonus-mode Wild full repaint) |
| Loot Link / Hotspot game | 2-4 variants (the SF/WYS feature tokens may get a "feature-active" treatment) |
| Pachinko / Drop Zone | 0 variants (pachinko pieces are mechanically distinct, not mode-variant) |
| Wheel-feature game | 0-1 variants (the wheel's slice graphics live separately in `Wheels/` — they're not "symbol mode variants") |

`/slot-step-08` recolor-budget grading:
- 0-3 mode-variant symbols → GREEN
- 4 mode-variant symbols → GREEN (cap reached but defensible)
- 5 mode-variant symbols → **YELLOW** (over recommended budget; designer should justify in the brief)
- 6+ mode-variant symbols → **RED** (clearly over budget — recolor sprawl will confuse players and inflate production)

Plus an unconditional **RED** for any LP or MP slot with a non-null
`modes` block — LP/MP should never have mode variants, regardless of
the total count.

---

## Routing decision tree — `nb2_edit` vs `nb2_generate`

When `/slot-step-03 mode:<x>` runs, the skill chooses the MCP tool
based on the type of delta requested:

```
Is the mode variant a TIER-DISCIPLINE shift?
  (glow bump, saturation shift, rim light delta — silhouette and
  subject identical to base)
    ↓ yes
  nb2_edit with source = base-mode approved asset
  parent_path in the iteration record = base-mode approved path

Is the mode variant a FULL REPAINT?
  (different palette family, different subject treatment, different
  pose — i.e. base mode's HP1 phoenix vs bonus mode's HP1 phoenix-on-fire)
    ↓ yes
  nb2_generate with references = [base-mode approved asset, key art]
  parent_path in the iteration record = null (fresh generate)
```

The skill defaults to `nb2_edit` for tier-discipline shifts because:

- Faster (one MCP call, no recompose)
- Cheaper (edit is typically cheaper than generate)
- Preserves silhouette and composition exactly (the player's visual
  memory of base mode's HP1 stays intact)

The skill switches to `nb2_generate` when:

- The user explicitly asks for "a different palette" / "a full
  bonus-mode redesign" / similar repaint language
- The brief defines mode-variant subject changes (e.g. base wild =
  phoenix, bonus wild = phoenix-on-fire)

When in doubt, ask the user before generating: "Did you want a
glow/palette tweak on the existing wild, or a full repaint? The
first is a 30-second edit; the second is a fresh generate that
takes 2-3 retries to lock."

---

## Storage in `project.json`

Mode variants live in the per-symbol `modes` slot — see
`shared/project_memory.md` → "modes slot for mode-variant assets"
for the full schema. Brief reminder of the shape:

```json
"WD1": {
  "iterations": [ ... base-mode iteration records ... ],
  "approved": "Symbol_Art/WD1_002.png",
  "upscaled": null,
  "resized": [],
  "metrics_summary": null,
  "modes": {
    "freespins": {
      "iterations": [ ... freespins iteration records ... ],
      "approved": "Symbol_Art/WD1_freespins_001.png",
      "upscaled": null,
      "resized": [],
      "metrics_summary": null
    },
    "bonus": null,
    "pickme": null,
    "wheel": null
  }
}
```

The top-level `iterations` / `approved` always represents base mode.
Each `modes.<mode>` sub-record follows the same asset-record shape
recursively (it can have its own `upscaled`, `resized`, `metrics_summary`).
Mode variants are never nested deeper than one level — there's no
`modes.freespins.modes` (a free-spins variant doesn't have its own
mode variants).

---

## `/slot-step-08` per-mode checks

When the audit scope includes symbols with populated `modes`,
`/slot-step-08` applies these additional checks beyond the standard
per-symbol rubric:

| Check | RED | YELLOW | GREEN |
|---|---|---|---|
| LP/MP mode variant exists | Any `assets.symbols.LP*.modes` or `MP*.modes` is non-null | (n/a — binary) | LP/MP `modes` are all null |
| Recolor budget | More than 4 symbols across the game have populated `modes` | 4 symbols have modes (cap reached) | ≤3 symbols have modes |
| Base/mode silhouette match (tier-discipline shifts) | Mode variant's `bounding_box` differs from base by >20% in either dimension | 10-20% difference | <10% (silhouette preserved) |
| Base/mode palette family (tier-discipline shifts) | Mode variant's dominant `h` differs from base by >60° (palette family changed when only a glow bump was requested) | 30-60° drift | <30° (palette family preserved) |
| Mode variant has lineage | `iterations[0].parent_path` is null for an `nb2_edit`-based mode variant | (n/a — should be deterministic) | `parent_path` set to base-mode approved asset |

The silhouette and palette-family checks use the metrics already
captured by `/slot-step-08` Step 3.5 — no extra measurement needed.

---

## When to ignore this doc

- Game has no mode variants (the common case — base mode is all)
- Game is a pachinko / Drop Zone variant (mode-variant symbols don't
  apply to game-piece-style art)
- Designer is iterating on base-mode art and hasn't started thinking
  about modes yet — finish base first, then come back here

This doc only loads when someone asks `/slot-step-03 mode:<x>` or
when the brief's `symbol_manifest` includes per-symbol `modes` field
hints. Otherwise it's purely informational and doesn't affect the
default workflow.
