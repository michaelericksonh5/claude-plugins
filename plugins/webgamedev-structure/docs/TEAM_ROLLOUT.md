# Team Rollout

## Install Expectations

Marketplace install is inert. It provides docs and a skill only. It must not install hooks, start MCP servers, register agents, or run P4 commands.

## Suggested Rollout

1. Review `skills/webgamedev-structure/GAMEFORGE_STRUCTURE.md` with art, tech art, engineering, and production leads.
2. Confirm current P4 workspace mappings for `//webgamedev/assets/_Common-New/` and each game folder.
3. Confirm typemap and exclusive-lock coverage for binary art.
4. Pick owners for `GLOBAL` / `_Common-New` reviews.
5. Share `docs/ARTIST_QUICKSTART.md` with artists and producers.
6. Run the optional doctor script on representative workstations.

## Validation Before Publishing

```powershell
npm test
claude plugin validate .
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
```

Do not add this plugin to a marketplace until those checks pass.
