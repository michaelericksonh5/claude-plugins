# GameForge Structure

This is the distilled GameForge folder canon for `//webgamedev/` assets.

## Golden Rules

1. Final runtime assets belong in `GAMEFORGE_folderstructure/ASSETS`.
2. Source, WIP, references, PSDs, AE projects, Maya scenes, WAV masters, MOV masters, and review exports belong under `assets`.
3. `ASSETS/GLOBAL` and `ASSETS/LOCAL` mirror each other by relative path.
4. A `LOCAL` file overrides a `GLOBAL` file only when the path after `LOCAL` and `GLOBAL` is identical.
5. `_Common-New` is the exact shared common folder name.

## Runtime Delivery Tree

```text
GAMEFORGE_folderstructure/
  ASSETS/
    GLOBAL/
      audio/
      data/themes/
      fonts/
      texture/portrait/
        animations/spine/
        animations/video/
        backgrounds/
        bigwin/
        effects/
        loading/
        logo/
        platform/
        symbols/
        ui/
    LOCAL/
      audio/
      data/themes/
      fonts/
      texture/portrait/
        animations/spine/
        animations/video/
        backgrounds/
        bigwin/
        effects/
        loading/
        logo/
        platform/
        symbols/
        ui/
```

Audio subfolders are `feature`, `interface`, `reel`, `rollup`, `symbols`, and `underscores`. Shared UI commonly uses `ui/bottom_toolbar` and `ui/quick_access`.

## P4 Mapping

```text
ASSETS/GLOBAL = //webgamedev/assets/_Common-New/
ASSETS/LOCAL  = //webgamedev/<gamefolder>/
```

Correct override:

```text
GLOBAL/texture/portrait/ui/bottom_toolbar/options_modal/panel.webp
LOCAL/texture/portrait/ui/bottom_toolbar/options_modal/panel.webp
```

Incorrect override:

```text
GLOBAL/texture/portrait/ui/bottom_toolbar/options_modal/panel.webp
LOCAL/texture/portrait/ui/panel.webp
```

## LOCAL vs GLOBAL

Use `LOCAL` for game-specific art, timing, naming, branding, colors, audio, fonts, feature assets, overrides, and anything only one game should ship.

Use `GLOBAL` for platform-wide assets or shared common assets reused unchanged across games. `GLOBAL` changes can affect multiple games and need review.

`assets/shared` means shared source art inside one game. It is not the same as runtime `ASSETS/GLOBAL`.

## Source Folders

The source `assets` tree is organized by mode and asset type:

```text
assets/base/
assets/freeGames/
assets/pickBonus/
assets/powerBet/
assets/shared/
assets/transition/
```

Common source asset types include `banner`, `font`, `highPaySymbol`, `midPaySymbol`, `lowPaySymbol`, `specialSymbol`, `interface`, `popUp`, `reelSound`, `rollup`, `underscore`, `celebration`, `winBox`, `intro`, and `outro`.

Most named source assets use `work/` for active files and `publish/` for approved handoff exports. Final runtime files are placed in `GAMEFORGE_folderstructure/ASSETS` after export and review.
