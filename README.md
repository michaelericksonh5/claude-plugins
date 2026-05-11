# h5g-plugins

A Claude plugin marketplace for High 5 Games tooling. Works in both
**Claude Code** (the CLI / IDE plugin) and **Claude Cowork** (the
collaborative mode inside the Claude desktop app).

## Plugins in this marketplace

| Plugin | What it does |
|---|---|
| [`slot-art-creator-node`](https://github.com/michaelericksonh5/slot-art-creator-node) | Generate, QA, and resize mobile slot art (symbols, UI, backgrounds, key art) with Nano Banana 2. 11 numbered slash commands, persistent project memory, dual-provider routing (Gemini + fal.ai). |

## Add this marketplace

### Claude Code (CLI / IDE)

From inside Claude Code:

```
/plugin marketplace add michaelericksonh5/claude-plugins
/plugin install slot-art-creator-node@h5g-plugins
```

Or from a shell:

```
claude plugin marketplace add michaelericksonh5/claude-plugins
claude plugin install slot-art-creator-node@h5g-plugins
```

### Claude Cowork (Claude desktop app)

1. Open **Claude Desktop**
2. Switch to the **Cowork** tab
3. Click **Customize** in the left sidebar
4. Click **Browse plugins**
5. In the **Personal** section, click **+** > **Create plugin** > **Add marketplace**
6. Enter the URL: `https://github.com/michaelericksonh5/claude-plugins`
7. After it syncs, the **slot-art-creator-node** plugin appears in the marketplace listing — click **Install**

> [!NOTE]
> Cowork's **Personal** marketplace tier has a documented persistence bug
> ([claude-code #40600](https://github.com/anthropics/claude-code/issues/40600))
> where the marketplace persists but the installed plugin must be re-installed
> after every Claude Desktop restart. The fix on Anthropic's side is in progress.
> For a stable install, use Claude Code or wait for the fix.

## Repository structure

```
claude-plugins/
└── .claude-plugin/
    └── marketplace.json    # catalog: lists each plugin and where to fetch it
```

Individual plugins live in **their own GitHub repositories** and are referenced
via the `github` source type. This keeps each plugin's release cycle, issues,
and version history independent.

## Adding a new plugin to this marketplace

1. Publish the plugin to its own public GitHub repo with a valid
   `.claude-plugin/plugin.json` at its root.
2. Add an entry to the `plugins[]` array in `.claude-plugin/marketplace.json`:
   ```json
   {
     "name": "my-new-plugin",
     "source": {
       "source": "github",
       "repo": "michaelericksonh5/my-new-plugin"
     },
     "description": "...",
     "version": "1.0.0"
   }
   ```
3. Validate locally: `claude plugin validate .`
4. Commit and push. Users with the marketplace already added pick up new
   plugins on the next `/plugin marketplace update`.

## Validation

Validate the marketplace manifest with the Claude CLI:

```
claude plugin validate .
```
