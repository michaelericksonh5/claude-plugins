# Lobby Tile Template

The lobby tile is the thumbnail in a grid of competing games. It must
communicate the game in **one visual idea** at small size. The title
wordmark is part of the tile.

## Surface rules

- **One visual idea.** No ensemble. The hero theme element + the title.
- **Hero element:** center-frame, the most recognizable thing about the game
- **Title:** prominent, occupies roughly the center band, 40–60% of tile width
- **Aspect ratio:** typically `1:1` square or `4:3`, passed via API arg
- **Silhouette:** must survive a 5-pixel blur test (be still recognizable when blurred)

## Prompt — lobby tile

```
A lobby tile thumbnail for the slot game "<game_name>", <style_lock>,
one strong visual idea readable at small size,
hero theme element center-frame,
title wordmark "<game_name>" prominent across roughly the center band,
<palette_leads.primary> palette,
strong silhouette that survives a 5-pixel blur test.
```

## Pre-gen quick checks

- [ ] One single hero element (not an ensemble)
- [ ] Title wordmark text included verbatim
- [ ] "Strong silhouette" / "5-pixel blur test" language present
- [ ] Palette pulled from `brief.palette_leads.primary`

## Post-gen quick checks

- [ ] Recognizable at small size (mentally shrink to 200×200 px)
- [ ] Title wordmark is readable
- [ ] One clear focal point — eyes don't wander
- [ ] Silhouette test: blur the image mentally; can you still tell what game this is?
- [ ] Title doesn't fight the hero element for attention (one is dominant, the other supports)

## Variations

Some lobbies need both `1:1` (grid tile) and `4:3` (featured tile) versions.
Generate the `1:1` first, then use it as a reference image when generating
the `4:3` variant — pass it via the API's `references` arg, not in
the prompt body. Save as `Tile_NNN.png` and `Tile_4x3_NNN.png`.

## Competitor-grid mockup discipline — required before sign-off

A lobby tile is never reviewed in isolation. The player sees it in a grid
of 12–20 competing games on the same screen. A tile that looks gorgeous
alone may disappear or look generic when surrounded by competitor art. The
rule: **never approve a lobby tile without comparing it inside a
competitor-grid mockup.**

### How to do the mockup

1. **Collect 11–19 competitor tiles** from existing games in the same
   genre (the slot lobby it'll ship to). H5G has internal references;
   external users can pull from public slot-aggregator screenshots.
2. **Composite into a 3×4 or 4×5 grid** with the new tile in any
   position (avoid putting it dead-center — that's not where a player's
   eyes land first).
3. **Review at lobby thumbnail size** (~200×200 px per tile). Squint
   at the grid. Three questions:
   - Does the new tile **draw the eye** within 500 ms? (F-pattern or
     Z-pattern scan should hit it.)
   - Does it look **categorically different** from neighbors, or does
     it blend? Blending kills tap-through rate.
   - Is the title wordmark **readable** at thumbnail size, or has it
     turned to mud?

### Target metric

A successful tile lifts **tap-through rate by 5–10%** vs the previous
tile or vs an A/B control. That's the production benchmark. Aesthetic
preference is secondary; if your favorite tile loses an A/B against
something uglier, the data wins.

### Common failure modes (red flags caught at this stage)

- **Dark tile on dark lobby BG** — the tile silhouette disappears.
  Fix by adding a thin contrasting edge or shifting BG palette warmer.
- **Mismatched tile art vs in-game** — the player taps expecting one
  thing, gets another, and the game's perceived quality drops.
  Erodes lifetime value. Solution: the tile's hero element must be
  the same character/object that's in the actual gameplay (usually
  HP1 or the wild).
- **Title wordmark turns to noise at 200 px** — re-author the wordmark
  with bolder strokes or higher contrast.

This check is a **slot-step-08 Gate 2** item — the cross-asset audit
should never sign off GREEN on a lobby tile that hasn't been seen in a
competitor-grid mockup.
