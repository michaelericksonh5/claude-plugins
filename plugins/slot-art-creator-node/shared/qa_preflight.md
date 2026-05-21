# QA Preflight — Integrated Generation Protocol

Every design skill (symbol-designer, background-designer, ui-designer,
key-art) follows this two-gate protocol: **validate before generating,
inspect immediately after**. The standalone `/slot-step-08` skill handles
final production sign-off only; this file handles the per-asset loop.

---

## Gate 1: Pre-generation validation

Run these checks **before** calling `nb2_generate`. If any RED fires, stop,
surface the specific problem, and fix the prompt. Do not generate until clean.

### Universal checks (all asset types)

| Check | Pass condition | Fail action |
|---|---|---|
| Brief loaded | `game_brief.json` exists and has `style_lock`, `palette_leads` | Stop. Run `/slot-step-01` or `/slot-step-00` first. |
| `style_lock` in prompt | Prompt contains the exact style phrase from the brief | Add it verbatim. |
| No hex codes | Prompt has no `#RRGGBB` or `rgb(...)` | Replace with named colors. |
| No internal codenames | No project numbers, car names, letter-number pairs used as subjects | Replace with user-facing name. |
| No `negative_prompt` | Not passing a negative_prompt field (NB2 ignores it) | Convert to positive constraints. |
| No resolution strings in prompt body | Prompt has no `"2K"`, `"4K"`, `"1024px"`, `"1080×1920"`, etc. | Strip from prompt — pass via `image_size` API arg only. Default `2K`. |
| No aspect ratio strings in prompt body | Prompt has no `"9:16"`, `"16:9"`, `"1:1"`, `"portrait orientation"`, `"landscape composition"`, etc. | Strip from prompt — pass via `aspect_ratio` API arg only. |
| Aspect ratio valid (API arg) | One of the 14 supported ratios | Correct or default to `1:1` (symbols) / `9:16` (BG). |
| Resolution ≥ 2K (API arg) | `image_size` is `"2K"` or `"4K"` | Bump to `"2K"`. Never generate below 2K. |

### Symbol-specific pre-generation checks

**LP symbols** — all three must be true:
- [ ] Prompt does NOT contain: `gold`, `amber`, `warm`, `detailed`, `ornate`, `rich`, `glowing`
- [ ] Background is `flat solid white background, no gradients`
- [ ] LP family is consistent: if the brief says `card_royals`, subject is a card letter. Never mix families.

**HP symbols:**
- [ ] Background is `flat solid black background, no gradients`
- [ ] Prompt includes a warm-leaning palette from `palette_leads.primary`
- [ ] Size phrase: "large and prominent, more valuable than all mid and low tier symbols"
- [ ] Rim glow allowed and encouraged

**MP symbols:**
- [ ] Background is `flat solid black background, no gradients`
- [ ] Palette is moderate — not as saturated as HP, cooler than HP
- [ ] No glow — "subtle highlight only"
- [ ] Size phrase: "generous size, visible padding, one tier below the high-pay characters"

**Wild:**
- [ ] Subject is a DIFFERENT CATEGORY than the rest of the set (if set = characters → wild is text or object; if set = objects → wild is text)
- [ ] Wild's primary color does NOT appear in `palette_leads.primary` or `.accents`
- [ ] Size phrase: "large and dominant, barely contained fills frame edge to edge"

**Scatter:**
- [ ] Shape is "circular badge" (default) or as specified in brief
- [ ] The word "SCATTER" or the brief's `scatter.label` appears in the subject

### Symbol/environment exclusivity

When generating environmental art (backgrounds, frames/bezels, UI chrome,
banners, lobby tiles), check the symbol manifest before writing the prompt.

**The rule:** Do not proliferate any subject from the symbol set across the
environmental art. A subject that is one of the reel symbols should not
appear as a recurring motif in the BG, frame, or UI.

**Why:** Either failure mode breaks the visual hierarchy:
- **Over-saturation** — the subject is everywhere, so the on-reel symbol
  reads as common environmental decoration rather than a hero asset within
  its tier.
- **Over-empowerment** — the subject defines the entire game world, so
  every other symbol feels subordinate to it, flattening the value
  gradient the player needs to read the reels.

Either way, the symbol loses the "hero of category" identity that drives
pay-tier recognition.

**Concrete checks for environment prompts:**

| Check | Pass condition | Fail action |
|---|---|---|
| BG/frame/UI prompt mentions a symbol subject | Subject appears 0 times, OR appears exactly once as an intentional callback (e.g. a single petal trailing in the foreground) | Strip subject mentions, replace with the theme's broader environmental vocabulary |
| Symbol's defining shape is repeated as decorative motif | Shape used 0 times in env art | Replace with a different theme motif that isn't a reel symbol |
| Frame/bezel pulls thematic motifs | Motifs are from the wider theme vocabulary, not specifically from the symbol manifest | Swap to non-symbol theme elements |

**Example:** A game has a flower as a symbol (HP2). The BG can be the
broader scene (a graveyard at dusk), the frame can have theme-appropriate
ornaments (skull motifs, scrollwork, candles), but the BG/frame should not
be carpeted in that same flower — at most a single subtle callback.

Every game's symbol roster is different. Always read the current brief's
symbol manifest before writing environment prompts and apply this rule
to whatever subjects are in the current set.

### Visual hierarchy awareness

Before generating each symbol, answer these questions internally:

1. **What has already been generated in this set?** If prior symbols exist in
   the output folder, read one HP reference image and one LP reference image
   before building the new prompt.
2. **Where does this symbol sit relative to what's been generated?**
   - HP1 is the warmest, most dominant, highest contrast
   - HP2 is 10–15% less saturated and slightly smaller than HP1
   - MP1 sits visibly below both HPs — cooler, less glow, smaller
   - LP is clearly the coolest, least saturated, simplest
3. **Does the palette for THIS symbol respect that gradient?** If the new
   prompt would make an MP feel as warm as the HP1, pull it back.
4. **Pass reference images to NB2 when they exist.** When generating symbol N
   in a set where symbols 1..N-1 already exist, pass the most relevant prior
   symbol as a visual reference in the `nb2_generate` call. This keeps the
   style consistent without re-specifying every parameter in text.

---

## Gate 2: Post-generation inline check

Run immediately after `nb2_generate` returns — before reporting success to
the user, before moving to the next symbol.

**Read the generated image** using the Read tool. Visually inspect.

### Quick-grade table

Score each item **PASS / FLAG / BLOCK**:

| Check | BLOCK (stop) | FLAG (surface it) |
|---|---|---|
| File exists and opens | No file or 0 bytes | — |
| Silhouette readable at thumbnail | Shape is unrecognizable at small size | Shape is ambiguous |
| Background is correct color | Wrong BG color for the tier | BG has soft gradient instead of flat |
| LP gold contamination | Any LP shows gold, amber, or warm trim | LP feels slightly warm but no explicit gold |
| Tier hierarchy | This symbol's warmth/contrast contradicts its tier vs the rest | This symbol is very close in warmth to the tier above |
| Style match | Style clearly doesn't match `style_lock` | Style is close but feels off |
| Light direction | Multiple light sources | Light from a different angle than prior symbols |
| Wild break | Wild uses same palette as the rest of the set | Wild is slightly similar to HP |
| Export background | Background is not flat/solid | — |

### Always surface the project folder

Every report after every generation MUST include the project folder path so
the user knows where files landed and can click straight to it. The MCP
server's `formatResult` already prints `Folder:` and `Open:` lines, and the
PostToolUse hook surfaces them in the systemMessage. When you summarize back
to the user, always echo the folder path (and the `file:///` URI when on
Windows) so it appears in the chat — don't bury it behind individual file
paths.

Format:

```
Folder : H:\Shared drives\Content Management - AI\Production_AI 2\Asset_Creation_Suite\{GameID}_{username}
Open   : file:///H:/Shared drives/Content Management - AI/Production_AI 2/Asset_Creation_Suite/{GameID}_{username}
```

### Response after inline check

**All PASS:**
> ✓ [Symbol ID] passes inline check. Silhouette clean, tier hierarchy correct,
> background flat [black/white], style consistent.
> Folder: <project_root>
> Moving to next symbol — or say "stop here" to review first.

**One or more FLAG:**
> [Symbol ID] generated. One item to review:
> - [specific flag description]
> Iterate now or continue? (Iterating is cheap here.)

**Any BLOCK:**
> [Symbol ID] needs a fix before we move on:
> - [specific block description]
> Regenerating with: [state exactly what changed in the prompt]

For BLOCK items, **do not ask** — fix and regenerate automatically. Then
re-run the inline check. Max 2 auto-retries; if still blocking after 2, stop
and explain what NB2 seems unable to do.

---

## Between symbols: hierarchy check

After generating each symbol and before starting the next, do a one-line
hierarchy sanity check in your internal reasoning:

> "HP1 is warmest/dominant. HP2 is one step below. MP1 is noticeably cooler.
> The LP I'm about to generate must be visibly the least warm, least
> saturated, most understated symbol in the set. Am I building the prompt
> to reflect that?"

If the answer is no, adjust before generating.

---

## What the standalone `/slot-step-08` skill is for

The per-asset inline check above catches production blockers **per symbol**.
The standalone QA skill is for:

- **Final set review** — reviewing the full contact sheet as a unified set,
  checking tier hierarchy reads correctly across all symbols together.
- **Cross-asset consistency** — does the background work with the symbols?
  Does the UI chrome match the reel art?
- **Client/stakeholder handoff** — producing a structured RED/YELLOW/GREEN
  report with evidence for sign-off.
- **Post-edit QA** — after an NB2 edit or upscale, confirming the change
  didn't break anything.

The inline gate catches blocking problems immediately. QA catches holistic
problems that only appear when you see the full set together.
