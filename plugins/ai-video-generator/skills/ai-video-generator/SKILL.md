---
name: ai-video-generator
description: >
  AI video generation for Claude using Veo 3.1, Happy Horse (Alibaba), and Seedance 2.0 (ByteDance)
  via fal.ai or Google Gemini. Use this skill whenever a user wants to CREATE or GENERATE a video
  using AI -- from a text prompt, by animating an image, transitioning between two frames, using
  reference images for character consistency, or extending an existing video clip.

  Trigger on ANY of these:
  - "make a video", "generate a video", "create a video clip", "produce a video"
  - "animate this image/photo", "make my photo move", "bring this image to life"
  - "animate between these two images", "start with X end with Y", "morph between"
  - "extend this video", "continue this clip", "make it longer", "add more footage"
  - "use this as a reference image", "keep the character consistent", "same character in a video"
  - "Veo", "Veo 3.1", "fal.ai video", "Gemini video", "text to video", "image to video"
  - "Happy Horse", "Alibaba video model", "animate my portrait"
  - "Seedance", "ByteDance video", "Seedance 2.0"
  - "how do I set up my fal.ai key", "configure my Gemini key for video"
  - User drops/uploads an image file and asks for any kind of animation or video

  Do NOT trigger for: video editing (subtitles, captions, compression, ffmpeg, format conversion,
  trimming, merging), video transcription or captioning, generating still images only, research
  questions about comparing video models, or downloading/streaming existing videos.
---

# AI Video Generator Skill

Orchestrates AI video generation across 9 model endpoints and 3 providers. Handles the full
workflow: check keys -> upload files if needed -> clarify only what's missing -> generate -> return URL.

## The 9 Available Models

| Model | When to use | Provider |
|---|---|---|
| Veo 3.1 text-to-video | Any scene from a text prompt, dialogue, cinematic shots | fal.ai or Gemini |
| Veo 3.1 image-to-video | Animate a photo as the first frame | fal.ai or Gemini |
| Veo 3.1 first+last frame | Transition/morph between exactly two images | fal.ai or Gemini |
| Veo 3.1 reference-to-video | Keep a specific character/subject consistent | fal.ai or Gemini |
| Veo 3.1 extend-video | Continue/lengthen an existing video clip | fal.ai ONLY |
| Happy Horse image-to-video | Animate a portrait, product, lifestyle photo (up to 15s, 1080p) | fal.ai ONLY |
| Happy Horse reference-to-video | Multi-character scenes, up to 9 reference images | fal.ai ONLY |
| Seedance 2.0 image-to-video | Image to video with optional end frame + native audio (up to 15s) | fal.ai ONLY |
| Seedance 2.0 reference-to-video | Multi-modal refs: combine images + video clips + audio samples | fal.ai ONLY |

## Step 1: Check Keys (Always First)

Call `veo_check_api_keys` before anything else.

If `active_provider === "none"`:
- Ask: "Do you have a fal.ai key or a Google Gemini key?" then call `veo_setup_api_key` with the chosen provider and show the instructions
- Do not attempt generation


## Setup Scripts (Fastest Key Configuration)

Two scripts ship with the plugin for secure, no-paste key setup. Point users to these when they have no key configured.

**Windows (PowerShell):**
```powershell
cd "C:\Users\[you]\Documents\Claude_Plugins\ai-video-mcp-server"
.\setup-key.ps1              # fal.ai key (default)
.\setup-key.ps1 -Provider gemini  # Gemini key
.\setup-key.ps1 -Provider both    # Both keys
```

**Mac/Linux (Terminal):**
```bash
cd ~/Documents/Claude_Plugins/ai-video-mcp-server
bash setup-key.sh fal     # fal.ai key
bash setup-key.sh gemini  # Gemini key
bash setup-key.sh both    # Both keys
```

The script uses secure input (key never displayed), writes directly to the Claude Desktop config, and clears the key from memory. After running it, the user restarts Claude Desktop and the MCP server is ready.


## Step 2: Handle File Uploads

If the user has dropped or mentioned a local file:
- Call `veo_upload_file` with the absolute path
- Tell the user: "Uploading your file..." then use the returned URL in the generation call
- If the path doesn't work: ask them to right-click the file and copy the full path

If the user gives a public https:// URL, use it directly -- no upload needed.

## Step 3: Choose the Right Model

Use the most specific match for what the user described:

```
Has local/dropped image + wants it animated?
  -> Upload first, then veo_image_to_video (or Happy Horse if they mention portrait/product)

Has TWO images and wants a transition?
  -> veo_first_last_frame_to_video OR veo_seedance_image_to_video (has end_image_url)

Has reference images for character consistency?
  -> veo_reference_to_video (up to 3 refs, Veo) or veo_happy_horse_reference_to_video (up to 9 refs)

Has reference images + video clips + audio together?
  -> veo_seedance_reference_to_video (most powerful multi-modal option)

Has an existing video to extend?
  -> veo_extend_video (fal.ai key required)

Just a text prompt, no images?
  -> veo_generate_video

Mentions "Happy Horse" or wants long animation (>8s) or portrait style?
  -> veo_happy_horse_image_to_video

Mentions "Seedance" or ByteDance or wants native audio sync?
  -> veo_seedance_image_to_video or veo_seedance_reference_to_video
```

## Step 4: Clarify Only What's Truly Missing

Ask at most 2 questions in one message. Never interrogate the user with a long list.

Essential (block generation if missing):
- Image tools: need the image URL/file
- Extend video: need the video URL/file
- Happy Horse reference / Seedance reference: need at least one reference URL

Smart defaults (use these, don't ask):
- Resolution: 720p (ask only if they say "4K", "high quality", or "best quality")
- Aspect ratio: 16:9 (ask only if content is clearly portrait/vertical)
- Duration: 8s for Veo, 5s for Happy Horse, auto for Seedance (ask only if they want specific)
- Audio: ON by default (ask only if they mention "no sound", "silent", "music over it")
- Provider: auto (ask only if they specifically name fal.ai or Gemini)
- safety_tolerance: always 4 (never ask)
- seed: omit unless they ask for reproducibility

## Step 5: Generate and Track Progress

Before calling the tool: "Generating your video -- this takes 2-5 minutes for Veo 3.1, up to 2 min for Happy Horse/Seedance. I'll share the link as soon as it's ready."

When done, return:
1. The video URL as a clickable link, prominently
2. Model used + resolution + duration
3. One sentence about what was generated

## Prompting Guidance

If the user's prompt is vague (e.g. "make a cool video"), help them improve it. A strong prompt has:
- Subject: what/who is in it
- Context: the background or setting
- Action: what is happening
- Style: cinematic, noir, cartoon, anime, documentary, horror, etc.
- Camera (optional): aerial, tracking shot, close-up, slow motion
- Ambiance (optional): golden hour, neon-lit, foggy, raining

For dialogue or speech, put it in quotes directly in the prompt:
> A reporter on the street says: "Breaking news -- the plugin is live."

For Happy Horse multi-character: remind user to use character1, character2 etc. in prompt
For Seedance reference-to-video: remind user to use @Image1, @Video1, @Audio1 in prompt

## Error Handling -- Actionable Guidance for Every Failure

**No API key configured**
- Call `veo_setup_api_key` with provider=fal or provider=gemini
- Show the full instructions that come back
- Do not just say "you need a key" -- actually give them the steps

**FAL_KEY wrong or expired**
- "Your fal.ai key seems invalid or expired. Go to https://fal.ai/dashboard/keys, create a new key, and update your Claude Desktop config's env block with the new value."

**GEMINI_API_KEY wrong or invalid**
- "Your Gemini key seems invalid. Go to https://aistudio.google.com/app/apikey, copy a fresh key, and update your Claude Desktop config."

**Video extension attempted with Gemini key**
- "Video extension is not supported with Gemini API keys -- it requires Google Cloud Storage and Vertex AI credentials. To extend videos, you need a fal.ai key (https://fal.ai/dashboard/keys). fal.ai handles the Vertex AI connection for you."

**Safety filter blocked the prompt (fal.ai)**
- "The content filter blocked that prompt. Try rephrasing to remove [specific problematic element]. The safety_tolerance is set to 4 by default -- the content policy applies regardless."

**Image format not accepted**
- Veo: "Image must be JPEG, PNG, or WebP, 720p or higher, max 8MB, in 16:9 or 9:16 ratio."
- Happy Horse: "Image must be JPEG, JPG, PNG, BMP, or WEBP, at least 300x300px, aspect ratio between 1:2.5 and 2.5:1, max 10MB."
- Seedance: "Image must be JPEG, PNG, or WebP, max 30MB."

**File path not found**
- "I couldn't find that file path. Try: right-click the file in Explorer/Finder -> 'Copy as path' (Windows) or hold Option and right-click -> 'Copy as Pathname' (Mac), then paste it here."

**Request timed out / no result after polling**
- "The generation timed out -- this can happen when the API is under heavy load. Your request may still be processing. Try again in a few minutes, or try with a shorter duration or lower resolution to speed things up."

**Rate limit hit (fal.ai)**
- "You've hit fal.ai's rate limit. Wait 60 seconds and try again. If this keeps happening, check your usage at https://fal.ai/dashboard."

**Gemini API 400/403 errors**
- 400: "The request format was rejected by Gemini. This may be a temporary API issue -- try again. If it persists, switching to fal.ai (FAL_KEY) is more reliable for this feature."
- 403: "Your Gemini key doesn't have access to Veo 3.1. This model requires the paid Gemini API tier. Check your billing at https://aistudio.google.com."

**"No video URL in response"**
- "The generation completed but didn't return a video URL -- this is a rare API glitch. Try generating again with the same prompt."

## Per-Model Quick Reference

**veo_generate_video** -- text prompt only, no images
- Key params: prompt, aspect_ratio (16:9/9:16), duration (4s/6s/8s), resolution (720p/1080p/4k)
- Supports dialogue and audio natively

**veo_image_to_video** -- one starting image
- Key params: prompt (how to animate it), image_url, aspect_ratio (auto/16:9/9:16)
- Gemini will fetch and inline the image automatically

**veo_first_last_frame_to_video** -- two images, model fills the middle
- Key params: prompt (describe the transition), first_frame_url, last_frame_url
- Great for morphs, transitions, scene changes

**veo_reference_to_video** -- 1-3 images for character/style consistency
- Key params: prompt, image_urls (array of 1-3)
- The model keeps the subject's appearance consistent throughout

**veo_extend_video** -- adds footage to an existing video
- Key params: prompt (how to continue), video_url
- fal.ai ONLY -- Gemini key users cannot use this feature
- Input: max 8 seconds, 720p/1080p, 16:9 or 9:16

**veo_happy_horse_image_to_video** -- Alibaba model, great for portraits
- Key params: image_url, prompt (optional), resolution (720p/1080p), duration (3-15)
- Image: 300px+ min, aspect ratio 1:2.5 to 2.5:1, max 10MB

**veo_happy_horse_reference_to_video** -- Alibaba, up to 9 character refs
- Key params: prompt (use character1, character2...), image_urls (1-9)
- Aspect ratios: 16:9, 9:16, 1:1, 4:3, 3:4

**veo_seedance_image_to_video** -- ByteDance, native audio, optional end frame
- Key params: prompt, image_url, end_image_url (optional), resolution (480p/720p/1080p), duration (auto or 4-15)
- Aspect ratios: auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16

**veo_seedance_reference_to_video** -- ByteDance, multi-modal refs
- Key params: prompt (use @Image1, @Video1, @Audio1...), image_urls, video_urls, audio_urls
- Limits: up to 9 images, 3 videos (combined 2-15s), 3 audio files (combined max 15s)
