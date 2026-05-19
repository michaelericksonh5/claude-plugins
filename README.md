# h5g-plugins

A Claude plugin marketplace for High 5 Games tooling. Works in both
**Claude Code** (the CLI / IDE plugin) and **Claude Cowork** (the
collaborative mode inside the Claude desktop app).

## Plugins in this marketplace

| Plugin | What it does |
|---|---|
| [`skill-auditor`](https://github.com/michaelericksonh5/skill-auditor) | Audits a Claude skill against an 8-dimension quality rubric and returns a **READY / NEEDS WORK / DRAFT** verdict with specific, actionable findings. Checks frontmatter validity, description trigger quality, instruction clarity, reference integrity, completeness (no TODO/FIXME/TBD), output specification, evals coverage, and security. |
| [`slot-art-creator-node`](https://github.com/michaelericksonh5/slot-art-creator-node) | Generate, QA, and resize mobile slot art (symbols, UI, backgrounds, key art) with **two model families**: Nano Banana 2 (Gemini + fal.ai, 4 tools — the bulk of the workflow) and OpenAI's gpt-image-2 (2 tools — optional, for paytables, logos, banners with required copy, photorealistic 4K, and compositional multi-image edits). 13 slash commands (workflow + onboarding), persistent project memory, independent keys per family. |
| [`spine-slot-animation`](https://github.com/michaelericksonh5/Claude_Spine_Generator) | Generate validated Spine 4.2 proof packages for slot-game symbols, UI/system elements, and avatar state rigs from natural-language notes, separated PNG layers, or PSD-export manifests. Deterministic compiler pipeline with atlas packing, loop/settle validation, browser preview proof, and guarded advanced features. |
| [`rtk-token-saver`](https://github.com/michaelericksonh5/rtk-token-saver) | H5G wrapper around RTK for shell-output reduction, model-routing guidance, context hygiene, and conflict-safe setup checks. RTK remains the upstream engine; setup is explicit opt-in so it does not compete with other hooks during marketplace install. |
| [`webgamedev-structure`](https://github.com/michaelericksonh5/webgamedev_structure) | GameForge folder structure and artist-safe Perforce workflow guidance for `//webgamedev` assets. Covers GLOBAL/LOCAL placement, source-vs-runtime rules, Spine/video/UI/audio/text paths, and optional preview-first P4 helpers. |
| [`ai-video-generator`](https://github.com/michaelericksonh5/ai-video-mcp-server) | Generate AI videos using Veo 3.1, Happy Horse, and Seedance 2.0. Text-to-video, image-to-video, first+last frame, reference images, and video extension. Works with fal.ai and Google Gemini API keys. |

## Add this marketplace

### Claude Code (CLI / IDE)

From inside Claude Code, add the marketplace once, then install whichever plugins you want:

```
/plugin marketplace add michaelericksonh5/claude-plugins
/plugin install skill-auditor@h5g-plugins
/plugin install slot-art-creator-node@h5g-plugins
/plugin install spine-slot-animation@h5g-plugins
/plugin install rtk-token-saver@h5g-plugins
/plugin install webgamedev-structure@h5g-plugins
/plugin install ai-video-generator@h5g-plugins
/slot-setup
/rtk-token-saver
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
claude plugin install skill-auditor@h5g-plugins
claude plugin install slot-art-creator-node@h5g-plugins
claude plugin install spine-slot-animation@h5g-plugins
claude plugin install rtk-token-saver@h5g-plugins
claude plugin install webgamedev-structure@h5g-plugins
claude plugin install ai-video-generator@h5g-plugins
```

### Claude Cowork (Claude desktop app)

1. Open **Claude Desktop**
2. Switch to the **Cowork** tab
3. Click **Customize** in the left sidebar
4. Click **Browse plugins**
5. In the **Personal** section, click **+** > **Create plugin** > **Add marketplace**
6. Enter the URL: `https://github.com/michaelericksonh5/claude-plugins`
7. After it syncs, all six plugins appear in the marketplace listing — click **Install** on whichever you want
8. Open the plugin's settings and paste your API keys into the env-var fields (**not into chat** — credentials in chat get persisted in conversation history). See the [slot-art README](https://github.com/michaelericksonh5/slot-art-creator-node#api-keys) or [ai-video README](https://github.com/michaelericksonh5/ai-video-mcp-server#set-up-your-api-keys) for where to get keys.
9. **Restart Claude Desktop once** so the MCP server picks up your keys
10. In any Cowork chat, run `/slot-help` for the slot-art workflow overview, `/slot-setup` for a guided check that your keys are configured correctly, or `/rtk-token-saver` for RTK/model/context hygiene guidance. Ask for GameForge or `//webgamedev` structure help after installing `webgamedev-structure`. RTK shell-output filtering itself is a Claude Code/local-machine workflow; Cowork gets guidance, not local hook enforcement.

> [!NOTE]
> Cowork's **Personal** marketplace tier has a documented persistence bug
> ([claude-code #40600](https://github.com/anthropics/claude-code/issues/40600))
> where the marketplace persists across Claude Desktop restarts but installed
> plugins need to be re-installed each time Claude Desktop reopens. The fix
> on Anthropic's side is in progress. Workaround: re-install from the
> marketplace listing — the marketplace stays added.

## Marketplace catalog

```
claude-plugins/
└── .claude-plugin/
    └── marketplace.json    # catalog: lists each plugin's GitHub repo source
```

All six active plugins are sourced from GitHub repos owned by `michaelericksonh5` and exposed through this marketplace:

- `skill-auditor` from `michaelericksonh5/skill-auditor`
- `slot-art-creator-node` from `michaelericksonh5/slot-art-creator-node`
- `spine-slot-animation` from `michaelericksonh5/Claude_Spine_Generator`
- `rtk-token-saver` from `michaelericksonh5/rtk-token-saver`
- `webgamedev-structure` from `michaelericksonh5/webgamedev_structure`
- `ai-video-generator` from `michaelericksonh5/ai-video-mcp-server`

The older `token-saver` repo remains available at `michaelericksonh5/token_saver` for rollback or future reuse, but it is no longer listed in this marketplace.

## Adding a new plugin to this marketplace

1. Publish the plugin to its own public GitHub repo with a valid
   `.claude-plugin/plugin.json` at its root.
2. If the plugin includes a Node.js MCP server, bundle it into a single
   self-contained file (e.g. via `esbuild --bundle --platform=node --format=esm`)
   and check the bundle into the repo — Claude Code and Cowork don't run
   `npm install` on the cached plugin, so the bundle must be import-ready.
   Point `plugin.json`'s MCP `args` at the bundle path.
3. Add an entry to the `plugins[]` array in `.claude-plugin/marketplace.json`.
   Use the `github` source type for plugin repos:
   ```json
   {
     "name": "my-new-plugin",
     "source": { "source": "github", "repo": "michaelericksonh5/my-new-plugin" },
     "description": "...",
     "version": "1.0.0"
   }
   ```
4. Validate locally: `claude plugin validate .claude-plugin/marketplace.json`
5. Commit and push. Users with the marketplace already added pick up new
   plugins on the next `/plugin marketplace update`.

## Validation

Validate the marketplace manifest with the Claude CLI:

```
claude plugin validate .
```