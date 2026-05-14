---
name: ai-video-generator
description: >
  AI video generation for Claude using Veo 3.1, Happy Horse (Alibaba), and Seedance 2.0 (ByteDance)
  via fal.ai or Google Gemini. Use this skill whenever a user wants to CREATE or GENERATE a video
  using AI -- from a text prompt, by animating an image, transitioning between two frames, using
  reference images for character consistency, or extending an existing video clip.

  DEFAULT CONTEXT: All generation is for slot machine game content (animations, symbol reveals,
  win celebrations, bonus sequences, background loops, lobby trailers) unless the user explicitly
  says otherwise. Every prompt and parameter choice must reflect casino game production standards.

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
  - "win animation", "spin reveal", "bonus trigger", "symbol animation", "reel transition"
  - "lobby video", "loading screen animation", "jackpot sequence"

  Do NOT trigger for: video editing (subtitles, captions, compression, ffmpeg, format conversion,
  trimming, merging), video transcription or captioning, generating still images only, research
  questions about comparing video models, or downloading/streaming existing videos.
---

# AI Video Generator Skill

Orchestrates AI video generation across 9 model endpoints and 3 providers. Handles the full
workflow: check keys → upload files if needed → clarify only what's missing → generate → return URL.

**Default context:** This plugin operates in a slot machine game production environment. Unless
the user explicitly says otherwise, assume all content is for casino game use — symbols, win
animations, bonus sequences, background loops, character reveals, lobby trailers, etc. Apply
appropriate style guidance automatically.

## The 9 Available Models

| Model | Best for slot game use | Provider |
|---|---|---|
| Veo 3.1 text-to-video | Win celebrations, bonus intros, cinematic trailers, ambient loops | fal.ai or Gemini |
| Veo 3.1 image-to-video | Animate a symbol or key art as the first frame | fal.ai or Gemini |
| Veo 3.1 first+last frame | Reel-stop reveals, morph between two states | fal.ai or Gemini |
| Veo 3.1 reference-to-video | Keep a specific character consistent across a sequence | fal.ai or Gemini |
| Veo 3.1 extend-video | Continue/extend an existing game animation | fal.ai ONLY |
| Happy Horse image-to-video | Animate a character portrait (up to 15s, 1080p) | fal.ai ONLY |
| Happy Horse reference-to-video | Multi-character scenes, up to 9 reference images | fal.ai ONLY |
| Seedance 2.0 image-to-video | Image to video with optional end frame + native audio (up to 15s) | fal.ai ONLY |
| Seedance 2.0 reference-to-video | Multi-modal refs: combine images + video clips + audio samples | fal.ai ONLY |

---

## Step 1: Check Keys (Always First)

Call `veo_check_api_keys` before anything else.

### Interpreting the result

`active_provider === "none"` means **no valid key is configured**. This is the definitive check —
do not attempt generation.

> **Important:** Claude Code may inject placeholder values (empty strings or `${VAR_NAME}` patterns)
> for keys not yet configured. The MCP server filters these out automatically — if `active_provider`
> is "none", the key genuinely is not set, even if you think it might be.

If `active_provider === "none"`, ask: "Do you have a fal.ai key, a Google Gemini key, or neither?"

- **fal.ai key** — gives access to all 9 models. Get one at https://fal.ai/dashboard/keys
- **Gemini key** — gives access to Veo 3.1 (text, image, first/last, reference). Get one at https://aistudio.google.com/app/apikey

### Setting up keys — always use the setup script

Point users to the setup script. It writes directly to `~/.claude/settings.json` (the shared key
store for all H5G Claude plugins — set once, works everywhere).

**Locate the script first** — use the Glob tool to find it:
```
~/.claude/plugins/marketplaces/h5g-plugins/plugins/ai-video-generator/setup-keys.mjs
```
On Windows that expands to:
```
C:\Users\<username>\.claude\plugins\marketplaces\h5g-plugins\plugins\ai-video-generator\setup-keys.mjs
```

**Run it:**
```powershell
node "<full path to setup-keys.mjs>" --check   # verify current status
node "<full path to setup-keys.mjs>" --fal     # add fal.ai key
node "<full path to setup-keys.mjs>" --gemini  # add Gemini key
node "<full path to setup-keys.mjs>" --both    # add both
```

After running the script, **restart Claude Code** so the new key is picked up by the MCP server.

Do not manually edit `settings.json` unless you know what you're doing. The script handles the
correct JSON structure and validates the key before saving.

---

## Step 2: Handle File Uploads

If the user has dropped or mentioned a local file:
- Call `veo_upload_file` with the absolute path
- Tell the user: "Uploading your file..." then use the returned URL in the generation call
- If the path doesn't work: ask them to right-click the file and copy the full path

If the user gives a public https:// URL, use it directly — no upload needed.

---

## Step 3: Choose the Right Model

Use the most specific match:

```
Has local/dropped image + wants it animated?
  → Upload first, then veo_image_to_video
  → Or Happy Horse if subject is a character portrait/bust

Has TWO images and wants a transition/reveal?
  → veo_first_last_frame_to_video (Veo morph)
  → Or veo_seedance_image_to_video with end_image_url (Seedance has native audio)

Has reference images for character consistency?
  → veo_reference_to_video (up to 3 refs) or veo_happy_horse_reference_to_video (up to 9 refs)

Has reference images + video clips + audio samples together?
  → veo_seedance_reference_to_video (most powerful multi-modal option)

Has an existing video clip to extend?
  → veo_extend_video (fal.ai key required)

Just a text prompt, no images?
  → veo_generate_video

Wants long animation (>8s) or portrait/character style?
  → veo_happy_horse_image_to_video (up to 15s)

Mentions "Seedance" or wants native audio sync?
  → veo_seedance_image_to_video or veo_seedance_reference_to_video
```

---

## Step 4: Clarify Only What's Truly Missing

Ask at most 2 questions in one message. Never interrogate the user.

**Essential (block generation if missing):**
- Image tools: need the image URL/file
- Extend video: need the video URL/file
- Happy Horse reference / Seedance reference: need at least one reference URL

**Smart defaults (use these, don't ask):**
- Resolution: 720p
- Aspect ratio: 16:9 (ask only if content is clearly portrait/vertical)
- Duration: 8s for Veo, 5s for Happy Horse, auto for Seedance
- Audio: ON by default
- Provider: auto (fal.ai first, Gemini fallback)
- safety_tolerance: always 4
- seed: omit unless reproducibility requested

---

## Step 5: Generate and Return

Before calling the tool: "Generating your video — this takes 2–5 min for Veo 3.1, up to 2 min for Happy Horse/Seedance. I'll share the link as soon as it's ready."

When done, return:
1. The video URL as a clickable link
2. Model used + resolution + duration
3. One sentence about what was generated

---

## Prompting for Slot Game Content

**This is the core discipline for slot machine game video generation.**

### Default style framing

When the user doesn't specify a style, use this framing adapted to the game's theme:

```
Slot machine game animation, premium casino production quality, bold and vivid colors,
clean graphic forms optimized for mobile display, [theme] aesthetic.
Not photorealistic. No UI chrome, no text overlays, no reel frame unless specified.
```

The key constraint: **not photorealistic** for game symbols and character reveals. Photorealism
is only appropriate for cinematic trailers or marketing hero shots — not for reel-cell animations.

### Per-model prompting best practices

#### Veo 3.1 (text-to-video, image-to-video, first/last frame, reference, extend)

Veo 3.1 understands cinematic language and responds to:
- **Camera moves:** "slow push in on the symbol", "aerial establishing shot", "tracking shot",
  "close-up on the character's face", "pull back to reveal the reel"
- **Timing language:** "smooth 8-second loop", "quick 2-second burst", "slow-motion cascade"
- **Lighting directives:** "warm golden light from upper left", "dramatic rim lighting",
  "volumetric light rays breaking through", "cool blue ambient with gold accent glints"
- **Physics:** "coins shower down", "particles swirl outward", "energy pulses radiate"

**For slot game use — strong Veo 3.1 prompt structure:**
```
[Shot type + camera move]. [Subject description] — [style phrase].
[Lighting setup]. [Action in 1–2 sentences].
[Loop/end behavior if relevant]. Casino game animation quality.
```

Example — jackpot reveal:
```
Slow push in, camera holding on center frame. A glowing golden Zeus symbol
surrounded by crackling lightning bolts — epic mythology slot art, oil-glazed highlights.
Warm gold volumetric rays burst outward from the symbol, electric arcs spiral upward.
Ends with a sustained glow pulse. Casino game animation, premium mobile quality.
```

Example — background ambient loop:
```
Aerial shot slowly drifting left over a moonlit ancient Greek temple complex at night.
Torches flicker in the courtyard, light reflecting on marble columns.
Stylized semi-realistic slot game art, cool blue night sky with warm torch glow.
8-second seamless loop. No characters, no UI.
```

#### GPT-Image-2 (for still frames before animating)

gpt-image-2 is exposed via the slot-art plugin (not here), but when you need a high-quality
still to feed into a Veo or Seedance generation, remember:
- Use gpt-image-2 for any still that needs **accurate text** (win banners, lobby tiles, paytable frames)
- Use gpt-image-2 at **2K** for marketing-quality hero frames
- Pass the resulting image as the source for `veo_image_to_video` or `veo_first_last_frame_to_video`
- Always prefix the gpt-image-2 prompt with a **style lock** sentence:
  "Painted CG, soft volumetric lighting, mobile slot game art, not photorealistic."

#### Seedance 2.0

Seedance 2.0 excels at:
- **Native audio sync** — sound effects and ambient audio are generated alongside the video
- **End-frame transitions** — specify `end_image_url` to create a smooth morph between two states
- **Multi-modal reference assembly** — use @Image1, @Image2, @Video1, @Audio1 in the prompt body

**For slot game use — Seedance 2.0 prompt structure:**
```
@Image1 [describe reference role]. [Action description].
[Audio directive if needed: "with rising orchestral swell", "coin clinking sound effects",
"silence", "ambient casino background"].
Slot machine game animation style. [Duration and aspect hints if needed].
```

Example — symbol reveal with audio:
```
@Image1 is the key art — the golden dragon symbol for the HP1 reel symbol.
The dragon breathes a burst of golden flame directly toward camera.
Coins cascade down around it. Rising orchestral fanfare with metallic coin clinks.
Slot machine game, bold cinematic style, 6 seconds.
```

**Seedance audio guidance:**
- Default to ambient audio ON for trailers and lobby videos
- For reel symbol animations, prefer `audio: false` (game engine handles sound)
- For win celebrations and jackpot sequences, audio ON with coin/fanfare description in prompt

#### Happy Horse (Alibaba happyhorse-1.0-i2v)

Happy Horse specializes in bringing portraits and character images to life with natural motion.

**Best for slot game use:**
- Animating a HP character symbol (bust or 3/4 portrait)
- Creating a character idle animation for lobby screens
- Multi-character interaction scenes (reference mode, up to 9 refs)

**Prompting discipline for Happy Horse:**
- The image provides the character — the prompt directs **motion only**
- Keep prompts short and motion-focused: "The character smiles and turns slightly, golden
  light playing across their features"
- For multi-character: "character1 gestures welcomingly toward character2, both in idle stance"
- Avoid over-describing the character's appearance — that's already locked in the reference image
- Use `resolution: "1080p"` for production-quality character animations
- Duration 5–8s is the sweet spot; 10–15s for extended idle loops

**Example — HP character idle:**
```
image_url: [approved HP1 symbol image]
prompt: "The character holds their regal pose, robes shifting gently, eyes scanning with quiet
authority. Subtle breathing motion. Warm golden ambient light."
resolution: "1080p"
duration: 8
```

**Example — multi-character greeting (reference mode):**
```
image_urls: [character1_image, character2_image]
prompt: "character1 raises their goblet in a toast toward character2, who nods approvingly.
Rich tavern atmosphere, warm firelight, idle celebratory energy."
resolution: "1080p"
duration: 6
```

---

## Error Handling — Actionable Guidance for Every Failure

**No API key configured (active_provider === "none")**
Show the exact setup script command above. Do not just say "you need a key" — give them the steps.

**FAL_KEY wrong or expired**
"Your fal.ai key seems invalid or expired. Go to https://fal.ai/dashboard/keys, create a new key,
then run: `node setup-keys.mjs --fal` and enter the new key. Restart Claude Code after."

**GEMINI_API_KEY wrong or invalid**
"Your Gemini key seems invalid. Go to https://aistudio.google.com/app/apikey, copy a fresh key,
then run: `node setup-keys.mjs --gemini`. Restart Claude Code after."

**Video extension attempted with Gemini key**
"Video extension requires a fal.ai key — Gemini extension requires Google Cloud Storage and
Vertex AI credentials not available through the standard API. Get a fal.ai key at
https://fal.ai/dashboard/keys and run `node setup-keys.mjs --fal`."

**Safety filter blocked the prompt (fal.ai)**
"The content filter blocked that prompt. Try rephrasing to remove [specific element].
The safety_tolerance is set to 4 — content policy applies regardless."

**Image format not accepted**
- Veo: JPEG, PNG, or WebP; 720p or higher; max 8MB; 16:9 or 9:16 ratio
- Happy Horse: JPEG, JPG, PNG, BMP, or WEBP; at least 300×300px; aspect ratio 1:2.5 to 2.5:1; max 10MB
- Seedance: JPEG, PNG, or WebP; max 30MB

**File path not found**
"Right-click the file in Explorer → 'Copy as path', then paste the path here."

**Request timed out**
"The generation timed out — try again in a few minutes, or reduce duration or resolution."

**Rate limit (fal.ai)**
"You've hit fal.ai's rate limit. Wait 60 seconds, then try again. Check usage at https://fal.ai/dashboard."

**Gemini 403**
"Your Gemini key doesn't have access to Veo 3.1 — this model requires the paid Gemini API tier.
Check billing at https://aistudio.google.com."

**"No video URL in response"**
"The generation completed but didn't return a URL — rare API glitch. Try generating again."

---

## Per-Model Quick Reference

**veo_generate_video** — text prompt, no images
- Slot use: win sequences, ambient loops, trailers, jackpot cutscenes
- Key params: prompt, aspect_ratio (16:9/9:16), duration (4s/6s/8s), resolution (720p/1080p/4k)
- Supports dialogue and audio natively

**veo_image_to_video** — one starting image
- Slot use: animate an approved symbol or key art
- Key params: prompt (describe the motion), image_url, aspect_ratio
- Gemini fetches the image inline automatically

**veo_first_last_frame_to_video** — two images, model fills the middle
- Slot use: reel-stop reveals, idle→celebrate state transition
- Key params: prompt (describe the transition), first_frame_url, last_frame_url

**veo_reference_to_video** — 1–3 images for subject consistency
- Slot use: character sequence with the same character appearing in multiple shots
- Key params: prompt, image_urls (array of 1–3)

**veo_extend_video** — continues an existing video
- Slot use: extend a winning animation or ambient loop
- Key params: prompt, video_url; fal.ai ONLY; input max 8s, 720p/1080p

**veo_happy_horse_image_to_video** — Alibaba, portrait animation
- Slot use: HP character idle animations, character reveals
- Key params: image_url, prompt (motion only), resolution (720p/1080p), duration (3–15)

**veo_happy_horse_reference_to_video** — Alibaba, up to 9 character refs
- Slot use: multi-character bonus screens, interactive character scenes
- Key params: prompt (use character1, character2...), image_urls (1–9)

**veo_seedance_image_to_video** — ByteDance, native audio, optional end frame
- Slot use: symbol reveals with sound, win transitions between two visual states
- Key params: prompt, image_url, end_image_url (optional), resolution (480p/720p/1080p), duration (auto or 4–15)

**veo_seedance_reference_to_video** — ByteDance, multi-modal refs
- Slot use: complex assembled sequences using approved art + existing clips + audio stems
- Key params: prompt (use @Image1, @Video1, @Audio1...), image_urls, video_urls, audio_urls
- Limits: up to 9 images, 3 videos (combined 2–15s), 3 audio files (combined max 15s)
