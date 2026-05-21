# webgamedev-structure

GameForge folder placement and P4 workflow guidance for `//webgamedev/` asset teams.

This plugin is intentionally inert on install. It ships one skill, documentation, optional scripts, and tests. It does not install hooks, start MCP servers, register agents, or run Perforce commands automatically.

## What It Covers

- GameForge runtime structure under `GAMEFORGE_folderstructure/ASSETS`.
- `ASSETS/GLOBAL` to `//webgamedev/assets/_Common-New/` and `ASSETS/LOCAL` to `//webgamedev/<gamefolder>/`.
- Artist-safe P4 setup, diagnostics, preview-first add/edit operations, never-delete policy, and submit checklists.
- Asset placement for Spine, video, symbols, backgrounds, UI, logo, big win, effects, fonts, audio, theme data, and source files.

## Optional Local Scripts

Read-only checks can run directly:

```powershell
.\scripts\p4-doctor.ps1
.\scripts\webgamedev-p4.ps1 doctor
.\scripts\webgamedev-p4.ps1 classify GAMEFORGE_folderstructure\ASSETS\LOCAL\texture\portrait\symbols\hp1.webp
```

Mutating P4 operations require `--apply`; without it, the CLI prints the command it would run or uses preview flags where P4 supports them.

```powershell
.\scripts\webgamedev-p4.ps1 sync //webgamedev/mygame/... --apply
.\scripts\webgamedev-p4.ps1 edit //webgamedev/mygame/texture/portrait/symbols/hp1.webp --apply
```

Blocked operations include `p4 clean`, `p4 delete`, `p4 move`, `p4 reconcile -d`, `p4 reconcile -w`, `p4 revert`, `p4 revert -w`, `p4 obliterate`, typemap edits, and binary conflict resolution. Reconcile automation uses add/edit only: `p4 reconcile -n -a -e` for previews and `p4 reconcile -a -e` with `--apply`.

## Development

```powershell
npm test
claude plugin validate .
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
```
