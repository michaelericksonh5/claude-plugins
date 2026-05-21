# HP — High-Pay Symbol Templates

HP symbols are the warmest, richest, most dominant tier. They establish the
top of the value gradient. Usually 2 per set (HP1, HP2). HP1 is the
warmest/most saturated; HP2 is one notch below HP1.

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1) is
prepended to every prompt verbatim — it lives in `project.json.style_anchor.text`.

## Tier rules

- **Background:** flat solid black, no gradients
- **Palette:** warm end of `palette_leads.primary` + rim glow allowed
- **Light:** upper-left key light at 10 o'clock + soft inner rim glow
- **Size phrase:** "large and prominent, more valuable than all mid and low tier symbols"
- **Tier hierarchy:** HP1 sets the high water mark; HP2 is 10–15% less saturated and slightly smaller than HP1
- **Anatomy lock** (when HP is a recurring character): include the explicit
  feature-list + count assertions to prevent identity drift across regens.
  See `[ANATOMY LOCK]` block below.

## Prompt — HP character

Use when the HP subject is a character, person, deity, animal, etc.

```
[RENDER STYLE — LOCKED to attached key art reference]
Match the reference for rendering technique, surface finish, and lighting
direction (warm key from upper-left, cool fill from lower-right, warm rim
along the upper silhouette). Bold confident forms, clean shape separation,
not photorealistic. Inherit ONLY the rendering technique from the reference —
ignore its background color and palette, which are specified below.

[PLAQUE SHAPE — ornate vertical cartouche]
An ornate vertical CARTOUCHE plaque centered on flat solid black background,
no gradients, no patterns. Layered construction: outer metal frame in cast
polished warm gold from <palette_leads.primary> with sculpted <theme>
filigree (small thematic motifs at the corners and center blocks only,
3–5 motifs maximum); inside the frame, a clean glossy enamel field (color
specified below); thin inner metal lip separates the enamel from the
subject. Large and dominant — the plaque fills most of the available
space with a small even margin of flat black around it.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: high-pay premium symbol (HP<N>).
- Enamel field color: <warm color from palette_leads.primary> — the
  dominant color of the plaque interior.
- Halo / aura: warm-gold halo radiating from the plaque itself, with a
  few gold sparkle particles drifting nearby. Halo is light radiating
  FROM the plaque — the canvas background stays flat pure black.
- Size phrasing: "large and dominant, commands the frame with a small border".

[SUBJECT INSIDE — <subject from manifest>]
<2–3 sentence subject description: pose, identity, mood, what makes it
the hero of its tier>.

[ANATOMY LOCK]   (only when the HP is a recurring character)
The <character> matches the attached reference EXACTLY: <explicit feature
list — colors, body parts, costume>. <Count assertion: "one head, one
beak, two eyes, one wattle, two wings, two legs, two feet" — whatever
the character's anatomy is>. Clean silhouette with no deformities.
Expression: <signature mood — never goofy, never scary, never
overdramatic>.

[MOBILE CONSTRAINTS]
Recognizable as a tiny thumbnail on a phone — overall silhouette and
subject must read instantly at a glance. Maximum three to five decorative
motifs on the plaque frame; more becomes visual noise at reel scale.
Bold clean shapes with high contrast between subject, enamel field, and
outer black frame. Centered composition, perfectly upright, no tilt,
small even margin from canvas edges. Flat solid black background, no
gradients, no patterns.

high quality game asset, sharp clean edges, professional slot game art,
mobile-optimized icon, clear strong silhouette at small sizes.
```

## Prompt — HP iconic object

Use when the HP subject is a hero object (a sword, a treasure chest, a
totem) rather than a character. Drop the `[ANATOMY LOCK]` block.

```
[RENDER STYLE — LOCKED to attached key art reference]
Match the reference for rendering technique, surface finish, and lighting.
Inherit ONLY the rendering technique — ignore the reference's background
color and palette, specified below.

[PLAQUE SHAPE — <plaque family from brief>]
<plaque construction, fills most of the cell with small border>.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: high-pay (HP<N>).
- Palette: warm <palette_leads.primary> with metallic highlights and
  inner rim glow.
- Halo radiating from the plaque, not the background.

[SUBJECT INSIDE — <hero object>]
<object brief — material, surface, what makes it the tier's hero>.

[MOBILE CONSTRAINTS]
Clear silhouette at tiny thumbnail size. Centered. Flat solid black
background, no gradients.

high quality game asset, sharp clean edges, professional slot game art,
mobile-optimized icon.
```

## Pre-gen quick checks

- [ ] `style_anchor.text` (from `project.json.style_anchor.text`) is prepended to the prompt verbatim
- [ ] `[RENDER STYLE — LOCKED]` block present with explicit "Inherit ONLY X, ignore Y" clause
- [ ] Background is `flat solid black background, no gradients`
- [ ] Warm palette pulled from `palette_leads.primary`
- [ ] Rim glow allowed and encouraged
- [ ] If this is HP2: prompt notes it's "one notch below HP1" + slightly less saturated
- [ ] If subject is a recurring character: `[ANATOMY LOCK]` block included with explicit feature list + count assertions
- [ ] Subject is the manifest's `subject` field, not the internal ID
- [ ] Decorative motifs capped at 3–5 (otherwise turns to noise at reel scale)

## Post-gen quick checks

- [ ] Silhouette readable at thumbnail size
- [ ] Background is flat black (no gradient bleed from reference)
- [ ] Warmer/more saturated than the MP and LP tiers in the set
- [ ] Light direction matches prior HP if one exists in the set
- [ ] If recurring character: anatomy matches reference exactly (correct number of features, correct colors)
