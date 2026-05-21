# Mobile Slot Art — Core Principles

This is the shared reference cited by every skill in `slot-art-creator`. It is a
condensed extract of the much larger master reference; see the source slot-art
research for full depth. Each skill cites the exact section it depends on.

---

## §1. The ten core principles (the spine)

1. **Mobile-first always.** Design for iPhone-SE-class screens. Standard reel
   format is **3 rows × 5 reels**; reel grid takes **~60–70% of screen height**;
   the **bottom ~30%** stays dark for UI.
2. **Silhouette first.** Identity must survive the solid-black "what is it?"
   test at **64×64–100×100 px**.
3. **Readability > beauty.** Test at **25% of source size**. Detail invisible
   at that scale doesn't belong in the asset.
4. **Value hierarchy by pay tier.** Pay value is signalled by **color
   temperature (warm = high / cool = low)**, **saturation** (higher = more),
   **contrast/detail** (higher = more), and **cell fill %** (higher = more).
   Flat hierarchy = failure.
5. **One focal point per asset.** One subject per symbol, one hero on key art,
   one dominant CTA on UI.
6. **Global light is locked.** Key light **upper-left at ~10 o'clock, ~45°
   elevation**, applied identically to symbols, UI, and background.
7. **The reel is the hero.** Background is a stage; chrome is thin. A
   background that pulls the eye has failed.
8. **Gold is reserved.** Warm gold/amber/saturated reds are reserved for
   **HP symbols, specials, and win FX.** Never on low-pay art — not even trim.
9. **Break the pattern to signal "special."** Wilds and bonuses break the
   set's dominant shape, palette, or complexity so they pop pre-attentively.
10. **Consistency binds the set.** Shared padding, lighting direction, outline
    policy, stroke weight, stylization, color temperature — across every asset.

---

## §3. Symbol design (essentials)

### Pay tiers

Standard set: **3–4 tiers of pay symbols + specials**, **10–14 total**. Canonical
structure: **3 special + 2 HP + 2 MP + 5–6 LP**.

| Tier | Count | Pay (5OAK, ×bet) | Treatment |
|---|---|---|---|
| LP (low-pay) | 5–6 | 0.1× – 2× | Simple, cool/muted, minimum detail |
| MP (mid-pay) | 2–3 | 1× – 10× | Themed objects, moderate richness, warm-leaning |
| HP (high-pay) | 2–3 | 5× – 50× | Characters / iconic objects, warm + saturated, soft inner rim glow |
| Special / Wild / Scatter / Jackpot | 2–4 | mechanic-dependent | Break the set — max weight, unique color |

### LP policy (strict)

Pick **one** LP family; **never mix**:

- Card royals (A, K, Q, J, 10, 9)
- Suits (♠♥♦♣)
- Themed small objects (5–6 uniform items matching the theme)
- Gems (4–5 cool/muted)

**LP discipline:** never use the word `detailed`. Never use `gold`/`amber`/
`warm` on LP — not even trim. Letter/suit reads first; theme is decoration
*behind* the letter.

### Edge definition — primary readability mechanism

At reel-cell size, the subject must read as a clean, confident silhouette
against the dark background. **This is the single most important readability
element.** Without clear edge definition, symbols merge into visual noise at
thumbnail.

Two techniques achieve this. **Pick one per game and stay consistent** —
never mix within a set:

| Technique | Use when | Prompt language |
|---|---|---|
| **Rim lighting / edge glow** | Painterly, semi-realistic, oil, fantasy styles | "warm luminous rim light tracing the silhouette, clear edge separation from background" |
| **Hard outer outline** | Stylized 2D illustrated style | "bold clean outer outline, strong contrast against background" |

Rim lighting is generally more premium — it integrates with the lighting
model naturally. Hard outline is appropriate (and correct) for the stylized
2D style. Both serve the same goal: **unambiguous subject/background
separation at thumbnail size.** Never rely on interior detail for this —
detail is invisible at 64 px. The edge is what reads.

### Mid-frequency texture ban

Three texture families destroy readability at mobile thumbnail size and must
be avoided at every pay tier:

| Forbidden texture | Why |
|---|---|
| Fine scales / fish-scale fill | Becomes gray smear at 25% scale |
| Chainmail / ring-mail mesh | Indistinguishable from noise at 64 px |
| Fine hatching / cross-hatching | Creates halftone banding at reel size |
| Basket-weave / tight wicker | All detail collapses to mid-value mud |
| Dense filigree / micro-ornament | Same as above — adds weight, zero read |

**What to use instead:** bold macro-shapes, broad color planes, **3–5 color
regions max** across the symbol face. Each region must be identifiable at 64 px
by both hue and value difference from its neighbors.

### 3–5 color region rule

Every symbol face (foreground subject + immediate frame) must read as **no
more than 3–5 distinct color regions** at thumbnail size. More than that
collapses into noise.

Count by region, not by named color: a gradient counts as **one** region if
both endpoints share the same hue family and relative value. A warm gold
center + warm orange frame = one region. A warm gold center + dark navy
frame = two regions.

This is a design constraint, not just a QA check. Build with it in mind from
the first prompt draft.

### Silhouette tests (mandatory)

- **Black-fill test** — solid black on white at 64 px. Target **≥85%**
  recognition among peer testers.
- **Thumbnail test** — readable at 64×64 px, ~100 ms flash.
- **Mirror-flip test** — does the symbol still look "right" flipped?
- **Grayscale test** — sheet still differentiates with hue stripped.
- **Adjacent-symbol rule** — any two symbols differ in **≥2 of {hue,
  saturation, value}**.
- **Asymmetry budget** — aim for **40–50% asymmetric** silhouettes in any set.

### §3.5 Cell-fill by tier (use as prompt phrasing)

| Tier | Approx fill | Phrase to use in prompt |
|---|---|---|
| Jackpot | ~95% | "fills entire cell, edge to edge" |
| Wild | ~90% | "large and dominant, small border" |
| Scatter | ~88% | "prominent, fills cell" |
| HP1 / HP2 | 82–85% | "large and prominent" |
| MP1 / MP2 | 72–75% | "generous size, visible padding" |
| LP1–LP3 | 58–65% | "small and understated, generous empty space" |

**Never write raw percentages into an NB2 prompt.** Translate to natural language.

### Wild / Scatter / Bonus

- **Wild** — `WILD` label legible at reel cell size; differs in **category**
  from the base theme (theme is characters → wild is text/object); unique
  electric/emissive color (cyan lightning, hot magenta, neon white).
- **Scatter** — `SCATTER` or `BONUS` label; **circular or badge-shaped**
  (breaks rectangular rhythm); warm luminous treatment.
- **Export BG**: black for glow-heavy / warm subjects; white for cool / LP.

### Set-consistency rules

Across **every** symbol in the set:

- Same key light direction and key-to-fill ratio.
- All hard outlines (2–4 px) **or** all soft with inner rim — never mixed.
- All clean edges **or** all distressed — never mixed.
- One stylization level (no flat-vector LPs with painterly HPs).

---

## §4. Color (essentials)

- Master palette: **12–14** classic, **15–17** standard, **18–20** premium,
  derive beyond that via tint/shade.
- **Saturation budget:** ~80% of screen low-to-moderate, ~20% vivid.
- **Saturation step between tiers:** **≥15–20 percentage points**.
- **L\* gap** between adjacent tiers: **≥20%**.
- **Background:** L\* 5–25, cool-leaning, low saturation.
- **Warm + saturated = forward / premium.** Cool + desaturated = receding /
  low-tier. Single strongest depth cue on a flat reel.
- Author **sRGB**. Never pure `#FFFFFF` body text on OLED (halation).

---

## §5. Lighting (essentials)

- Key light upper-left, **~10 o'clock**, **~45° elevation**.
- **Default key:fill = 3:1** for stylized semi-real slots.
- **Gold metal**: tinted warm specular — **never** white spec on gold (reads
  as plastic).
- **Dielectric** (plastic, ceramic, glass): pure white, tighter highlights.
- **Gem**: 2–3 bold spec points, not 8 micro-facets (noise at thumbnail).
- **Shadows**: never pure black. Match environment temperature.
- **Contact shadow / AO**: 3–8 px under every symbol.

---

## §6. Typography (essentials)

- Workhorse UI: geometric sans, **weight 500–600**, never below 400.
- **Tabular lining figures (`tnum`)** mandatory for any live-updating number.
- **Minimums (mobile):** body 11 px, pay values 14 px, hero numerals 48 px+.
- **Outline rule of thumb:** outline = **5–10% of cap height**.
- **Contrast (WCAG):** 4.5:1 normal text, 3:1 large text and UI chrome.

---

## §7. Surfaces (essentials)

- **Reel grid:** 85–95% of grid region should be symbols. Frame thickness
  @1080p: ornate 40–80 px, moderate 15–40 px, minimal 0–15 px.
- **Background:** stage not hero. Three-layer composition (foreground crop,
  midground story, distant sky) with parallax-ready separation. Vignette
  20–40% darker at corners. ~10–20% brightness drop under the grid.
- **UI / HUD:** transparent panels at 40–70% dark opacity, 1–2 px borders or
  none. Spin button 80–120 pt diameter; 44 pt minimum touch target.
- **Pay table:** **same symbol assets as the reels** (alternate art breaks
  trust). 4–6 symbols per page on portrait.
- **Win presentation:** 3–5 tiers (Small / Medium / Big / Mega / Epic).
  Tiers must differ in **≥2 dimensions** (size, palette, frame, burst,
  intensity). Win amount is the focal point.
- **Lobby tile:** one visual idea at small size. Title/logo 40–60% of tile
  width. Test at lobby thumbnail size in a competitor-grid mockup.

---

## §8. Accessibility & contrast

- **~8% of males** have some CVD. Never rely on hue alone.
- Differentiate with **≥2 of:** hue, saturation, value, shape, size, texture,
  position.
- Prefer CVD-safe pairings: **blue/orange, purple/yellow.**
- WCAG: 4.5:1 normal text; 3:1 large text and UI chrome.
- Test on a cheap **720p LCD** in addition to studio monitors.

---

## §10. QA checklists (condensed)

### Per-symbol

- Silhouette black-fill at 64 px (peer recognition ≥85%).
- Readable at 25% source size.
- Edge definition present (rim light or hard outline per style lock), clearly separates subject from background at 64 px.
- No mid-frequency textures (scales, chainmail, hatching, filigree) — see §3.
- 3–5 color regions max across symbol face — see §3.
- Light direction matches upper-left ~10 o'clock.
- No duplicate silhouettes in the set.
- Edge policy matches the set.
- Fill % matches tier.
- No pure black shadows.
- LP prompts contain no `gold` / `detailed`.

### Per-set

- One style phrase across the whole set.
- One LP family.
- ≥15–20 saturation points between tiers.
- ≥20% lightness gap between adjacent tiers.
- 40–50% asymmetric silhouettes.
- Wild breaks category + color; scatter is circular/badge.

### Per-prompt (NB2)

- Style phrase matches the game's locked phrase.
- Tier stated explicitly.
- Temperature-matched palette in natural language.
- Export BG specified (black or white per export policy).
- Quality tag block appended.
- Semantic negatives ("no X, not even Y") instead of relying on a `negative_prompt` field.
- No raw percentages, pixel counts, hex codes, or codenames.
