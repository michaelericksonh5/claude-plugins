---
name: webgamedev-structure
description: "Guides GameForge, Game Forge, gameforge, game forge, webdev, webgamedev, //webgamedev, Perforce, P4, p4, sync, syncing, synching, checkout, check out, checking out, check in, checking in, submit, push updates, pushing updates, add assets, asset folders, and dropped folders into artist-safe asset placement and P4 workflow decisions."
---

# webgamedev-structure

Use this skill when a user asks about GameForge asset structure, `//webgamedev/` P4 placement, checkout/submit steps, folder placement, local overrides, `_Common-New`, Spine exports, video animations, UI art, audio, text/data/theme assets, artist-safe P4 workflows, or whether an asset belongs in `ASSETS/GLOBAL`, `ASSETS/LOCAL`, or source `assets`.

GameForge is the system name. Treat `//webgamedev/` as the P4 source of truth and the folder template as canonical. Tiki Titans, Tesla, and older project names are examples only.

## When This Skill Should Jump In

- GameForge, Game Forge, gameforge, game forge, webdev, webgamedev, or `//webgamedev` folder questions.
- Perforce, P4, or p4 workflows: sync, syncing, synching, checkout, check out, checking out, check in, checking in, submit, push updates, pushing updates, reconcile, edit, add, or preview status.
- Add assets, asset folders, dropped folders, final delivery, or plugin handoff questions.
- Audio files, Spine files, png/webp symbols and tiers, UI, text/data/theme JSON, video, or game-specific asset placement.

## First Principles

- Final runtime assets go in `GAMEFORGE_folderstructure/ASSETS`.
- Source and WIP files go in `assets`, not the runtime delivery tree.
- `ASSETS/GLOBAL` maps to `//webgamedev/assets/_Common-New/`.
- `ASSETS/LOCAL` maps to `//webgamedev/<gamefolder>/`.
- `LOCAL` overrides `GLOBAL` only when the relative path under each root is identical.
- If unsure between global and local, choose `LOCAL` and leave a note.
- H5G never-delete policy: write over/update to a new version, but do not automate delete, move, obliterate, clean, or revert operations.
- P4 mutating operations require explicit user approval and `--apply` when using bundled scripts.

## Asset Folder Intake

1. Inventory the dropped folder by type: audio, Spine, png/webp, UI, text/data/theme JSON, video, source files, and unknowns.
2. Ask for the target game folder if it is missing, then separate source/WIP files from runtime-ready files.
3. Map each runtime file to `ASSETS/LOCAL` unless it is intentionally shared in `ASSETS/GLOBAL`.
4. Preview the P4 plan only: status, sync, edit/checkout, add/reconcile, and submit checklist. Treat "push updates" as Perforce submit of a reviewed changelist. Require explicit confirmation before any apply step.

## Reference Docs

- `GAMEFORGE_STRUCTURE.md`: canonical folder and override rules.
- `ASSET_PLACEMENT.md`: where each common art/audio/data asset belongs.
- `ASSET_FOLDER_INTAKE.md`: dropped asset folder inventory, classification, destination mapping, and P4 preview checklist.
- `PERFORCE_CLI_REFERENCE.md`: concise P4 command reference, add/edit reconcile rules, history recovery, and blocked no-delete commands.
- `PERFORCE_ARTIST_WORKFLOWS.md`: safe P4 setup, edit, submit, and history workflows.
- `SAFETY_RULES.md`: preview-first, binary locking, GLOBAL review, and blocked operations.
- `INTEGRATIONS.md`: how this structure should guide adjacent H5G plugins and skills.

When answering placement questions, cite the exact target path and explain whether it is source, runtime `LOCAL`, or runtime `GLOBAL`.
