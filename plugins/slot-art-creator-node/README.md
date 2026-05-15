# slot-art-creator-node

High 5 Games slot machine art generation plugin for Claude Code and Claude Cowork.
**Node.js edition — no Python required.**

**Two model families, your choice per call:**

- **Nano Banana 2** ([fal.ai/models/fal-ai/nano-banana-2](https://fal.ai/models/fal-ai/nano-banana-2)) — 4 tools (`nb2_generate`, `nb2_edit`, `nb2_upscale`, `nb2_smart_resize`). Either Google Gemini OR fal.ai works fully. With both keys set, generate/edit/upscale routes to Gemini (direct API, same NB2 model) and smart-resize routes to fal.ai (purpose-built Nano Banana Pro endpoint).
- **GPT Image 2** ([OpenAI gpt-image-2](https://developers.openai.com/api/docs/models/gpt-image-2), released April 2026) — 2 tools (`gpt2_generate`, `gpt2_edit`) at 1K or 2K resolution. Best for **accurate in-image text** (paytables, logos, banners with copy), **stable 2K photorealism**, and **compositional multi-image edits**. More expensive per call than NB2 — use selectively for hero and text-heavy assets. For 4K marketing output: generate at 2K with `gpt2_generate`, then run `nb2_upscale` (tested path). **No faithful upscale mode** in gpt-image-2 (always regenerates); use `nb2_upscale` for true source-preserving upscales. **Multi-aspect resize stays on `nb2_smart_resize`** — a gpt2-based smart resize was prototyped but not shipped in v1.5.3 because output quality wasn't verified against the well-tested fal.ai path.

Both families are independent — set whichever keys you need. The NB2
family powers the bulk of the slot-step-* workflow; the gpt2 family is
opt-in for the surfaces where its strengths matter.

---

## Install

> **What is a marketplace?**
> Claude Code and Cowork discover plugins through *marketplace registries* — a small JSON index file hosted on GitHub that lists available plugins and where to find them. The H5G marketplace (`https://github.com/michaelericksonh5/claude-plugins`) is that index. Adding the marketplace URL is a one-time step; once it's added, any plugin in the registry shows up in the listing and can be installed with one click. Future updates are picked up automatically on the next sync.
>
> The plugin code itself lives in a separate repo (`slot-art-creator-node` — the one you're reading now), but for a marketplace install you never need to clone it. Claude pulls the pre-built MCP bundle directly from the registry.

### Fastest path — pick your situation

| You are... | Easiest install |
|---|---|
| **H5G employee on Cowork** | Ask IT / your Cowork admin to enable the H5G marketplace at the org level (one-time — see [H5G org-level install](#h5g-org-level-install-admins-set-once) below). After that, the plugin appears in your Customize tab with one click — no marketplace URL to paste. |
| **Anyone on Claude Code CLI** | Open a Claude Code terminal session and paste this block — it installs and starts setup in one go: `/plugin marketplace add michaelericksonh5/claude-plugins` then `/plugin install slot-art-creator-node@h5g-plugins` then `/slot-setup`. Three commands, ~10 seconds. |
| **Solo user on Cowork (no admin help)** | The 9-step Customize-tab flow in Path A2 below. There is no shorter user-level path today — Cowork has no chat install, no CLI install, and no deep-link install URLs. |
| **Plugin developer** | Path B (clone + `install.bat` / `install.sh`) further down. |

#### H5G org-level install (admins, set once)

Cowork Team / Enterprise plans support **organization-level marketplace sync**. An admin connects the H5G plugin registry once and every employee then sees H5G plugins auto-listed in their Cowork Customize tab — no marketplace URL pasting, no manual sync.

1. Sign in to **Claude Cowork** as an organization admin.
2. Open **Settings → Plugins** (admin-only section).
3. Choose **Connect GitHub repository** (or the equivalent "Add organization marketplace" action — Cowork's UI labels may vary by plan tier).
4. Paste the marketplace URL:
   ```
   https://github.com/michaelericksonh5/claude-plugins
   ```
5. Save. After Cowork syncs, every H5G employee sees `slot-art-creator-node` (and any future H5G plugins) in their personal Customize tab.

Reference: Anthropic's [Manage Cowork plugins for your organization](https://support.claude.com/en/articles/13837433-manage-claude-cowork-plugins-for-your-organization).

Employees still set their own API keys per-machine (`/slot-setup` or the Cowork plugin settings UI) — keys are per-user, not per-org.

---

### The two install paths in detail

Two paths. Pick the one that matches what you're doing:

| Path | Best for | Summary |
|---|---|---|
| **A. Marketplace install** | Most users — you just want to use the plugin | Add one URL in Claude Code or Cowork. Done. |
| **B. Local installer (`install.bat` / `install.sh`)** | Developers editing the plugin, offline machines, or anyone who wants API keys saved on disk instead of pasted into Cowork's UI | Clone repo, run installer, **then** add the marketplace to Cowork |

Both paths end the same way for Cowork: you add the GitHub marketplace URL inside Claude Desktop. **Cowork is a separate plugin system from Claude Code** — running `install.bat` doesn't install anything into Cowork on its own. The installer can build a legacy upload ZIP, but the marketplace flow below is simpler and stays in sync with future updates.

---

### Path A — Marketplace install (recommended)

You don't need to clone this repo or run anything locally. The marketplace ships a pre-built, self-contained MCP server bundle.

#### A1. Claude Code

> **These commands run in the Claude Code CLI — a terminal application, not Claude.ai or Claude Desktop.**
> Open a terminal (PowerShell, Terminal.app, etc.) and run `claude` to start a Claude Code session. The `/plugin` commands below are Claude Code CLI slash commands and will return "/plugin isn't available in this environment" if you try them anywhere else.
> Don't have Claude Code CLI? Install it: https://docs.anthropic.com/en/docs/claude-code/getting-started

Inside a Claude Code terminal session, run these three commands in order:

```
/plugin marketplace add michaelericksonh5/claude-plugins
/plugin install slot-art-creator-node@h5g-plugins
/slot-setup
```

The first two install the plugin. `/slot-setup` is a guided first-run skill — it
walks you through getting and saving API keys safely (it will never accept a key
typed in chat; it points you at a double-click launcher script that uses
hidden-input terminal prompts instead). Once keys are set, type `/slot-help` for
the workflow overview, or jump straight to `/slot-step-00` if you have a GDD or
`/slot-step-01` to pitch fresh.

#### A2. Claude Cowork

1. Open **Claude Desktop**
2. Switch to the **Cowork** tab
3. Click **Customize** in the left sidebar
4. Click **Browse plugins**
5. In the **Personal** section, click **+** > **Create plugin** > **Add marketplace**
   *(the label says "Create plugin" but this is how Cowork adds an external marketplace registry — you're not building anything new)*
6. Paste this URL and click **Add**:
   ```
   https://github.com/michaelericksonh5/claude-plugins
   ```
   This is the H5G plugin registry — a different repo from `slot-art-creator-node`. Adding it makes all H5G plugins discoverable inside Cowork.
7. After Cowork syncs (~5 seconds), `slot-art-creator-node` appears in the marketplace listing — click **Install**.
8. Open the plugin's settings inside Cowork. You'll see env-var fields for `GEMINI_API_KEY`, `FAL_KEY`, and `OPENAI_API_KEY` — paste your keys there (**not into chat** — credentials in chat get persisted in conversation history). Either Gemini or fal.ai alone unlocks the four NB2 tools; OpenAI is optional and enables the two `gpt2_*` tools (`gpt2_generate`, `gpt2_edit`) for text-heavy surfaces like paytables, logos, and banners. See [API keys](#api-keys) for where to get them.
9. **Restart Claude Desktop once** so the MCP server picks up the keys.
10. In any Cowork chat, type `/slot-help` for the workflow overview, or `/slot-setup` if you want a guided check that your keys are configured correctly. Then `/slot-step-00` (if you have a GDD) or `/slot-step-01` (fresh concept).

> [!NOTE]
> Cowork's **Personal** marketplace tier has a documented persistence bug
> ([claude-code #40600](https://github.com/anthropics/claude-code/issues/40600)) —
> the marketplace itself persists across Claude Desktop restarts, but the
> installed plugin needs to be re-installed each time Claude Desktop reopens.
> The marketplace stays, so re-installing is one click from the listing.
> Anthropic is working on an upstream fix.

---

### Path B — Local installer (`install.bat` / `install.sh`)

Use this if you want any of: a local clone of the source for editing, the plugin to work without GitHub access at runtime, or API keys saved to a local file (`~/.h5g-slot-art-creator/.env`) instead of typed into Cowork's UI.

#### B1. Clone the repo

```bash
git clone https://github.com/michaelericksonh5/slot-art-creator-node.git
cd slot-art-creator-node
```

#### B2. Run the installer

**Windows:** double-click `install.bat`. At the *"Where do you want to install this plugin?"* prompt, **press Enter** (default is `[1] BOTH`).

**Mac / Linux:**
```bash
chmod +x install.sh && ./install.sh
```
Same — press Enter at the install-target prompt.

The installer does this end-to-end:
1. Checks for Node.js 18+
2. Runs `npm ci` and `npm run build` inside `nb2-mcp-server/` to install dependencies and produce the self-contained MCP bundle at `dist/index.mjs`
3. Walks you through API key setup via `setup-keys.js` — keys saved to `~/.h5g-slot-art-creator/.env` (Windows: `%USERPROFILE%\.h5g-slot-art-creator\.env`). This file survives plugin reinstalls.
4. **For Claude Code:** registers a local marketplace at `~/Documents/Claude_Plugins/` pointing at your clone, and enables the plugin. After this, `/slot-step-*` commands work in Claude Code.
5. **For Claude Cowork (optional legacy path):** builds a manual-upload ZIP at `dist/slot-art-creator-node-cowork-upload.zip`. You don't need this if you follow B3 below.

#### B3. Add the marketplace to Cowork

Cowork doesn't see anything the installer did — it's a separate plugin system. To use the plugin in Cowork, follow the same steps as **A2** above (`https://github.com/michaelericksonh5/claude-plugins`).

You can ignore the upload ZIP unless your Cowork org policy blocks GitHub-synced marketplaces (rare). The marketplace flow auto-updates when we push new versions; the ZIP doesn't.

#### B4. (Re-)register Claude Code's local marketplace later

If you skipped step B2's Claude Code registration, or moved the cloned folder, run:

```bash
node tools/register-marketplace.js --enable
```

---

### Verifying it worked

**Claude Code:**
```
claude plugin list
```
Should show `slot-art-creator-node@h5g-plugins ... Status: √ enabled`.

**Both:** Type `/slot-` in chat. You should see 15 commands: 4 non-numbered utilities (`/slot-help` workflow tour, `/slot-setup` API-key configuration, `/slot-tutorial` guided end-to-end walkthrough, `/slot-compare` side-by-side review) plus the 11 numbered steps `slot-step-00` through `slot-step-10`. If they're missing, see [Troubleshooting](#troubleshooting) below.

---

## API keys

**Two key families with independent requirements:**

- **NB2 family** (4 `nb2_*` tools): either `GEMINI_API_KEY` OR `FAL_KEY` is fully sufficient. Both routes each tool to its strongest backend.
- **GPT Image 2 family** (2 `gpt2_*` tools — `gpt2_generate`, `gpt2_edit`): `OPENAI_API_KEY`. Optional — only needed if you want gpt-image-2 for paytables, logos, banners with required copy, stable-2K photorealism, or compositional multi-image edits. For 4K marketing output, generate at 2K with `gpt2_generate` then upscale via `nb2_upscale` (tested path).

| Provider | Get a key | Powers |
|---|---|---|
| **Google Gemini** | https://aistudio.google.com/apikey | NB2 tools (`nb2_*`) |
| **fal.ai** | https://fal.ai/dashboard | NB2 tools (`nb2_*`) |
| **OpenAI** | https://platform.openai.com/api-keys | gpt-image-2 tools (`gpt2_*`) — optional |

### NB2 tools — what each provider does

| Tool | Gemini path | fal.ai path |
|---|---|---|
| `nb2_generate` / `nb2_edit` / `nb2_upscale` | Calls `gemini-3.1-flash-image-preview` directly — this *is* Nano Banana 2 | Calls `fal-ai/nano-banana-2` — same underlying NB2 model, wrapped by fal.ai |
| `nb2_smart_resize` | Calls NB2 N times (once per target size) and center-crops the results with `pngjs` locally. Real limitation: if NB2 returns an image smaller than your target, it errors out and asks you to use fal.ai for that size. | Calls `fal-ai/smart-resize` — a **purpose-built endpoint using Nano Banana Pro** (a different, larger model). One API call handles all target sizes. No size limitation. |

### gpt-image-2 tools — when to prefer them

| If the asset needs... | Reach for... |
|---|---|
| Accurate text rendering in the image (paytables, logos, banners with copy) | `gpt2_generate` / `gpt2_edit` |
| Photorealistic 2K (marketing hero shots — gpt-image-2's stable ceiling) | `gpt2_generate` (size `2K`, quality `high`) — for genuine 4K, generate at 2K then run `nb2_upscale` |
| Compositional editing combining 2-16 reference images | `gpt2_edit` with `extra_references` |
| Routine slot symbols at thumbnail size | `nb2_generate` (NB2 is purpose-tuned, gpt2 is overkill and pricier) |
| Multi-aspect resize of any source | `nb2_smart_resize` (fal.ai NB Pro purpose-built endpoint, single call, cheapest; falls back to Gemini + pngjs when only `GEMINI_API_KEY` is set) |
| Multi-aspect resize where wordmark text must stay readable | Generate the new aspect ratio fresh at 2K with `gpt2_generate` and a recompose prompt — gpt2-based smart resize was prototyped but not shipped (output quality wasn't verified) |
| Genuine 4K marketing output | `gpt2_generate` at `2K` → `nb2_upscale` to 4K (tested path) |
| Upscale an approved 2K asset to 4K | `nb2_upscale` (gpt-image-2 doesn't faithfully upscale — it generates fresh) |

See `shared/gpt_image2_prompting.md` for the full gpt2 playbook (size mapping, quality settings, cost rule-of-thumb, per-skill recommendations).

### Routing when both keys are set

| Tool | Runs on | Why |
|---|---|---|
| `nb2_generate`, `nb2_edit`, `nb2_upscale` | Gemini | Same NB2 model underneath, but the direct Google API call is one hop fewer than going through fal.ai's wrapper |
| `nb2_smart_resize` | **Gemini** (as of v1.7.2) | Keeps the whole plugin on one model family (NB2) by default. fal's NB Pro endpoint is a different model and a single-call recompose without local crop — slightly different output character. To force fal's path, unset `GEMINI_API_KEY` in the calling process. |

### What each setup gives you

| Keys set | Result |
|---|---|
| **Gemini only** | All 4 tools work. `nb2_smart_resize` uses the NB2 + pngjs path; may fail on certain target sizes (see limitation above) |
| **fal.ai only** | All 4 tools work. Generate / edit / upscale go through fal's wrapper of NB2; smart_resize uses NB Pro |
| **Both (recommended)** | All 4 tools work, each routed to its strongest backend (table above) |

### Where to put your keys

**Never paste API keys into chat** — chat messages are persisted in
conversation transcripts. Use one of the safe entry channels below:

| You installed via... | Where to enter keys (safe channels) |
|---|---|
| **Claude Cowork (Path A or B)** | Cowork's built-in plugin settings UI. Open the plugin, find the env-var fields `GEMINI_API_KEY`, `FAL_KEY`, and `OPENAI_API_KEY`, paste your keys. Restart Claude Desktop. |
| **Claude Code, marketplace install (Path A)** | Easiest: run `/slot-setup` inside Claude Code — it'll surface the exact path to the double-click launcher script that ships with the plugin (`setup-keys.bat` on Windows, `setup-keys.sh` on Mac/Linux). The script uses hidden-input prompts so keys never echo to the terminal log. Walks you through up to three keys: Gemini, fal.ai, and OpenAI. Saves to `~/.h5g-slot-art-creator/.env`. Alternative: set shell env vars (`GEMINI_API_KEY`, `FAL_KEY`, `OPENAI_API_KEY`) before launching Claude Code. |
| **Claude Code, local installer (Path B)** | The installer already ran `setup-keys.js` for you. Keys are saved at: Windows `%USERPROFILE%\.h5g-slot-art-creator\.env`; macOS / Linux `~/.h5g-slot-art-creator/.env`. This file survives plugin reinstalls. |

To change keys later, double-click the launcher in your plugin install:

| Platform | Launcher path (replace `<version>` with what's in your install) |
|---|---|
| **Windows** | `%USERPROFILE%\.claude\plugins\cache\h5g-plugins\slot-art-creator-node\<version>\setup-keys.bat` |
| **Mac / Linux** | `$HOME/.claude/plugins/cache/h5g-plugins/slot-art-creator-node/<version>/setup-keys.sh` |

Or — equivalently — from a clone of the repo:

```bash
node setup-keys.js              # interactive (choose which to set)
node setup-keys.js --gemini     # only set the Gemini key
node setup-keys.js --fal        # only set the fal.ai key
node setup-keys.js --openai     # only set the OpenAI key
node setup-keys.js --check      # verify saved keys + show routing summary
node setup-keys.js --clear-gemini   # remove the Gemini key
node setup-keys.js --clear-fal      # remove the fal.ai key
node setup-keys.js --clear-openai   # remove the OpenAI key
```

### External users / non-H5G installs

The plugin's project folder defaults to H5G's Drive Stream path
(`H:\Shared drives\Content Management - AI\Production_AI 2\Asset_Creation_Suite\`)
when that mount exists. If you don't have that drive (most non-H5G installs),
the plugin falls back to `~/slot-art-projects/` per user.

To put project folders elsewhere (e.g. a Dropbox folder), set the env var
before launching Claude Code:

```
# Windows (PowerShell, persisted)
[Environment]::SetEnvironmentVariable("SLOT_ART_PROJECT_BASE", "C:\Users\you\Dropbox\slot-art-projects", "User")

# Mac / Linux (add to ~/.zshrc or ~/.bashrc)
export SLOT_ART_PROJECT_BASE="$HOME/Dropbox/slot-art-projects"
```

Resolution order at runtime: `SLOT_ART_PROJECT_BASE` env var →
H5G Drive Stream → `~/slot-art-projects/`. First hit wins.

### A note on naming

The Gemini SDK accepts both `GEMINI_API_KEY` and `GOOGLE_API_KEY` as aliases for the same key. Per [Google's official docs](https://ai.google.dev/gemini-api/docs/api-key) you should **set only one** — if both are set, `GOOGLE_API_KEY` takes precedence and the SDK prints a warning. Our plugin manifest only declares `GEMINI_API_KEY`, so Cowork's UI prompts you once (not twice for the same value).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Slash commands missing in Cowork after install | Persistence bug ([#40600](https://github.com/anthropics/claude-code/issues/40600)) | Re-install the plugin from the marketplace listing. The marketplace itself stays added. |
| MCP tools missing (`nb2_*`) but skills appear | API keys not set, or Claude Desktop wasn't restarted after entering them | Open plugin settings, verify keys are entered, restart Claude Desktop |
| "Plugin failed to load: Duplicate hooks file" | Stale cache of an old version | `claude plugin uninstall slot-art-creator-node@h5g-plugins` then re-install |
| `claude plugin marketplace add` errors with SSH host key | git client tried SSH but you have no SSH key configured | Our marketplace uses HTTPS sources, so this shouldn't happen — if it does, add `github.com` to `~/.ssh/known_hosts` or run `ssh -T git@github.com` once to accept the host |
| Skills sorted alphabetically (not numerically) in autocomplete | Old version cached | Update the marketplace: `/plugin marketplace update h5g-plugins`, then reinstall |

---

## Numbered workflow

The slash commands are numbered in workflow order — type `/slot-` and the
numbers tell you which step comes next. Project state persists across
sessions and conversation compaction (see [Project memory](#project-memory)).

| # | Command | When | What it does |
|---|---|---|---|
| — | `/slot-help` | Any time | Workflow overview + routes you to the right next step |
| — | `/slot-setup` | First run or when changing keys | Guided API-key configuration (never accepts keys via chat — points you at the safe launcher script) |
| — | `/slot-tutorial` | First time on the plugin, or a long gap away | Guided end-to-end walkthrough using a sample game. **DRY mode** by default (zero API credits — explains every step, every gate, every state diff). **LIVE mode** opt-in to actually generate the sample. |
| — | `/slot-compare` | Picking between iterations, verifying tier hierarchy, or auditing a reskin | Readonly side-by-side review of slot art. Three modes: ITERATION (multiple iterations of one asset), ASSET (different assets in one project), CROSS-PROJECT (same slot across two projects). Scores each against the rubric. Never writes to `project.json`. |
| 00 | `/slot-step-00` | Optional, before brief | Pulls GDD from Drive, seeds project |
| 01 | `/slot-step-01` | Foundation | Locks theme, palette, style, manifest into `project.json` |
| 02 | `/slot-step-02` | After brief | Master key art — becomes the visual style anchor |
| 03 | `/slot-step-03` | After key art | Individual symbols (HP, MP, LP, Wild, Scatter, Coin, Bonus, Mystery, Blocker, Loot Link family, Jackpot tiers, …) |
| 04 | `/slot-step-04` | After symbols (or after key art for IDEATION mode) | Full contact sheet for review |
| 05 | `/slot-step-05` | After key art | Base, free-spins, bonus, pick-me, wheel BGs |
| 06 | `/slot-step-06` | After BG | Bezel, HUD, paytable, banners, multipliers, lobby tile, logo, in-game avatars (animated characters), and bonus wheels (jackpot / bonus / multiplier / pick-em — generated as full single-graphic wheels with every slice laid out) |
| 07 | `/slot-step-07` | Optional | Adapt an existing UI mock to a new theme |
| 08 | `/slot-step-08` | Final review | RED/YELLOW/GREEN audit report |
| 09 | `/slot-step-09` | Production | Upscale approved 2K to 4K (output naming: `<source>_upscl_x<N>.png`) |
| 10 | `/slot-step-10` | Final delivery | Multi-aspect-ratio variants of approved hero (output naming: `<source>_resize_<W>_<H>.png`) |

### Natural-language triggers — you don't have to type the slash commands

Every skill auto-summons from plain English in chat — you don't need to remember the slash command. Here's what to say if you'd rather just describe what you want:

| If you say... | Claude runs |
|---|---|
| "help", "what does this plugin do", "where do I start", "I'm lost" | `/slot-help` |
| "set up my keys", "401 unauthorized", "auth failed", "the plugin isn't working", "Gemini rejected", "OPENAI_API_KEY is not set", "tools are failing" | `/slot-setup` |
| "show me how this works", "give me a tutorial", "I'm new", "demo this for me" | `/slot-tutorial` |
| "compare these", "which is better", "rank these", "A vs B", "are these consistent" | `/slot-compare` |
| "grab the GDD", "pull the design doc from Drive", "import the spec", "load [game] from Drive" | `/slot-step-00` |
| "let's make a [theme] game", "design a [theme] slot", "lock the brief", "define the symbols" | `/slot-step-01` |
| "create key art", "make a hero shot", "show me what this game looks like", "concept art" | `/slot-step-02` |
| "make HP1", "design the wild", "regenerate Zeus", "iterate on the scatter", "the WY1 needs work" | `/slot-step-03` |
| "show all the symbols", "the full symbol set", "give me a contact sheet", "preview the set" | `/slot-step-04` |
| "create the background", "make the BG", "what's behind the reels", "design the bonus environment" | `/slot-step-05` |
| "design the UI", "make the buttons", "create the paytable", "design the bonus wheel", "create a character/mascot", "wheel", "paytable", "logo" | `/slot-step-06` |
| "reskin this UI", "port this layout to our theme", "match this UI", "skin over this" | `/slot-step-07` |
| "audit the symbols", "QA the art", "is this ready to ship", "final QA", "review the whole game" | `/slot-step-08` |
| "upscale", "make this 4K", "blow this up", "higher resolution", "supersize this" | `/slot-step-09` |
| "multiple aspect ratios", "make a square version", "Instagram size", "social variants", "16:9 and 9:16" | `/slot-step-10` |

The triggers are fuzzy — you don't have to match the exact phrase. If you describe what you want and there's a reasonable match, the right skill will run. When you're not sure which one to invoke, just say "help" and `/slot-help` will route you.

### Route-and-resume on missing project

Starting with v1.5.5, generation skills (`/slot-step-02` through
`/slot-step-10`) and the comparison skill (`/slot-compare`) detect
when there's no active project on this machine and **guide you through
setup in the same conversation** instead of dead-ending. If you ask
`/slot-step-03 generate HP1` cold, the skill acknowledges what you
asked for, runs `/slot-step-01` (and `/slot-step-02` for the key art),
then resumes the original HP1 generation — without making you re-invoke
your command. See `shared/project_memory.md` → "The 'no active
project — guide through setup' pattern" for the full prerequisite chain
per skill.

---

## Project memory

Each game = one project folder under `<PROJECT_BASE>` (resolves to the
H5G shared Drive Stream when mounted, otherwise `~/slot-art-projects/`
or whatever `SLOT_ART_PROJECT_BASE` points at — see [External users /
non-H5G installs](#external-users--non-h5g-installs)). State persists
automatically — restart Claude Code, get compacted, switch machines,
and your project picks up where you left off.

### Folder layout

```
<PROJECT_BASE>/{GameID}_{username}/     # one folder per game
├── project.json                        # source of truth (brief + asset registry + counters)
├── game_brief.json                     # human-readable mirror of the brief
│
├── Key_Art/                            # master key art + wide/tall crops
├── Symbol_Sheets/                      # full-set contact sheets
├── Symbol_Art/                         # every individual reel symbol (HP, MP, LP, WD, SC, WY, JP, ...)
├── Backgrounds/                        # base, freespins, bonus, pickme, wheel
├── Avatars/                            # in-game animated characters (0–5 per game)
├── Bezels/                             # reel frames
├── HUD/                                # spin button + balance/bet/win chrome
├── Paytables/                          # paytable layouts
├── Win_Banners/                        # small / medium / big / mega / epic
├── Bonus_Screens/                      # intro screens for free-spins / pick-me / wheel bonuses
├── Wheels/                             # full bonus-wheel graphics (jackpot / bonus / multiplier / pick-em)
├── Multipliers/                        # x2, x10, ...
├── Logos/                              # hero / standard / compact lockups
├── Lobby_Tiles/                        # marketing thumbnails
└── QA_Reports/                         # audit .md reports from /slot-step-08
```

`<PROJECT_BASE>` resolves in this order: `SLOT_ART_PROJECT_BASE` env
var → the H5G shared Drive Stream → `~/slot-art-projects/`. Category
folders are created on first write. See `shared/project_memory.md` for
the full resolution rules.

### Asset naming

Inside each category folder, files follow `{Label}_{NNN}.{ext}` — a
three-digit zero-padded counter scoped to that folder, per-label,
monotonically increasing, **never overwritten**. Examples:

- `Key_Art/Key_Art_001.png`, `Key_Art/Key_Art_002.png`
- `Symbol_Art/HP1_001.png`, `Symbol_Art/HP1_002.png`,
  `Symbol_Art/LP1_001.png`, `Symbol_Art/WY1_001.png`,
  `Symbol_Art/JP1_001.png`
- `Backgrounds/BG_base_001.png`, `Backgrounds/BG_freespins_001.png`
- `Avatars/Avatar1_001.png`, `Avatars/Avatar2_001.png`
- `Wheels/Wheel_jackpot_001.png`, `Wheels/Wheel_multiplier_001.png`

Derived variants live next to their source: an upscaled `HP1_002.png`
becomes `Symbol_Art/HP1_002_upscl_x2.png`; a resized `Key_Art_003.png`
becomes `Key_Art/Key_Art_003_resize_2048_2048.png`.

See `shared/asset_naming.md` for the full label table.

### Active project pointer

`~/.h5g-slot-active-project.json` holds the current active GameID so any
slot- skill can find your project without asking. Pass a different GameID
as a skill argument to switch projects:

```
/slot-step-03 4471
```

### Resolution and aspect ratio

Always API parameters, never in prompt text:
- `image_size`: defaults to `2K` (project minimum); `4K` for key art and
  upscales
- `aspect_ratio`: defaults to `1:1` for symbols, `9:16` for portrait BGs

The MCP server enforces these as enums. Any prompt body that contains
resolution or aspect ratio strings fails Gate 1 validation and is
rejected before NB2 sees it.

---

## Two-gate generation protocol

Every design skill runs validation before AND after generating:

- **Gate 1 (pre-generation):** Validates the prompt against the brief —
  style lock present, tier-correct palette, LP gold contamination check,
  wild category break, background color rule, no resolution strings.
  Nothing goes to NB2 until clean.
- **Gate 2 (post-generation):** Claude reads the image immediately. BLOCK
  items trigger automatic re-prompt + regenerate (max 2 retries). FLAG
  items surface a question. Only PASS moves to the next asset.

`/slot-step-08` is the **final** audit, not the first pass — for the
cross-asset consistency review you can only do once a full set is done.

---

## MCP tools

The bundled `nb2node` MCP server exposes 8 tools across two model families plus two helpers:

| Tool | Family | Description |
|---|---|---|
| `nb2_generate` | NB2 | Text-to-image (Gemini/fal.ai routing) |
| `nb2_edit` | NB2 | Image-to-image edit / reskin |
| `nb2_upscale` | NB2 | Path-A upscale (the only **faithful** upscale tool — preserves source pixels). Typical 2K→4K is `_upscl_x2`. |
| `nb2_smart_resize` | NB2 | Multi-size pixel-perfect resize. Either provider works — see [API keys](#api-keys) for routing details. Output naming: `<source>_resize_<W>_<H>.png` (one file per target). |
| `gpt2_generate` | gpt-image-2 | Text-to-image with gpt-image-2 at 1K or 2K. Use for paytables, logos, banners with copy, hero photorealism. For 4K, generate at 2K here then run `nb2_upscale`. |
| `gpt2_edit` | gpt-image-2 | Image-to-image edit with optional mask; accepts an array of up to ~16 reference images for compositional editing |
| `nb2_stage_image` | helper | Copy any external/chat-attached image into the safe inputs folder so it can be passed as `source` or `references` to any of the above |
| `nb2_measure` | helper | OKLCH color metrics, fill percentage, and background-uniformity audit for a single PNG. Used by `/slot-step-08` for numeric QA checks. Generation tools accept `measure: true` to auto-run it on each output. |

**`output_dir` contract (v1.5.5+).** Every generation tool requires
`output_dir` to be an absolute path. Inside a `/slot-step-*` skill, that
means `path.join(project_root, "<Category>")` where `<Category>` is one
of the 13 named subfolders (`Key_Art`, `Symbol_Art`, `Avatars`, `Bezels`,
`Win_Banners`, etc.). Relative paths are rejected with an actionable
error message that lists every valid category. Omitting `output_dir`
entirely still falls back to `~/Pictures/claude_nb2` for ad-hoc usage
outside a project.

---

## Shared reference docs

| File | Contents |
|---|---|
| `shared/project_memory.md` | Project state schema, startup protocol, atomic writes |
| `shared/asset_naming.md` | Filename convention, per-label counter logic |
| `shared/qa_preflight.md` | Two-gate validation protocol |
| `shared/nb2_prompting.md` | Master prompt formula, bracketed-block templates, style library |
| `shared/gpt_image2_prompting.md` | When to prefer gpt-image-2 over NB2, size/quality settings, cost rules |
| `shared/art_principles.md` | Mobile slot art principles — silhouette, hierarchy, lighting, CVD |
| `shared/symbol_vocabulary.md` | Full H5G prefix system (HP, MP, LP, WD, WYS, SF, Loot Link family, compounds, etc.) |
| `shared/mode_variants.md` | Game mode variants (base, free-spins, bonus) — discipline for slot-step-03 |
| `shared/chat_image_staging.md` | How to stage chat-attached images into the allowed-roots envelope before passing to MCP tools |
| `shared/upscale_workflow.md` | Path-A upscale loop |
| `shared/production_handoff.md` | Final delivery checklist and handoff package spec |
