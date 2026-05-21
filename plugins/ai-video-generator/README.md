# AI Video Generator — Claude Plugin

AI video generation for Claude using **Veo 3.1**, **Happy Horse**, and **Seedance 2.0**.

Works with **fal.ai** API keys and **Google Gemini** API keys.

---

## What it can do

### AI Video Generation

| Capability | fal.ai | Gemini |
|---|---|---|
| Text → Video (Veo 3.1) | ✅ | ✅ (preferred) |
| Image → Video (Veo 3.1) | ✅ | ✅ (preferred) |
| First + Last Frame → Video | ✅ | ✅ (preferred) |
| Reference Images → Video | ✅ | ✅ (preferred) |
| Extend Video | ✅ | — (requires Vertex AI) |
| Happy Horse Image → Video | ✅ | — |
| Happy Horse Reference → Video | ✅ | — |
| Seedance 2.0 Image → Video | ✅ | — |
| Seedance 2.0 Reference → Video | ✅ | — |

**Gemini is preferred** for all dual-provider Veo 3.1 tools when both keys are configured.

**Resolutions:** 720p, 1080p, 4K
**Aspect ratios:** 16:9, 9:16, 1:1, 4:3, 21:9 (model-dependent)
**Duration:** 4–15 seconds
**Audio:** natively generated (fal.ai / Seedance)

### Output & Post-Processing

All generated videos are:
- **Auto-saved as `.mov`** to `~/.h5g-ai-video/output/` (lossless container rewrap from MP4)
- **Named by asset** when `asset_name` + `animation_type` are provided: `HP1_idle_1747234567.mov`
- **Named by prompt** otherwise: `Zeus_dragon_breathes_1747234567.mov`
- **Accompanied by a `.meta.json` sidecar** with full prompt, model, provider, seed, and source URL

### ffmpeg Post-Processing Tools

| Tool | Description |
|---|---|
| `veo_convert_video` | Lossless container rewrap — MP4↔MOV, no re-encode |
| `veo_resize_video` | Scale to exact game dimensions (fill/fit/stretch); ProRes, H.264, or H.265 |

These use the same ffmpeg binary auto-installed on first video generation. No extra setup.
**Resize fit modes:** fill (scale+crop, best for game assets), fit (letterbox), stretch (distort)

---

## Install via the H5G Marketplace

The easiest way to install this plugin — along with the slot art creator and skill auditor — is through the shared High 5 Games marketplace:

```
/plugin marketplace add https://github.com/michaelericksonh5/claude-plugins
/plugin install ai-video-generator@h5g-plugins
```

---

## Set up your API keys

After installing, run the setup script once from a terminal in the plugin directory:

**Windows (PowerShell):**
```powershell
.\setup-key.ps1
```

**Mac / Linux:**
```bash
./setup-key.sh
```

The script writes your keys to `~/.claude/settings.json` under the `"env"` key — the official Claude Code mechanism for plugin keys. Keys written there are automatically shared across every plugin in the H5G marketplace. If you already set `FAL_KEY` or `GEMINI_API_KEY` through the slot art creator setup, you're already done.

**fal.ai key:** https://fal.ai/dashboard/keys — supports all models (Veo 3.1, Happy Horse, Seedance 2.0)
**Gemini key:** https://aistudio.google.com/app/apikey — Veo 3.1 only; requires the paid Gemini API tier

> **Security:** Never paste your API key into Claude's chat. The setup script uses hidden input so your key is never visible on screen.

---

## Usage

Just talk to Claude naturally:

- *"Make an 8-second cinematic video of a wolf running through a snowy forest"*
- *"Animate this photo"* (drop an image)
- *"Generate a video that starts with [image1] and ends with [image2]"*
- *"Extend this video: [URL]"*
- *"Use Happy Horse to animate my portrait"*
- *"Make a Seedance video with my character reference"*
- *"Animate the HP1 symbol as an idle animation"* (auto-named `HP1_idle_*.mov`)
- *"Resize this video to 1280 by 852"*
- *"Convert this MP4 to MOV losslessly"*

Claude will ask for any missing details and guide you through the process.

---

## Available MCP Tools

| Tool | Description |
|---|---|
| `veo_check_api_keys` | Check which keys are configured (never shows key values) |
| `veo_setup_api_key` | Get safe setup instructions for fal.ai or Gemini |
| `veo_upload_file` | Upload a local image/video to fal.ai storage |
| `veo_generate_video` | Text → video (Veo 3.1) |
| `veo_image_to_video` | Image → video (Veo 3.1) |
| `veo_first_last_frame_to_video` | Two frames → video (Veo 3.1) |
| `veo_reference_to_video` | Reference images → video (Veo 3.1) |
| `veo_extend_video` | Extend an existing video (Veo 3.1) |
| `veo_happy_horse_image_to_video` | Image → video (Happy Horse / Alibaba) |
| `veo_happy_horse_reference_to_video` | Reference images → video (Happy Horse / Alibaba) |
| `veo_seedance_image_to_video` | Image → video with optional end frame (Seedance 2.0) |
| `veo_seedance_reference_to_video` | Multi-modal reference → video (Seedance 2.0) |
| `veo_convert_video` | Lossless container rewrap (MP4↔MOV, no re-encode) |
| `veo_resize_video` | Scale to exact pixel dimensions (fill/fit/stretch, ProRes/H.264/H.265) |

---

## License

MIT — built by [@michaelericksonh5](https://github.com/michaelericksonh5)
