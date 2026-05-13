# Chat-Image Staging Workflow

Every NB2 tool that takes a `source` or `references` path validates that
the image lives inside the allowed-roots envelope — the active project
folder, `~/Pictures/claude_nb2`, `~/.h5g-slot-art-creator/inputs`, the
plugin folder, or anything in `SLOT_ART_EXTRA_ROOTS`. This is a real
security boundary: the LLM controls these paths and prompt injection
could otherwise read arbitrary user files via a malicious symlink.

But the most natural input — an image the user pastes into chat — lives
in a temp path far outside that envelope. Without staging, every edit
flow would force the user to manually save the image into a project
folder before the plugin could use it. That's the wrong default.

**`nb2_stage_image` is the bridge.** Use it any time the source isn't
already inside an allowed root.

## When to stage

Stage the image **before** calling `nb2_edit`, `nb2_upscale`, or
`nb2_smart_resize` whenever the source path:

- Came from a chat attachment (the user dragged/pasted into Claude Code
  or Cowork) — these land in temp paths the validator will reject.
- Was downloaded by the user into `~/Downloads/` or similar — outside
  the allowed roots.
- Lives in a project folder OTHER than the active one — e.g. they want
  to pull a reference from a previous game.
- Is an external screenshot, asset from another tool, or a URL.

You do NOT need to stage when the source is already inside the active
project folder (e.g. `Symbol_Art/HP1_001.png` produced by an earlier
`/slot-step-03` generation, or `Key_Art/Key_Art_003.png` from
`/slot-step-02`) or in `~/Pictures/claude_nb2`. Just resolve the
stored relative path against `project_root` and pass the resulting
absolute path directly.

## How to stage

The tool is `nb2_stage_image`. Minimal call:

```
nb2_stage_image({ source: "/tmp/chat-paste-1234.png" })
  → { staged path: "~/.h5g-slot-art-creator/inputs/chat_input_001.png" }
```

The staged path is what you then pass to `nb2_edit` / `nb2_upscale` /
`nb2_smart_resize`'s `source` (or `references`) argument.

Optional `label` arg lets you self-document the input filename. Useful
when staging multiple references in one workflow:

```
nb2_stage_image({ source: "...", label: "user_paste_HP1_reference" })
  → ~/.h5g-slot-art-creator/inputs/user_paste_HP1_reference_001.png

nb2_stage_image({ source: "...", label: "user_paste_BG_mood" })
  → ~/.h5g-slot-art-creator/inputs/user_paste_BG_mood_001.png
```

## End-to-end example — user pastes an image and asks for an edit

```
User: "Edit this turkey character to make him have a santa hat."
      [pastes image]

You (internally):
  1. The image landed at /tmp/clipboard-img-9f3a.png  (temp path, outside allowed roots).
  2. Call: nb2_stage_image({
       source: "/tmp/clipboard-img-9f3a.png",
       label: "turkey_for_santa_edit"
     })
     → staged at ~/.h5g-slot-art-creator/inputs/turkey_for_santa_edit_001.png
  3. Call: nb2_edit({
       prompt: "<bracketed-block edit prompt>",
       source: "~/.h5g-slot-art-creator/inputs/turkey_for_santa_edit_001.png",
       output_dir: <project_root>,
       asset_name: "HP1_santa"
     })
  4. Read the output and report back.
```

This pattern works identically for:

- **Upscale a pasted asset** → stage → `nb2_upscale`
- **Multi-aspect a pasted asset** → stage → `nb2_smart_resize`
- **Use a pasted image as a style reference** for `nb2_generate` →
  stage → pass the staged path in the `references` array

## Supported inputs

| Source type | Example | Notes |
|---|---|---|
| Local file (chat temp) | `C:\Users\...\AppData\Local\Temp\img.png` | Most common — chat attachments |
| Local file (downloads) | `~/Downloads/screenshot.png` | Same handling |
| Local file (other project) | `H:\Shared drives\...\OldGame\HP1.png` | Pulled across project boundaries |
| `~/`-relative path | `~/Pictures/test.png` | Expanded to home dir |
| HTTP/HTTPS URL | `https://example.com/asset.png` | Fetched through the SSRF-guarded path |

Accepted extensions: `.png`, `.jpg`, `.jpeg`, `.webp`. Max size 50MB.

## What staging does NOT do

- **Doesn't validate visual quality.** It copies bytes. If the source is
  a corrupt PNG, downstream tools will surface that.
- **Doesn't normalize the image.** No resizing, no format conversion
  (beyond keeping the source extension). What you stage is what you get.
- **Doesn't write to `project.json`.** Staged images aren't project
  assets — they're scratch inputs. The actual generation output written
  by `nb2_edit` etc. is what gets recorded as a project iteration.

## What lives in `~/.h5g-slot-art-creator/inputs/`

Over time this folder accumulates every chat-staged image plus any
download/screenshot you fed through the plugin. It's safe to prune
periodically — staged inputs are never referenced from `project.json`,
so deleting old ones won't break any project state. Treat it like the
temp folder it is.
