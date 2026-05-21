# Avatar Template — In-Game Animated Characters

Avatars are the **player-facing animated characters** that live
alongside the reels and react to game state — a mascot dragon that
breathes fire on a big win, a host pharaoh that announces the bonus
round, a cheering villager that reacts to scatter triggers, a sleeping
phoenix that wakes during free spins. They are **not** reel symbols
(they never appear on the grid) and **not** UI chrome (they have
personality and animation, not transparency and chrome). They get their
own discipline.

Some games ship with zero avatars (the reels carry all the visual
energy). Most games ship with 1–2 (a single mascot, sometimes paired
with a sidekick). A few feature-rich games ship with up to 5 (a full
cast — host, mascot, sidekick, villain, mystery character).

## Surface rules

- **Folder:** `Avatars/` (every avatar in one folder)
- **Filename:** `Avatar1_NNN.png` through `Avatar5_NNN.png`
- **Slot in `project.json`:** `assets.avatars.Avatar1` through `Avatar5`
  (only the ones the game uses; unused slots stay at
  `{iterations: [], approved: null}`)
- **Aspect ratio:** `"1:1"` — avatars are rendered in a square frame
  so they fit cleanly into the slot machine's character zone
  regardless of game orientation
- **Background:** **flat solid black, no gradients** (the runtime
  composites the avatar over the game background; a textured
  background here would conflict)
- **Pose:** **neutral idle pose** — front-facing or three-quarter, eyes
  on the viewer, no extreme action. The runtime swaps in animation
  states; this art is the base / idle frame.
- **Character design discipline:** the avatar follows the **same style
  lock and palette family as the symbols and key art**. A photoreal
  avatar in a stylized game looks wrong; a flat-vector avatar in a
  painterly game looks wrong. Match the set.
- **Hierarchy:** avatars rank **below the reels** in visual weight but
  **above UI chrome** — they're characters with presence, not decorative
  borders. Aim for a brightness and saturation level between the HP
  symbols and the bezel.
- **No text on the avatar.** No nameplates, speech bubbles, or labels.
  Those get added at runtime.

## Prompt — single avatar (idle base pose)

Use the master §9.2 bracketed-block structure with the Style Anchor
prepended verbatim, then this body. Substitute placeholders from the
brief and the per-avatar concept note the user provided.

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference key art for rendering technique, surface finish,
and lighting direction (warm key from upper-left, cool fill from
lower-right). <surface-finish phrase from brief — e.g. "smooth
painterly cel shading", "stylized 3D illustration", "bold cartoon">.
Inherit ONLY the rendering technique from the reference — ignore its
background color, palette, and composition. The prompt below is the
single source of truth for those.

[CHARACTER — <avatar_name>, <one-line role: "host" | "mascot" |
"sidekick" | "cheering villager" | "sleeping phoenix" | ...>]
<2–3 sentences: who they are, how they look, how they feel. Anchor
to identifiable features — species, costume, palette, signature
prop. Avoid generic descriptors ("a wise old man") — be specific
("a weathered pharaoh in lapis-lazuli headdress, gold collar, kohl
around the eyes, hands resting on a golden ankh").>

[ANATOMY LOCK]
One head, two eyes, one nose, one mouth, two arms, two hands (five
fingers each unless the species varies). Symmetrical face, eyes
level. <Add any species-specific anatomy: "wings folded along the
back", "four-legged stance", "tail visible behind".>

[POSE]
Neutral idle pose — facing the camera straight on or at a slight
three-quarter angle. Eyes on the viewer. <Hands resting / arms
relaxed / wings folded>. No extreme action — this is the base frame
the runtime animates from. Centered in the frame with a small even
margin of flat black around the character.

[COLOR SYSTEM FOR THIS AVATAR]
Palette draws from <palette_leads.primary> with <palette_leads.accents>
accents. Saturation and warmth sit between the HP symbol tier and the
MP symbol tier — visible but not louder than the reel set. NO carry-
over of the wild's break color (avatars belong to the game's main
palette, not the wild's break palette).

[MOBILE CONSTRAINTS]
Recognizable as a tiny thumbnail in the slot's character zone (~200 px
tall). Clear silhouette. Bold clean shapes — no intricate micro-
textures or dense filigree that collapses at thumbnail size. Centered
composition. Flat solid black background, no gradients, no patterns.

high quality game asset, sharp clean edges, professional slot game art,
character design for mobile slot avatar, clear strong silhouette at
small sizes.
```

## Pre-gen quick checks

- [ ] Style lock matches the locked key art's style phrase exactly
- [ ] Palette draws from `brief.palette_leads`, not the wild's break color
- [ ] Pose is neutral idle (no extreme action)
- [ ] Aspect ratio in API arg is `"1:1"`
- [ ] Background stated as "flat solid black, no gradients"
- [ ] No text or labels described in the prompt
- [ ] Anatomy lock present (count assertions for symmetry)
- [ ] No mention of UI elements (the avatar doesn't share a frame with
      chrome — those are composited at runtime)

## Post-gen quick checks (Gate 2)

**BLOCK** (auto-iterate, max 2 retries):
- Pose is mid-action or asymmetric (not the idle base frame)
- Background isn't flat solid black
- Style clearly doesn't match the locked key art
- Visible text, label, speech bubble, or nameplate
- Asymmetric face / wrong number of features (extra arm, missing eye,
  etc.)
- Character is louder/more saturated than the HP symbols
- Character is photorealistic when the set is stylized (or vice versa)

**FLAG** (surface and ask):
- Character feels off-brand for the theme
- Palette drifts from the brief
- Silhouette is fussy and would lose clarity at thumbnail size
- Personality feels generic — "wise old man" instead of the specific
  archetype the brief named

**PASS:** confirm and offer to continue to the next avatar (or to a
different surface).

## Multiple avatars in one game

When generating a full cast (e.g., the brief calls for 3 avatars —
host, mascot, sidekick), generate them **in order** so each can
reference the previous ones as a style anchor:

1. **Avatar1** (typically the lead — host, hero, primary mascot)
2. **Avatar2** (sidekick / counterpoint)
3. **Avatar3+** (supporting cast)

Pass `Avatar1_001.png` as a reference when generating `Avatar2_001.png`
so the rendering language carries. Pass both as references when
generating `Avatar3_001.png`, and so on. This is the same "build by
gradient" technique used for the symbol tier ladder in `slot-step-03`.

## Cross-cast consistency check

After generating multiple avatars, read them side by side and confirm:

- Same rendering technique across the cast (all stylized 3D, or all
  painterly, never mixed)
- Same key light direction and key-to-fill ratio
- Palette family consistent — each avatar uses a different *accent*
  within the family but the family is shared
- Saturation and warmth all sit in the avatar band (between HP and
  MP intensity) — no single avatar should dominate the others unless
  the brief explicitly names one as the lead

Failures here are auto-FLAG (not auto-BLOCK) because cast consistency
is a set-level judgment the user usually wants to weigh in on.

## When does a game NOT have avatars?

Many slot games ship with zero avatars. Skip this template entirely if:
- The brief's mode list is base + free spins only (no bonus rounds
  with a "host" presenter)
- The theme has no anthropomorphic characters (pure object themes:
  fruit, gems, treasure piles)
- The reel is meant to carry all the visual energy on its own

If unsure, **ask the user** whether the game needs avatars before
generating. Avatars cost real generation time and disk space; don't
manufacture them speculatively.
