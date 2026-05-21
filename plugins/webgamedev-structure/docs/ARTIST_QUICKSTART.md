# Artist Quickstart

## 1. Confirm P4 Setup

```powershell
p4 set
p4 info
p4 login -s
p4 client -o
```

If `p4 login -s` says you are not logged in, run:

```powershell
p4 login
```

## 2. Preview Sync

```powershell
.\scripts\webgamedev-p4.ps1 sync //webgamedev/<gamefolder>/...
```

Add `--apply` only after reviewing the preview.

## 3. Place Files

Use source `assets` for work files. Use `GAMEFORGE_folderstructure/ASSETS/LOCAL` for final runtime files. Use `GLOBAL` only for shared common assets.

Examples:

```text
GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/symbols/hp1.webp
GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/animations/spine/bonus_intro.json
GAMEFORGE_folderstructure/ASSETS/LOCAL/audio/interface/button_press.opus
GAMEFORGE_folderstructure/ASSETS/LOCAL/data/themes/theme-h5g.json
```

## 4. Checkout, Add, or Reconcile

```powershell
.\scripts\webgamedev-p4.ps1 opened -- -as //webgamedev/<gamefolder>/...
.\scripts\webgamedev-p4.ps1 edit //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp --apply
.\scripts\webgamedev-p4.ps1 add //webgamedev/<gamefolder>/texture/portrait/symbols/hp2.webp --apply
.\scripts\webgamedev-p4.ps1 reconcile //webgamedev/<gamefolder>/...
```

`reconcile` previews as `p4 reconcile -n -a -e` by default. Add `--apply` only when the add/edit preview is correct.

## 5. Submit

Review first:

```powershell
.\scripts\webgamedev-p4.ps1 status
.\scripts\webgamedev-p4.ps1 opened
```

Submit requires a changelist and description:

```powershell
.\scripts\webgamedev-p4.ps1 submit --change 12345 --description "Add GameForge symbol exports" --apply
```
