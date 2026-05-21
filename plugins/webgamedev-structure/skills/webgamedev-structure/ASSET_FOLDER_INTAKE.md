# Asset Folder Intake

Use this when a user drops an asset folder or asks to add, sync, sync up, check out, check in, push updates, or submit a batch of GameForge assets. In Perforce, "push updates" means submit a reviewed changelist. Do not run P4 commands from this skill; provide preview steps and ask before any apply workflow.

## Intake Workflow

1. Inventory files by type and call out unknowns:
   - Audio: `.wav`, `.ogg`, `.mp3`, `.m4a`.
   - Spine: `.json`, `.skel`, `.atlas`, and texture pages that belong to the same export.
   - Symbols: `.png` and `.webp` for HP, MP, LP, special, scatter, wild, and free games symbols.
   - UI: buttons, panels, overlays, prompts, bottom toolbar, quick access, loading, logo, and feature UI.
   - Text/data/theme: game data, theme JSON, localization, paytable, and config-like files.
   - Video: runtime `.webm` or approved video output, plus source `.mov` or editing project files.
2. Ask for the target game folder if it is not clear from the prompt or folder names.
3. Classify each file as source/WIP or runtime delivery.
4. Map final destinations before proposing P4 activity.
5. Preview P4 status/reconcile add-edit/sync/edit/add and require explicit apply confirmation before mutating anything.
6. Use a submit checklist: target paths reviewed, GLOBAL use justified, binaries locked where needed, changelist description drafted, and user approval captured.

## P4 Batch Plan

Use this order for a dropped folder:

```text
p4 info / p4 login -s / p4 client -o
p4 sync -n //webgamedev/<gamefolder>/...
p4 status //webgamedev/<gamefolder>/...
p4 reconcile -n -a -e //webgamedev/<gamefolder>/...
p4 opened -as <binary targets>
p4 add or p4 edit only after approval
p4 opened
p4 diff -sa
p4 submit -c <change> -d "Description" only after final approval
```

Never use Git language like "push" in the final instructions without translating it to Perforce `submit`.

## Destination Examples

| Input | Runtime destination |
|---|---|
| Feature or symbol audio | `GAMEFORGE_folderstructure/ASSETS/LOCAL/audio/feature` or `audio/symbols` |
| Spine skeleton, atlas, texture pages | `GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/animations/spine` |
| HP/MP/LP symbols | `GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/symbols` |
| Special, scatter, wild, free games symbols | `GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/symbols` |
| UI panels, buttons, prompts | `GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/ui` |
| Theme JSON | `GAMEFORGE_folderstructure/ASSETS/LOCAL/data/themes` |
| Game data JSON | `GAMEFORGE_folderstructure/ASSETS/LOCAL/data` |
| Runtime video | `GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/animations/video` |

Use the matching `ASSETS/GLOBAL` path only for assets intentionally shared across games. Keep PSD, AEP, source MOV, raw audio sessions, and other WIP/source files under source `assets`, not the runtime delivery tree.
