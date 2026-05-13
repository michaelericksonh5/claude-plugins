---
name: slot-setup
description: FIRST RUN and KEY-FAILURE TRIAGE — Configure the slot-art-creator-node plugin for use, OR diagnose why a tool just failed with an authentication error. Walks the user through getting Google Gemini, fal.ai, and/or OpenAI API keys and saving them WITHOUT ever putting the keys in chat. The plugin supports two model families with independent keys — NB2 (Gemini/fal.ai, runs the 4 nb2_* tools) and gpt-image-2 (OpenAI, runs the 2 gpt2_* tools). Use this skill aggressively whenever ANY of the following happens — these are the real-world phrases that mean "keys are broken or missing": "set up my keys", "add my OpenAI key", "configure the plugin", "I need to add my API key", "my key isn't working", "the plugin isn't working", "none of the tools work", "the MCP server isn't working", "I'm getting auth errors", "401 unauthorized", "401 error", "authentication failed", "API rejected the key", "Gemini rejected", "OpenAI rejected the key", "OPENAI_API_KEY is not set", "GEMINI_API_KEY is not set", "FAL_KEY is not set", "no API key", "missing API key", "WARNING: no NB2 key", "tool failed with auth", or any pasted MCP error containing 401/403/unauthorized/forbidden. Also use when a user has just installed the plugin, wants to add a new provider, change which provider runs, rotate a key, check whether keys are valid, or generally confirm everything is configured. Run this BEFORE any /slot-step-* skill if keys aren't configured — and run it AGAIN any time a generation tool fails with an auth-shaped error to re-validate.
---

# Setup — API Keys & First-Run Configuration

This skill handles the one-time setup users need before any other skill in
the plugin works. It does **orientation and validation only** — it never
accepts API keys via chat. Keys go through safe channels (terminal scripts
with hidden input, or Cowork's built-in plugin settings UI).

## Why never accept keys in chat

API keys are credentials. Chat messages are persisted in conversation
transcripts, may be stored locally on disk, and may be visible to other
tools, processes, or backups. Treating an API key the same way you'd treat
a credit card means: never paste it in chat.

**If the user pastes a key in chat at any point during this skill, stop
and tell them:**

> "Please don't paste API keys in chat — they get saved in conversation
> history. Delete that message if you can, then use one of the safe entry
> methods below. Your keys are not yet saved to the plugin."

Then redirect them to the appropriate safe method.

## Workflow

### Step 1 — Diagnose with ground truth (DO THIS FIRST)

**Never infer key state from reading files alone.** A key that's present in
`.env` but doesn't authenticate is the most common silent failure mode (stale
key, account deactivated, wrong project, copy-paste error introducing
whitespace). Run the plugin's built-in validator before doing anything else:

1. Resolve the plugin's installed path. The plugin lives in the Claude Code
   plugin cache. Use Glob with pattern
   `~/.claude/plugins/cache/h5g-plugins/slot-art-creator-node/*/setup-keys.js`
   and pick the newest version directory.

2. Run the validator via the Bash tool:

   ```
   node "<absolute path to setup-keys.js>" --check
   ```

   This makes real (free) API calls against Gemini and OpenAI to confirm the
   keys actually work, and reports a routing summary showing which tools are
   enabled.

3. **Show the user the full output.** Don't summarize — the user benefits
   from seeing exactly what's set vs. what's missing vs. what's broken.

4. Based on the output, branch:
   - **All keys OK** → confirm everything works, recommend a next-step skill, done.
   - **NB2 keys (Gemini/FAL) all missing** → user needs to run setup. Continue to Step 2.
   - **One key missing or broken** → ask the user whether they want to add/fix it. Continue to Step 2 for the affected provider only.

### Step 1b — Where keys actually live

- Canonical `.env` file: `~/.h5g-slot-art-creator/.env`
  - Windows: `%USERPROFILE%\.h5g-slot-art-creator\.env`
  - Mac/Linux: `$HOME/.h5g-slot-art-creator/.env`

The MCP server reads this file at startup via dotenv with `override: true`,
so values in the file always win over any environment variables Claude Code
may have injected (including unresolved `${VAR}` placeholder strings — that
was a real bug in versions before v1.7.0). If `node setup-keys.js --check`
reports a key as `MISSING`, the most likely cause is that the file doesn't
exist or that key wasn't written yet.

If the user reports a tool failed with an auth error after they thought keys
were set, check the MCP server's startup banner in the Claude Code logs.
The banner explicitly says which .env path loaded and which keys it found.
That's the fastest way to confirm the MCP server is seeing what the
validator sees.

**Detect which surface the user is on** (Claude Code or Cowork). Cowork
sessions can be inferred from environment cues or just asked. The
guidance differs between them.

### Step 2 — Branch on state

Two key families with independent requirements:

- **NB2 family** (the 4 `nb2_*` tools): needs `GEMINI_API_KEY` and/or
  `FAL_KEY`. Either alone is sufficient.
- **GPT Image 2 family** (the 2 `gpt2_*` tools — `gpt2_generate` and
  `gpt2_edit`): needs `OPENAI_API_KEY`. Optional — only required if the
  user wants to use gpt-image-2 for text rendering, stable-2K
  photorealism, or multi-image composition.

**State A — fully configured for both families:**
GEMINI and/or FAL set AND OPENAI set. Confirm everything's ready, skip
to Step 4 (validation).

**State B — NB2 ready, no OpenAI:**
The plugin's main NB2 workflow works. Ask the user if they want to add
OpenAI for the gpt-image-2 tools (worth it for paytables, logos,
text-heavy assets). If no, skip to Step 4.

**State C — OpenAI only, no NB2:**
gpt2_* tools work but nothing else does. Tell the user the NB2 tools
are disabled and ask if they want to add GEMINI_API_KEY or FAL_KEY.

**State D — nothing configured:**
Walk through all three. Continue to Step 3.

**State E — partial NB2 (one of Gemini/fal but not both):**
Tell the user what their current setup does, ask if they want to add
the other NB2 key for optimal routing AND/or add OpenAI for the
gpt2_* tools.

### Step 3 — Guide the user to set keys safely

State each provider once, with the link to get a key. Then give the user
the platform-specific safe entry instructions below.

> **API keys — two independent families:**
>
> **NB2 family** (powers the 4 `nb2_*` tools — generate / edit / upscale /
> smart_resize). Either alone is sufficient; both set gives optimal routing.
> - Google Gemini: https://aistudio.google.com/apikey
> - fal.ai: https://fal.ai/dashboard
>
> **GPT Image 2 family** (powers `gpt2_generate` / `gpt2_edit`). Optional —
> set this if you want OpenAI's gpt-image-2 for paytables, logos, banners
> with text, stable-2K photorealism, or compositional multi-image edits.
> For genuine 4K, generate at 2K with gpt2 then upscale with `nb2_upscale`
> (that's a tested path). More expensive per call than NB2 — use selectively.
> - OpenAI: https://platform.openai.com/api-keys
>
> See `shared/nb2_prompting.md` for the NB2 routing table and
> `shared/gpt_image2_prompting.md` for when to pick gpt-image-2 over NB2.

#### Claude Cowork users

Cowork has a built-in safe key entry UI. Walk them through it:

1. Open the **Claude Desktop** app
2. Switch to the **Cowork** tab
3. Click **Customize** in the sidebar > **Browse plugins**
4. Find **slot-art-creator-node** in the listing and click into it
5. In the plugin's settings, you'll see fields for `GEMINI_API_KEY`,
   `FAL_KEY`, and `OPENAI_API_KEY`. **Paste your key(s) there — not in
   this chat.** Either Gemini or fal.ai is enough to run the NB2
   workflow; OpenAI is optional and unlocks the `gpt2_*` tools used
   for text-heavy surfaces (paytables, logos, wheels, banner copy).
6. **Restart Claude Desktop once** so the MCP server picks up the new keys.
7. Come back to chat and say "done" (or "keys are set", or similar) — I'll
   verify everything works.

#### Claude Code users — double-click launcher (recommended)

Resolve the absolute path to the launcher script. The plugin lives in the
Claude Code plugin cache:

- Windows: `%USERPROFILE%\.claude\plugins\cache\h5g-plugins\slot-art-creator-node\<version>\setup-keys.bat`
- Mac/Linux: `$HOME/.claude/plugins/cache/h5g-plugins/slot-art-creator-node/<version>/setup-keys.sh`

Read the plugin manifest (`<install path>/.claude-plugin/plugin.json`) to
get the exact `<version>`. List the directory under
`~/.claude/plugins/cache/h5g-plugins/slot-art-creator-node/` if multiple
versions exist — pick the newest.

Print the exact path to the user with clear platform instructions:

**Windows:**
> 1. Open File Explorer
> 2. Paste this path into the address bar and press Enter:
>    `<absolute path to setup-keys.bat>`
> 3. A terminal window opens. Paste your key(s) when prompted — your input
>    is hidden, keys do not echo to the screen.
> 4. When it says "Setup complete," close that window and come back here.

**Mac / Linux:**
> 1. Open a Terminal
> 2. Paste this command and press Enter:
>    `bash '<absolute path to setup-keys.sh>'`
> 3. The script prompts you for each key — your input is hidden.
> 4. When done, come back here.

Once the user reports they've finished, continue to Step 4.

#### Claude Code users — manual fallback

If the launcher script doesn't run for any reason (Node missing,
permissions, etc.), the user can edit the `.env` file directly:

> 1. Create or open this file in any text editor:
>    `~/.h5g-slot-art-creator/.env`
>    (You may need to create the folder first.)
> 2. Add one, two, or all three lines (no quotes, no spaces around the `=`):
>    ```
>    GEMINI_API_KEY=AIza...your-key-here
>    FAL_KEY=...your-key-here
>    OPENAI_API_KEY=sk-...your-key-here
>    ```
>    Either Gemini or fal.ai is enough to run the NB2 workflow; OpenAI
>    is optional and only needed if you want the `gpt2_*` tools for
>    text-heavy surfaces (paytables, logos, wheels, banner copy).
> 3. Save the file, then come back here.

### Step 4 — Validate (re-run the same diagnostic)

Once the user reports keys are set, re-run the validator that Step 1 used:

```
node "<absolute path to setup-keys.js>" --check
```

This is the **single source of truth** for whether keys actually work. It
makes real API calls against Gemini and OpenAI (free / cheap endpoints), so
a passing result here means the MCP server will succeed on its first real
generation call.

If the validator still reports a key as `MISSING` or `FAIL`:
- `MISSING` → the user didn't write to `~/.h5g-slot-art-creator/.env`. Ask
  where they saved keys — they may have used a different file or the wrong
  Cowork field.
- `FAIL: 401` → the key is wrong (typo, deactivated account, wrong project).
  Ask them to regenerate the key at the provider's dashboard.
- `Network check skipped` → ambient network issue; the key is structurally
  valid but couldn't be validated this run. That's fine; move on.

Do **NOT** print the key values back to the user. The validator never prints
them either — just lengths and pass/fail.

For Cowork users where keys live in the plugin's env-var UI (not in `.env`),
the validator can't see them — Cowork passes them through Claude's MCP
spawn rather than the .env file. In that case, the validator will say
`MISSING` even though keys are set. Trust the user's confirmation and move
on; real validation happens on first MCP call. (This is a known limitation
of running the validator outside the Claude harness.)

### Step 5 — Confirm and route

Tell the user what they have and what's next. Examples:

**Full setup:**

> ✓ Setup complete.
>   Gemini  : set       (NB2 tools: enabled)
>   fal.ai  : set       (NB2 tools: enabled, smart_resize optimized)
>   OpenAI  : set       (gpt2_* tools: enabled)
>
> NB2 routes generate/edit/upscale to Gemini and smart_resize to fal.ai.
> gpt-image-2 is available via gpt2_generate / gpt2_edit for paytables,
> logos, text-heavy banners, and compositional edits.
>
> Next steps:
>   - If you have a Game Design Document: run `/slot-step-00`
>   - If you're pitching a fresh concept: run `/slot-step-01`
>   - For an overview of the workflow: run `/slot-help`

**NB2 only:**

> ✓ NB2 setup complete (Gemini and/or fal.ai). All 4 NB2 tools work.
>   gpt2_* tools are disabled — add OPENAI_API_KEY later if you want
>   gpt-image-2 for paytables, logos, or text-heavy assets.
>
> Next steps: `/slot-step-00`, `/slot-step-01`, or `/slot-help`.

**OpenAI only (rare):**

> ✓ gpt-image-2 setup complete. gpt2_generate and gpt2_edit are
>   available, but the NB2 tools (which power most of the slot-step-*
>   workflow) need GEMINI_API_KEY or FAL_KEY too.

## Hard rules

- **Never accept an API key value in chat.** If the user pastes one,
  refuse to use it and instruct them to delete the message and use a
  safe channel.
- **Never echo a key value back to the user.** Even partial values. Confirm
  presence only ("set" / "empty").
- **Never write a key value to any file the user can see in the chat
  output.** Only the canonical `.env` file, which the user manages.
- **Always tell the user where keys are saved** so they know how to update
  them later.

## What this skill does NOT do

- It does not store keys in the project's `project.json` (those are
  per-game; keys are per-user).
- It does call `node setup-keys.js --check` in Steps 1 and 4 to get
  ground-truth validation of the keys. Those checks hit Gemini's
  `models.list` endpoint and OpenAI's `models.list` endpoint — both are
  free / cheapest-tier reads, not generation calls. Quota impact is
  negligible. The validator returns within a couple of seconds and
  surfaces stale, deactivated, or malformed keys before they cause a
  confusing 401 in a real generation later.
- It does not handle multi-account scenarios (e.g. one Gemini key for
  prod, one for testing). Users with that requirement should set keys
  via shell env vars instead of `.env` so they can swap on the fly.

## References

- `setup-keys.js` — the implementation that actually prompts for keys
  with hidden input
- `setup-keys.bat` / `setup-keys.sh` — double-clickable launchers around
  setup-keys.js
- `shared/nb2_prompting.md` — provider routing table for context
- `README.md` — installation flow including this step
