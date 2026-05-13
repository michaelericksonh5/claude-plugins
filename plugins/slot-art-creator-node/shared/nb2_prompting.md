# Nano Banana 2 (NB2) Prompting Playbook

NB2 = `gemini-3.1-flash-image-preview`. This is the production prompt
playbook every design skill in `slot-art-creator` follows.

> [!NOTE]
> **There is a second model family available.** When `OPENAI_API_KEY` is
> set, the plugin also exposes `gpt2_generate` and `gpt2_edit` (at 1K or
> 2K) for OpenAI's gpt-image-2 model — which has different strengths
> (accurate text rendering, stable 2K photorealism, multi-image
> compositional editing). For genuine 4K, generate at 2K via gpt-image-2
> then run `nb2_upscale`. See `shared/gpt_image2_prompting.md` for when
> to prefer gpt-image-2 over NB2 (paytables, logos, banners with required
> copy, hero key art with photorealism, multi-reference composition).
> Multi-aspect resize stays on `nb2_smart_resize` — a gpt-image-2-based
> equivalent was prototyped but not shipped (output quality wasn't
> verified against the well-tested fal.ai path). This NB2 playbook covers
> the four `nb2_*` tools only.

## Contents

- **Model basics** — resolutions, aspect ratios, references, chat-mode
  pitfalls, prompt-text vs tool-args rules, no `negative_prompt`
- **§9.2 Master prompt structure** — the bracketed-block format every
  shipped game uses
  - **§9.2.1 Style Anchor** — write once from the brief, prepend to
    every prompt (Gemini's `systemInstruction` equivalent)
  - **§9.2.2 Reference-image discipline** — canonical "inherit ONLY X,
    ignore Y" clause to prevent NB2 from copying reference BG colors
  - **§9.2.3 Bracketed-block templates per symbol type** — HP, MP, LP,
    Wild, Scatter
- **Reel frame / bezel section** — thickness vocabulary, grid-dimension
  rule, ultra-thin/thin templates
- **Background section** — 9:16 skeleton with the four hard rules
- **§9.3 Quality tag block** — reusable
- **§9.4 Style library** — pick one per game and lock it
- **§9.5 Export-background policy** — black vs white per tier
- **§9.6 Edit operations** — in-place, isolate, recreate, style-transfer,
  UI reskin, component separation
- **§9.7 Hard rules** — never in any prompt (forbidden words + anti-pattern gallery)
- **§9.8 Game Concept Brief fields** — what `slot-step-01` locks
- **After every generation call** — show thumbnails, state save location,
  one-sentence visual assessment

---

## Model basics

- **Resolutions:** `"512"`, `"1K"`, `"2K"` (default), `"4K"`. `"0.5K"` is invalid.
- **Aspect ratios:** `"1:1"`, `"3:2"`, `"2:3"`, `"4:3"`, `"3:4"`, `"5:4"`,
  `"4:5"`, `"16:9"`, `"9:16"`, `"21:9"`, `"4:1"`, `"1:4"`, `"8:1"`, `"1:8"`,
  `"auto"`.
- **References:** up to ~10 object refs + ~4 character refs (14 total cap).
  Recommended ~10 for stability. Pass inline image bytes — do not extra-
  base64-encode.
- **Chat mode:** `aspect_ratio` and `image_size` are not supported after the
  first turn. The plugin always makes single-turn calls so dimensions take effect.
- **Prompt text vs tool args:** when `image_size`, `aspect_ratio`, or the output
  file type is supplied by the tool call, do not repeat those values in the
  creative prompt. Put only artistic, functional, and export-background
  instructions in prompt text.
- **Reasoning:** narrative scenes beat keyword lists. State context
  ("mobile slot, tiny thumbnail") explicitly.
- **No `negative_prompt` field.** Express negatives as positive constraints
  ("flat solid black, no gradients"; "no warm gold anywhere, not even trim").

---

## §9.2 Master prompt structure

**Production-tested format.** Every shipped game (4470 Tesla, Gobble Stampede) uses
the same two-piece structure: a once-per-game **Style Anchor** prepended to a
**Body** with explicit `[BRACKETED SECTIONS]`. NB2 reasons better on structured,
labeled prompts than on flat paragraphs — this is the largest single quality
lever in the playbook.

```
<STYLE ANCHOR — built once from the brief, prepended verbatim to every prompt>

[RENDER STYLE — LOCKED to <reference|style_lock>]
…rendering technique, surface finish, lighting direction, what NOT to do…

[<SUBJECT-TYPE SHAPE> — <one-line silhouette family>]
…plaque/frame/badge construction, layered build, size dominance…

[COLOR SYSTEM FOR THIS SYMBOL]
…tier, palette in this slot, dominant interior color, halo/aura treatment…

[SUBJECT INSIDE — <name + role + tier>]
…full subject brief, pose, identity, mood…

[ANATOMY LOCK]   (optional — only when a recurring character appears)
…exact feature list + "one head, two eyes…" count assertions…

[MOBILE CONSTRAINTS]
…thumbnail readability, motif cap, contrast, centered, padding…

<quality tag line>
```

Every `[BRACKETED HEADER]` should be on its own line. The body underneath
can be one paragraph or several short ones. Do not omit headers even when a
section is short — NB2 uses the structural breaks as soft attention anchors.

### §9.2.1 Style Anchor — write once, reuse forever

The Style Anchor is a **single block of game-wide discipline** built from
`game_brief.json` and prepended verbatim to every prompt in the game's run.
It exists so each per-symbol prompt can stay lean while the style/mood/mobile-
readability lock is repeated reliably on every call. (In Gemini terms, this
is the equivalent of `config.systemInstruction`. fal.ai has no equivalent
field — for fal calls, the anchor is just prepended to the prompt body.)

**Build it once when the brief is finalized in `slot-step-01`.** Save the
60–90-word block to `project.json.style_anchor.text` (string field on the
`style_anchor` object — see the field contract in `shared/project_memory.md`).
Reuse verbatim on every subsequent generation.

**Template (fill from brief):**

```
You are generating art assets for a mobile slot machine game ("<game_name>" —
<one-sentence theme summary from brief>). Every output must be optimized for
small phone screens — every element must be recognizable by silhouette alone
when small on a phone. Use bold, clean shapes — no intricate micro-textures,
no dense filigree that collapses at thumbnail size. High contrast between
foreground and the flat background. Warm saturated colors signal high pay;
cool muted colors signal low pay. Gold is reserved for premium and special
symbols only. Maintain a consistent <style_lock> rendering technique across
the entire set.
```

**Rules:**
- Build once per game, reuse verbatim. Do not rewrite per prompt.
- Keep it 60–90 words. Longer dilutes attention.
- Lives in `project.json.style_anchor.text` so every skill can read it.
- Prepend to body with a blank line separator.

### §9.2.2 Reference-image discipline

When a prompt passes a reference image (key art, prior symbol, mood board),
**state explicitly what to inherit and what to ignore**. Without this clause
NB2 will copy the reference's background color and palette into the new
symbol — a real production failure mode that shows up as off-tier colors.

**Canonical clause** (paste at the end of `[RENDER STYLE — LOCKED]`):

```
Inherit ONLY <rendering technique / lighting / surface finish> from the
reference. Ignore its <background color, palette, composition>. The prompt
below is the single source of truth for those.
```

Be explicit about both halves — both *what* to inherit and *what* to ignore.
The vague phrasing "match the style" is not enough.

### §9.2.3 Bracketed-block templates per symbol type

Each template below assumes the Style Anchor (§9.2.1) is prepended verbatim.
`<placeholders>` are filled from `game_brief.json` and the per-symbol manifest.

#### HP (high-pay character or hero object)

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference for rendering technique, surface finish, and lighting
direction (warm key from upper-left, cool fill from lower-right, warm rim
along the upper silhouette). Bold confident forms, no drawn outlines, not
photorealistic. Inherit ONLY the rendering technique from the reference —
ignore its background color and palette, which are specified below.

[PLAQUE SHAPE — <plaque family from brief>]
<plaque construction>: outer metal frame in <palette_leads.primary>; inside
the frame, a clean glossy enamel field (color specified below); thin inner
metal lip separates the enamel from the subject. Large and dominant — the
plaque fills most of the available space with only a small even margin of
flat black around it.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: high-pay premium symbol (HP<N>).
- Enamel field color: <warm-leaning color from palette_leads.primary>.
- Halo / aura treatment: warm-gold halo radiating from the plaque itself,
  not a colored background fill — canvas background stays flat pure black.
- Size phrasing: "large and dominant, commands the frame with a small border".

[SUBJECT INSIDE — <subject from manifest>]
<subject pose, identity, mood — 2–3 sentences>.

[MOBILE CONSTRAINTS]
Recognizable as a tiny thumbnail on a phone. Maximum three to five decorative
motifs on the plaque frame. Bold clean shapes, high contrast between subject,
enamel field, and outer black frame. Centered composition, perfectly upright,
small even margin from canvas edges. Flat solid black background, no
gradients, no patterns.

high quality game asset, sharp clean edges, professional slot game art,
mobile-optimized icon, clear strong silhouette at small sizes.
```

#### MP (mid-pay themed object)

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Same rendering technique as the HP set. <surface-finish phrase from brief>.
Subtle highlight only — no glow, no rim halo. Inherit ONLY rendering
technique from the reference; ignore its background color and palette.

[PLAQUE SHAPE — <plaque family from brief, simpler than HP>]
<plaque construction, one tier less ornate than HP>. Generous size but
visibly one tier below the HP plaques in frame complexity and outer scale.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: mid-pay (MP<N>), one tier below the high-pay characters.
- Palette: moderate warm-leaning <palette_leads.primary> — cooler/less
  saturated than HP, no gold-on-LP carry-down.
- No halo. Subtle highlight only.

[SUBJECT INSIDE — <subject from manifest>]
<subject brief>.

[MOBILE CONSTRAINTS]
Clear silhouette at thumbnail size. Visible padding around the subject.
Centered. Flat solid black background, no gradients.

high quality game asset, professional slot game art, mobile-optimized icon.
```

#### LP (low-pay card royal or low-tier themed object)

```
[RENDER STYLE — LOCKED to <style_lock>]
Flat vector game icon design. Letter shape (or object silhouette) reads
first. No drawn outlines on subject. No painterly modeling. Inherit ONLY
the rendering language from the style lock; do not pull warmth or trim
from any HP reference.

[BADGE SHAPE — minimal]
Generous empty space around the subject. No ornate frame, no plaque, no
metal — a simple flat field at most. The card letter or small themed
object is the entire visual content.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: low-pay (LP<N>).
- Palette: cool muted only — soft cyan, pale silver, dusty blue, soft
  desaturated <theme accent>. NO warm gold, NO amber, NO crimson, NO
  warm trim anywhere, not even as accents.
- Theme decoration: subtle and behind the letter (if card royal).

[SUBJECT INSIDE — <letter|small object>]
<one-line subject>. Small and understated.

[MOBILE CONSTRAINTS]
Clear silhouette at tiny thumbnail size. Flat solid white background, no
gradients. Generous empty space. Sharp clean edges.

professional slot game art. (Do not use the word "detailed".)
```

#### Wild — silhouette break + category break + color break

```
[RENDER STYLE — LOCKED to <style_lock>]
Same rendering technique as the rest of the set.

[BADGE SHAPE — categorically different from the pay symbols]
This wild's outer silhouette must be a DIFFERENT SHAPE FAMILY than every
pay symbol in the set — if the pay symbols use vertical cartouches or
shields, this wild uses a radial sunburst, circular medallion, or hexagonal
emblem. A player glancing at the reel must identify this as the WILD from
peripheral vision alone, based on silhouette shape.

[COLOR SYSTEM FOR THIS SYMBOL]
- Wild's primary color must NOT appear in palette_leads.primary or .accents.
- The wild's palette deliberately BREAKS the game's color story —
  electric cyan / hot magenta / acid green are common choices.

[SUBJECT INSIDE — "WILD" text label]
The word "WILD" is the most readable text at reel cell size. The wild
character or motif (if any) is secondary to the readable WILD text.
Barely contained — fills the frame edge to edge.

[MOBILE CONSTRAINTS]
Centered on flat solid black background, no gradients. Clear silhouette
at thumbnail size. Sharp clean edges.

professional slot game art.
```

#### Scatter

```
[RENDER STYLE — LOCKED to <style_lock>]
Same rendering technique as the rest of the set.

[BADGE SHAPE — circular]
Circular badge-shaped bonus symbol. Radial composition. Warm luminous
glow radiating from the badge.

[COLOR SYSTEM FOR THIS SYMBOL]
- Warm gold-leaning palette — radiant, premium.
- Halo / aura: strong warm-gold radiance, soft sparkle particles.

[SUBJECT INSIDE — "<scatter_label>" badge]
The word "<scatter_label>" (default: "SCATTER") clearly readable.
A premium thematic icon — golden ticket, bonus coin, glowing emblem.

[MOBILE CONSTRAINTS]
Centered on flat solid black background, no gradients. Clear silhouette
at thumbnail size.

high quality game asset, professional slot game art.
```

### Reel frame / bezel

**Thickness vocabulary — use exactly one per prompt. Default: `thin`.**

| Level | Prompt phrase |
|---|---|
| `ultra-thin` | "outer border the same width as the interior divider lines — a razor-thin stone strip" |
| `thin` | "outer frame slightly heavier than the interior lines but still narrow — not ornate" |
| `moderate` | "frame about a third of a symbol cell's height" |
| `ornate` | "thick sculptural frame with dimensional relief elements" |

**The single most important rule:** anchor the outer border weight to the interior
dividers. NB2 over-builds frames when given no anchor. Saying "same weight as the
grid lines" is the strongest constraint available.

**Ultra-thin / thin — no decoration:**

```
A <<cols>>×<<rows>> slot reel frame floating on a flat solid black background,
[outer stone border the same width as the interior grid lines — ultra-thin, razor strip, not a thick frame],
[one-pixel warm gold inner liner separating the stone from the transparent black cell interiors],
<theme_material> stone surface, matte and even, upper-left key light at 10 o'clock,
[no glow, no chromatic aberration, no color fringing on the outer edge],
[<<cols>> columns × <<rows>> rows of transparent black cells, interior dividers matching the outer border width],
no symbols inside the cells, no text, no decorative carving, no embellishment,
flat solid black outer background, professional slot game art.
```

**Thin — with shallow engraved theme motifs (corner and center blocks only):**

```
[Same as above but replace "no decorative carving, no embellishment" with:]
[shallow engraved <theme> motifs on the corner blocks and the center top/bottom/side blocks only —
subtle relief, not painted, not brightly colored, recessive against the stone]
```

**Grid dimension note:** always state `<<cols>>×<<rows>>` explicitly. Leaving
it out causes NB2 to guess — often landing on a 3×3 when you need 5×4.

### Background (9:16 portrait)

```
[Theme scene description], mobile slot game background, 9:16 portrait,
bottom third darkest for UI controls, center reel zone blurred and darkened,
upper-left key light at 10 o'clock, [warm/cool] atmospheric perspective,
no UI, no text, [locked style phrase], not photorealistic.
```

---

## §9.3 Quality tag block (reusable)

```
high quality game asset, sharp clean edges, professional slot game art,
mobile-optimized icon, clear silhouette at small size
```

---

## §9.4 Style library (pick one per game; lock it)

- `bold cartoon game art style`
- `stylized 2D mobile game illustration`
- `flat vector game icon design` (LP-leaning)
- `bold painterly slot game art, slightly stylized` (HP-leaning)
- `cel-shaded game art, bold outlines`
- `stylized semi-realistic slot game art`

Do **not** mix styles within a game. Keep the style phrase identical across
every prompt in the set.

---

## §9.5 Export-background policy

| Subject type | Export background |
|---|---|
| Light / warm / HP / gold subjects | **Black** |
| Dark subjects | **White** |
| Cool / LP / blue subjects | **White** |
| Neon / emissive / glow-heavy | **Black** |
| Default unspecified | **Black** |
| Full environment scenes | Exempt — use scene BG |

Always explicitly say "flat solid [black/white] background, no gradients" to
prevent textured mat generation.

---

## §9.6 Edit operations

- **In-place edit:** "keep everything identical, replace the character's hat
  with a golden crown".
- **Isolate from sheet:** pass sheet as reference, prompt for one element only
  on a clean background.
- **Recreate from ref:** "recreate this symbol in [new style/palette]".
- **Style transfer:** explicitly extract technique, palette, shading, outline
  policy, and lighting from reference, then apply to new subject.
- **UI reskin:** edit operation — **preserve exact layout and positions**,
  resurface only.
- **Component separation** (slot-specific):
  - Extract frame: prompt the frame/border, instruct "remove
    character/symbol, leave empty/transparent center".
  - Extract symbol: prompt the character/symbol, "on clean dark background,
    remove any frame or border elements".
  - Label runs clearly (`label="frame_only"`, `label="symbol_only"`).

---

## §9.7 Hard rules (never in any prompt)

- Raw percentages, pixel counts, or hex codes — translate to natural language.
- Internal GDD codenames — use the user-facing game theme.
- `gold` / `amber` / `warm` on LP symbols.
- `detailed` on LP prompts.
- "Wild that fits the theme" — wilds must **break** the category.
- Photorealism for base reel symbols.
- Same richness across tiers.
- Intricate backgrounds behind reels.
- Mixing LP types (cards + gems + fruit = broken set).
- White, busy reel backgrounds.

### Anti-pattern gallery

- `beautiful ornate golden card A` → LP masquerading as HP; gold forbidden on LP.
- `wild that fits the cute theme` → wild must **break** the theme.
- `intricately carved dragon letter A` → letter shape lost under decoration.
- `detailed painterly cherry LP` → "detailed" forbidden on LP; cherry should
  be flat and small.

---

## §9.8 Game Concept Brief fields

Before any production NB2 prompt is written, the game brief should declare:

- **Mood** — 1–2 words ("mystical serene", "aggressive electric").
- **Theme summary** — ≤2 sentences.
- **Style lock** — single phrase from §9.4.
- **Palette leads** — primary + accent (named colors, not hex).
- **Tier plan** — count per tier + LP family choice.
- **Wild category** — what it is (text label, object, character) and how it
  breaks the theme.

This brief is created once per game and read back into every design prompt.
The `slot-step-01` skill writes it to `game_brief.json` and the master `project.json`.

---

## After every generation call

These three steps apply after **every** `nb2_generate`, `nb2_edit`, or
`nb2_upscale` tool call, regardless of which skill triggered it.

### 1. Show thumbnails inline

Use the `Read` tool on each file path returned by the MCP server.
Claude Code renders image files inline — the user sees the result without
leaving the chat. Read every path, not just the first one.

```
# example — do this for each path in the result
Read("C:/Users/name/Pictures/claude_nb2/image_1.png")
```

### 2. State the save location clearly

Echo the full absolute path once, on its own line:

```
Saved to: C:\Users\name\Pictures\claude_nb2\image_1.png
```

Default output folder is `~/Pictures/claude_nb2` — on Windows this is
`C:\Users\<username>\Pictures\claude_nb2`, visible immediately in File
Explorer under Pictures. Always expand `~` to the full path when reporting.

### 3. One-sentence visual assessment

After showing the thumbnail, give one sentence: does it match the brief?
Call out any obvious mismatch (frame too thick, wrong tier color, grid
dimensions wrong) so the user knows whether to iterate before they look
at it closely themselves.
