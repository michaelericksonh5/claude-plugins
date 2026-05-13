# Game Logo Templates

Every game needs **three logo lockups**: hero (full premium), standard
(smooth gradients, fewer flourishes), and compact (flat or near-flat,
readable at 40 px). Generate all three when asked for "the logo."

## Model choice — strongly prefer gpt-image-2 if available

Logos are **wordmark-driven**, and getting the spelling exactly right
matters. NB2 frequently misspells or scrambles letterforms in stylized
fonts — a real production failure mode. **gpt-image-2 (`gpt2_generate`)
renders wordmarks substantially more reliably** and is the preferred
tool when `OPENAI_API_KEY` is configured.

Recipe:
1. If `OPENAI_API_KEY` is set: use `gpt2_generate` with the game's
   wordmark in quotes and a clear style description.
2. If only NB2 keys are set: use `nb2_generate` but be ready to
   regenerate — expect 2-4 attempts to get the wordmark right, and
   verify every letter at the post-gen QA gate.

For the hero lockup specifically (the marketing one), `gpt2_generate`
at `quality: high` and `image_size: "2K"` is the sweet spot. gpt-image-2's
4K targets are experimental and unreliable for production — if you need
4K marketing output, generate at 2K with gpt2 and then run `nb2_upscale`
on the approved result.

See `shared/gpt_image2_prompting.md` for full gpt2 guidance.

## Surface rules (all lockups)

- **Background:** flat solid black, no gradients
- **Bevel highlights:** from upper-left
- **No other text** in the image — just the wordmark
- **No icons** flanking the wordmark unless explicitly themed (decorative motifs are OK; standalone icons are not)

## Hero lockup — full premium

The marketing/key-art version. Full effect stack, decorative motifs.

```
The game title "<game_name>" as a slot game logo — hero lockup,
full premium treatment: gold gradient fill, dark brown outline,
secondary thin inner outline, bevel highlight from upper-left,
drop shadow, outer glow,
<theme_summary> themed decorative motifs flanking the wordmark,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art, no other text or icons.
```

### Hero quick checks

- [ ] Effect stack: gold gradient → dark outline → inner outline → bevel → drop shadow → outer glow
- [ ] Decorative motifs flank the wordmark (theme-relevant)
- [ ] Background is flat solid black

---

## Standard lockup

The in-game / lobby version. Smoother, less ornate.

```
[Same as hero but replace treatment with:]
smooth gold gradients with one outline and subtle bevel — fewer flourishes
than the hero lockup but still premium.
```

### Standard quick checks

- [ ] Reads as "the same logo, simpler version" — same wordmark, same palette family
- [ ] Fewer effects than hero (one outline instead of two, lighter glow, simpler bevel)
- [ ] No decorative motifs (or much smaller than hero)

---

## Compact lockup

The icon / footer version. Must be readable at 40 px height.

```
[Same as hero but replace treatment with:]
flat or near-flat treatment with one clean outline,
readable at 40 px height, no glow or drop shadow.
```

### Compact quick checks

- [ ] Flat or near-flat — minimal layering
- [ ] One clean outline only
- [ ] No glow, no drop shadow
- [ ] Mentally shrink to 40 px tall — still readable?

---

## Generating the trio

When asked for "the logo," generate all three lockups in this order:
hero → standard → compact. Pass each prior lockup as a reference image so
the wordmark, palette, and motif system stay consistent. Save as
`Logo_hero_NNN.png`, `Logo_standard_NNN.png`, `Logo_compact_NNN.png`.

## Cross-lockup consistency check

After generating all three, read them side by side and confirm:
- Same wordmark letterforms across all three
- Same palette family
- Visible reduction in complexity from hero → standard → compact
- All three remain identifiable as the same brand
