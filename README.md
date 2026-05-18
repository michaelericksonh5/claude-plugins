# h5g-plugins

A Claude plugin marketplace for High 5 Games tooling. Works in both
**Claude Code** (the CLI / IDE plugin) and **Claude Cowork** (the
collaborative mode inside the Claude desktop app).

## Plugins in this marketplace

| Plugin | What it does |
|---|---|
| [`skill-auditor`](https://github.com/michaelericksonh5/skill-auditor) | Audits a Claude skill against an 8-dimension quality rubric and returns a **READY / NEEDS WORK / DRAFT** verdict with specific, actionable findings. Checks frontmatter validity, description trigger quality, instruction clarity, reference integrity, completeness (no TODO/FIXME/TBD), output specification, evals coverage, and security. |
| [`slot-art-creator-node`](https://github.com/michaelericksonh5/slot-art-creator-node) | Generate, QA, and resize mobile slot art (symbols, UI, backgrounds, key art) with **two model families**: Nano Banana 2 (Gemini + fal.ai, 4 tools — the bulk of the workflow) and OpenAI's gpt-image-2 (2 tools — optional, for paytables, logos, banners with required copy, photorealistic 4K, and compositional multi-image edits). 13 slash commands (workflow + onboarding), persistent project memory, independent keys per family. |
| [`token-saver`](https://github.com/michaelericksonh5/token_saver) | Reduce avoidable Claude token usage and cost with model-routing guidance, context hygiene, Claude Code settings examples, output-filtering hooks, and status-line visibility. Helps teams default to cost-effective Claude usage while preserving Opus for work that actually needs it. |
| [`ai-video-generator`](https://github.com/michaelericksonh5/ai-video-mcp-server) | Generate AI videos using Veo 3.1, Happy Horse, and Seedance 2.0. Text-to-video, image-to-video, first+last frame, reference images, and video extension. Works with fal.ai and Google Gemini API keys. |

## Add this marketplace

### Claude Code (CLI / IDE)

From inside Claude Code, add the marketplace once, then install whichever plugins you want:

```
/plugin marketplace add michaelericksonh5/claude-plugins
/plugin install skill-auditor@h5g-plugins
/plugin install slot-art-creator-node@h5g-plugins
/plugin install token-saver@h5g-plugins
/plugin install ai-video-generator@h5g-plugins
/slot-setup
/token-saver
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
claude plugin install token-saver@h5g-plugins
```

### Claude Cowork (Claude desktop app)

1. Open **Claude Desktop**
2. Switch to the **Cowork** tab
3. Click **Customize** in the left sidebar
4. Click **Browse plugins**
5. In the **Personal** section, click **+** > **Create plugin** > **Add marketplace**
6. Enter the URL: `https://github.com/michaelericksonh5/claude-plugins`
7. After it syncs, all four plugins appear in the marketplace listing — click **Install** on whichever you want
8. Open the plugin's settings and paste your API keys into the env-var fields (**not into chat** — credentials in chat get persisted in conversation history). See the [slot-art README](https://github.com/michaelericksonh5/slot-art-creator-node#api-keys) or [ai-video README](https://github.com/michaelericksonh5/ai-video-mcp-server#set-up-your-api-keys) for where to get keys.
9. **Restart Claude Desktop once** so the MCP server picks up your keys
10. In any Cowork chat, run `/slot-help` for the slot-art workflow overview, `/slot-setup` for a guided check that your keys are configured correctly, or `/token-saver` for model/context hygiene guidance.

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
├── .claude-plugin/
│   └── marketplace.json    # catalog: lists each plugin and where to fetch it
└── plugins/
    ├── ai-video-generator/      # bundled copy of the ai-video plugin
    ├── skill-auditor/          # bundled copy of the skill-auditor plugin
    ├── slot-art-creator-node/  # bundled copy of the slot-art plugin
    └── token-saver/            # bundled copy of the token-saver plugin
```

The `skill-auditor`, `slot-art-creator-node`, `ai-video-generator`, and `token-saver` plugins are bundled directly
in this repo under `plugins/` (using `"source": "./plugins/…"` in the catalog).

## Adding a new plugin to this marketplace

1. Publish the plugin to its own public GitHub repo with a valid
   `.claude-plugin/plugin.json` at its root.
2. If the plugin includes a Node.js MCP server, bundle it into a single
   self-contained file (e.g. via `esbuild --bundle --platform=node --format=esm`)
   and check the bundle into the repo — Claude Code and Cowork don't run
   `npm install` on the cached plugin, so the bundle must be import-ready.
   Point `plugin.json`'s MCP `args` at the bundle path.
3. Add an entry to the `plugins[]` array in `.claude-plugin/marketplace.json`.
   Use the `github` source type for external repos:
   ```json
   {
     "name": "my-new-plugin",
     "source": { "source": "github", "repo": "michaelericksonh5/my-new-plugin" },
     "description": "...",
     "version": "1.0.0"
   }
   ```
   Or bundle it locally in `plugins/my-new-plugin/` and use:
   ```json
   { "name": "my-new-plugin", "source": "./plugins/my-new-plugin" }
   ```
4. Validate locally: `claude plugin validate .`
5. Commit and push. Users with the marketplace already added pick up new
   plugins on the next `/plugin marketplace update`.

## Validation

Validate the marketplace manifest with the Claude CLI:

```
claude plugin validate .
```