# Asset Placement

Default final destination is `GAMEFORGE_folderstructure/ASSETS/LOCAL`. Use `GLOBAL` only for platform-wide or cross-game shared assets.

For dropped folders or plugin handoffs, use `ASSET_FOLDER_INTAKE.md` first to inventory files, classify source versus runtime, and preview P4 activity before final delivery.

## Runtime Assets

| Asset | Final path |
|---|---|
| Theme data | `ASSETS/LOCAL/data/themes` |
| Game data | `ASSETS/LOCAL/data` |
| Fonts | `ASSETS/LOCAL/fonts` |
| Feature audio | `ASSETS/LOCAL/audio/feature` |
| Interface audio | `ASSETS/LOCAL/audio/interface` |
| Reel audio | `ASSETS/LOCAL/audio/reel` |
| Rollup audio | `ASSETS/LOCAL/audio/rollup` |
| Symbol audio | `ASSETS/LOCAL/audio/symbols` |
| Underscore music | `ASSETS/LOCAL/audio/underscores` |
| Spine exports | `ASSETS/LOCAL/texture/portrait/animations/spine` |
| Video animations | `ASSETS/LOCAL/texture/portrait/animations/video` |
| Backgrounds | `ASSETS/LOCAL/texture/portrait/backgrounds` |
| Big-win art | `ASSETS/LOCAL/texture/portrait/bigwin` |
| Effects | `ASSETS/LOCAL/texture/portrait/effects` |
| Loading assets | `ASSETS/LOCAL/texture/portrait/loading` unless platform-wide |
| Logo | `ASSETS/LOCAL/texture/portrait/logo` |
| Platform prompts | `ASSETS/GLOBAL/texture/portrait/platform` when shared |
| Symbols | `ASSETS/LOCAL/texture/portrait/symbols` |
| UI | `ASSETS/LOCAL/texture/portrait/ui` |
| Bottom toolbar overrides | `ASSETS/LOCAL/texture/portrait/ui/bottom_toolbar` |
| Quick access overrides | `ASSETS/LOCAL/texture/portrait/ui/quick_access` |

Use the matching `GLOBAL` path only when the file is intentionally common across games.

## Spine

Final Spine packages usually include skeleton data, atlas data, and texture pages. Keep final exports under:

```text
GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/animations/spine
```

Working Spine source files stay under the source asset's `work` or `publish` area.

## Video

Final runtime video goes under:

```text
GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/animations/video
```

High-quality MOV or other approved source video belongs in source `assets`, not the runtime tree. Confirm alpha-video requirements before delivery.

## Source Files

Use `assets/<mode>/<assetType>/<assetName>/work` for active work and `publish` for approved handoff exports. Examples:

```text
assets/freeGames/specialSymbol/freeGames_WD1/work/photoshop
assets/base/reelSound/base_reel/work/maya/sound
assets/transition/intro/transition_intro/publish/exports
```

Do not place final runtime files in `assets` just because they were exported from a source tool.
