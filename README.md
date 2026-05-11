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
8. Open the plugin's settings and paste your `GEMINI_API_KEY` and `FAL_KEY` into the env-var fields. (See the [plugin README](https://github.com/michaelericksonh5/slot-art-creator-node#api-keys) for where to get keys.)
9. **Restart Claude Desktop once** so the MCP server picks up your keys
10. Type `/` in any Cowork chat — you should see `/slot-art-creator-node:slot-step-00` through `slot-step-10`

> [!NOTE]
> Cowork's **Personal** marketplace tier has a documented persistence bug
> ([claude-code #40600](https://github.com/anthropics/claude-code/issues/40600))
> where the marketplace persists across Claude Desktop restarts but installed
> plugins need to be re-installed each time Claude Desktop reopens. The fix
> on Anthropic's side is in progress. Workaround: re-install from the
> marketplace listing — the marketplace stays added.

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
2. If the plugin includes a Node.js MCP server, bundle it into a single
   self-contained file (e.g. via `esbuild --bundle --platform=node --format=esm`)
   and check the bundle into the repo — Claude Code and Cowork don't run
   `npm install` on the cached plugin, so the bundle must be import-ready.
   Point `plugin.json`'s MCP `args` at the bundle path.
3. Add an entry to the `plugins[]` array in `.claude-plugin/marketplace.json`.
   Use the `url` source type with an explicit `https://` URL (avoids the
   git client trying SSH on machines without a key):
   ```json
   {
     "name": "my-new-plugin",
     "source": {
       "source": "url",
       "url": "https://github.com/michaelericksonh5/my-new-plugin.git"
     },
     "description": "...",
     "version": "1.0.0"
   }
   ```
4. Validate locally: `claude plugin validate .`
5. Commit and push. Users with the marketplace already added pick up new
   plugins on the next `/plugin marketplace update`.

## Validation

Validate the marketplace manifest with the Claude CLI:

```
claude plugin validate .
```
