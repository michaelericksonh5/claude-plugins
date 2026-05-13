# h5g-plugins

A Claude plugin marketplace for High 5 Games tooling. Works in both
**Claude Code** (the CLI / IDE plugin) and **Claude Cowork** (the
collaborative mode inside the Claude desktop app).

## Plugins in this marketplace

| Plugin | What it does |
|---|---|
| [`skill-auditor`](https://github.com/michaelericksonh5/skill-auditor) | Audits a Claude skill against an 8-dimension quality rubric and returns a **READY / NEEDS WORK / DRAFT** verdict with specific, actionable findings. Checks frontmatter validity, description trigger quality, instruction clarity, reference integrity, completeness (no TODO/FIXME/TBD), output specification, evals coverage, and security. |
| [`slot-art-creator-node`](https://github.com/michaelericksonh5/slot-art-creator-node) | Generate, QA, and resize mobile slot art (symbols, UI, backgrounds, key art) with **two model families**: Nano Banana 2 (Gemini + fal.ai, 4 tools — the bulk of the workflow) and OpenAI's gpt-image-2 (2 tools — optional, for paytables, logos, banners with required copy, photorealistic 4K, and compositional multi-image edits). 13 slash commands (workflow + onboarding), persistent project memory, independent keys per family. |

## Add this marketplace

### Claude Code (CLI / IDE)

From inside Claude Code, add the marketplace once, then install whichever plugins you want:

```
/plugin marketplace add michaelericksonh5/claude-plugins
/plugin install skill-auditor@h5g-plugins
/plugin install slot-art-creator-node@h5g-plugins
/slot-setup
```

The first command adds the marketplace. `/slot-setup` is a guided first-run skill
that walks you through getting and saving API keys safely (it points you at
a double-click launcher script — `setup-keys.bat` on Windows, `setup-keys.sh`
on Mac/Linux — that uses hidden-input prompts so keys never echo to terminal
logs and never touch chat). Once keys are configured, run `/slot-help` for
the workflow overview.

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
8. Open the plugin's settings and paste your `GEMINI_API_KEY` and `FAL_KEY` into the env-var fields (**not into chat** — credentials in chat get persisted in conversation history). See the [plugin README](https://github.com/michaelericksonh5/slot-art-creator-node#api-keys) for where to get keys.
9. **Restart Claude Desktop once** so the MCP server picks up your keys
10. In any Cowork chat, run `/slot-help` for the workflow overview, or `/slot-setup` for a guided check that your keys are configured correctly. Then jump to `/slot-step-00` (GDD-driven) or `/slot-step-01` (fresh concept).

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
via the `url` source type with explicit `https://` URLs. This keeps each
plugin's release cycle, issues, and version history independent, and avoids
the SSH-host-key fallback that the `github` shorthand triggers on machines
without an SSH key configured.

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
