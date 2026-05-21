# UI Reskin — Prompt Template

## The 5-part reskin structure

```
Reskin this slot game UI mock with a new theme. Preserve exactly:

- the exact pixel positions and proportions of every button, panel, and label
- the count and arrangement of all controls
- the aspect ratio and overall composition
- the typographic hierarchy (which text is largest, which is smallest)
- the spacing and padding between controls
- any payline indicators, win-line positions, frame thickness
[if reel-frame: reel grid dimensions and divider line positions]
[if paytable: row count and symbol-to-payout alignment]

Surface changes only:
- new theme: <theme_summary>
- new palette: <palette_leads.primary> with <palette_leads.accents> accents
- new material treatment for chrome, panels, and button fills
- new decorative motifs replacing old ones in the same positions
- new icon style for iconographic buttons (spin, autoplay, menu)

Do NOT move any control. Do NOT add any new control. Do NOT remove any
existing control. Do NOT change the relative size of any control.
Do NOT change the typographic hierarchy.

The output is a reskinned version of the source image with the same
layout exactly. Mobile slot UI.
```

**Aspect ratio** is passed as an API parameter, never in the prompt text.
Match the source image's ratio unless the user explicitly wants a reformat.

## Layout-preservation review rubric (8 axes)

| Axis | PASS | FAIL |
|---|---|---|
| Control count | Same number of buttons, panels, labels | New ones added, existing ones gone |
| Control positions | Each control in roughly same x/y | Spin button moved, panel slid |
| Control proportions | About same relative size | Spin huge, steppers tiny |
| Typographic hierarchy | Same text is largest/smallest | Win number now smaller than balance |
| Spacing & padding | Same gaps between controls | Crowding or new gaps |
| Theme application | New palette + decoration uniform | Half-reskinned, half-old |
| Material consistency | Chrome/panel reads as one set | Buttons reskinned, frame still old |
| Decorative motifs | Same positions as old ones | Scattered randomly, old motifs ghosted |

## Diagnose → patch

| Failure | Patch |
|---|---|
| Controls moved | Add: "preserve every control's pixel position relative to the canvas" |
| New controls invented | Add: "Do NOT add any control not visible in source image" |
| Theme half-applied | Restate theme bullet in both preservation AND surface-changes |
| Proportions off | Add: "preserve the exact aspect-ratio of every individual button and panel" |

## When to use reskin vs. designer

| Situation | Skill |
|---|---|
| Approved UI mock to re-theme | **slot-step-07** (this skill) |
| Wireframe with no theme yet | **slot-step-07** |
| Design from scratch | **slot-step-06** |
| Partner's UI to adapt | **slot-step-07** |
| Previous game UI to reuse | **slot-step-07** |

## Hard rules

- Source image is **required**. This skill does nothing without one.
- Single source image only.
- Never change "what the buttons say" — that is copy editing, not reskin.
- Match the original aspect ratio unless the user explicitly wants a reformat.
