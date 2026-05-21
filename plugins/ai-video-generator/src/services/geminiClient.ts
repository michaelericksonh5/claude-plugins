/**
 * Google Gemini Veo 3.1 client using the REST API directly.
 * Uses long-running operations with polling (no persistent SDK session needed).
 */

import {
  GEMINI_API_BASE,
  GEMINI_MODEL,
  GEMINI_POLL_INTERVAL_MS,
  GEMINI_MAX_POLL_ATTEMPTS,
} from "../constants.js";
import type { VideoGenerationResult, GeminiVideoOperation } from "../types.js";

async function geminiPost(
  path: string,
  body: unknown,
  apiKey: string
): Promise<unknown> {
  const url = `${GEMINI_API_BASE}/${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-goog-api-key": apiKey,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Gemini API error ${res.status}: ${err}`);
  }
  return res.json();
}

async function geminiGet(path: string, apiKey: string): Promise<unknown> {
  const url = `${GEMINI_API_BASE}/${path}`;
  const res = await fetch(url, {
    headers: { "x-goog-api-key": apiKey },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Gemini API error ${res.status}: ${err}`);
  }
  return res.json();
}

async function pollOperation(
  operationName: string,
  apiKey: string
): Promise<GeminiVideoOperation> {
  for (let attempt = 0; attempt < GEMINI_MAX_POLL_ATTEMPTS; attempt++) {
    await new Promise((r) => setTimeout(r, GEMINI_POLL_INTERVAL_MS));
    const status = (await geminiGet(operationName, apiKey)) as GeminiVideoOperation;
    process.stderr.write(`[gemini] Polling... attempt ${attempt + 1}, done: ${status.done ?? false}\n`);
    if (status.error) {
      throw new Error(`Gemini generation failed: ${status.error.message}`);
    }
    if (status.done) return status;
  }
  throw new Error("Gemini video generation timed out after 10 minutes.");
}

function extractGeminiVideo(op: GeminiVideoOperation, model: string): VideoGenerationResult {
  // Try modern SDK response shape first, then REST shape
  const modernVideo = op.response?.generatedVideos?.[0]?.video?.uri;
  const restVideo = op.response?.generateVideoResponse?.generatedSamples?.[0]?.video?.uri;
  const videoUrl = modernVideo ?? restVideo;

  if (!videoUrl) {
    throw new Error("Gemini returned no video URL in the operation response.");
  }

  return {
    provider: "gemini",
    model,
    video: { url: videoUrl },
    request_id: op.name,
  };
}

// ─── Gemini Text-to-Video ───────────────────────────────────────────────────
export async function geminiTextToVideo(
  apiKey: string,
  params: {
    prompt: string;
    aspect_ratio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    duration_seconds?: number;
    negative_prompt?: string;
    seed?: number;
  }
): Promise<VideoGenerationResult> {
  const videoConfig: Record<string, unknown> = {};
  if (params.aspect_ratio) videoConfig["aspectRatio"] = params.aspect_ratio;
  if (params.resolution) videoConfig["resolution"] = params.resolution;
  if (params.duration_seconds) videoConfig["durationSeconds"] = params.duration_seconds;
  if (params.negative_prompt) videoConfig["negativePrompt"] = params.negative_prompt;
  if (params.seed !== undefined) videoConfig["seed"] = params.seed;

  const body: Record<string, unknown> = {
    model: GEMINI_MODEL,
    prompt: params.prompt,
  };
  if (Object.keys(videoConfig).length > 0) body["config"] = videoConfig;

  const op = (await geminiPost(
    `models/${GEMINI_MODEL}:predictLongRunning`,
    body,
    apiKey
  )) as GeminiVideoOperation;

  const completed = await pollOperation(op.name, apiKey);
  return extractGeminiVideo(completed, GEMINI_MODEL);
}

// ─── Gemini Image-to-Video ──────────────────────────────────────────────────
export async function geminiImageToVideo(
  apiKey: string,
  params: {
    prompt: string;
    image_url?: string;
    image_base64?: string;
    image_mime_type?: string;
    aspect_ratio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    duration_seconds?: number;
    negative_prompt?: string;
    seed?: number;
  }
): Promise<VideoGenerationResult> {
  const videoConfig: Record<string, unknown> = {};
  if (params.aspect_ratio) videoConfig["aspectRatio"] = params.aspect_ratio;
  if (params.resolution) videoConfig["resolution"] = params.resolution;
  if (params.duration_seconds) videoConfig["durationSeconds"] = params.duration_seconds;
  if (params.negative_prompt) videoConfig["negativePrompt"] = params.negative_prompt;
  if (params.seed !== undefined) videoConfig["seed"] = params.seed;

  // Build image part
  let imagePart: Record<string, unknown>;
  if (params.image_url) {
    // Fetch and convert URL to base64 for Gemini
    const res = await fetch(params.image_url);
    const buf = await res.arrayBuffer();
    const b64 = Buffer.from(buf).toString("base64");
    const mime = res.headers.get("content-type") ?? params.image_mime_type ?? "image/jpeg";
    imagePart = { inlineData: { mimeType: mime, data: b64 } };
  } else if (params.image_base64 && params.image_mime_type) {
    imagePart = { inlineData: { mimeType: params.image_mime_type, data: params.image_base64 } };
  } else {
    throw new Error("Provide either image_url or both image_base64 and image_mime_type.");
  }

  const body: Record<string, unknown> = {
    model: GEMINI_MODEL,
    prompt: params.prompt,
    image: imagePart,
  };
  if (Object.keys(videoConfig).length > 0) body["config"] = videoConfig;

  const op = (await geminiPost(
    `models/${GEMINI_MODEL}:predictLongRunning`,
    body,
    apiKey
  )) as GeminiVideoOperation;

  const completed = await pollOperation(op.name, apiKey);
  return extractGeminiVideo(completed, GEMINI_MODEL);
}

// ─── Gemini First+Last Frame to Video ───────────────────────────────────────
export async function geminiFirstLastFrameToVideo(
  apiKey: string,
  params: {
    prompt: string;
    first_frame_url?: string;
    first_frame_base64?: string;
    last_frame_url?: string;
    last_frame_base64?: string;
    image_mime_type?: string;
    aspect_ratio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    duration_seconds?: number;
    negative_prompt?: string;
    seed?: number;
  }
): Promise<VideoGenerationResult> {
  async function urlToBase64(url: string): Promise<{ data: string; mime: string }> {
    const res = await fetch(url);
    const buf = await res.arrayBuffer();
    return {
      data: Buffer.from(buf).toString("base64"),
      mime: res.headers.get("content-type") ?? params.image_mime_type ?? "image/jpeg",
    };
  }

  const videoConfig: Record<string, unknown> = {};
  if (params.aspect_ratio) videoConfig["aspectRatio"] = params.aspect_ratio;
  if (params.resolution) videoConfig["resolution"] = params.resolution;
  if (params.duration_seconds) videoConfig["durationSeconds"] = params.duration_seconds;
  if (params.negative_prompt) videoConfig["negativePrompt"] = params.negative_prompt;
  if (params.seed !== undefined) videoConfig["seed"] = params.seed;

  let firstImg: { data: string; mime: string };
  if (params.first_frame_url) firstImg = await urlToBase64(params.first_frame_url);
  else if (params.first_frame_base64) firstImg = { data: params.first_frame_base64, mime: params.image_mime_type ?? "image/jpeg" };
  else throw new Error("Provide first_frame_url or first_frame_base64.");

  let lastImg: { data: string; mime: string } | undefined;
  if (params.last_frame_url) lastImg = await urlToBase64(params.last_frame_url);
  else if (params.last_frame_base64) lastImg = { data: params.last_frame_base64, mime: params.image_mime_type ?? "image/jpeg" };

  const body: Record<string, unknown> = {
    model: GEMINI_MODEL,
    prompt: params.prompt,
    image: { inlineData: { mimeType: firstImg.mime, data: firstImg.data } },
  };
  if (lastImg) {
    body["lastFrame"] = { inlineData: { mimeType: lastImg.mime, data: lastImg.data } };
  }
  if (Object.keys(videoConfig).length > 0) body["config"] = videoConfig;

  const op = (await geminiPost(
    `models/${GEMINI_MODEL}:predictLongRunning`,
    body,
    apiKey
  )) as GeminiVideoOperation;

  const completed = await pollOperation(op.name, apiKey);
  return extractGeminiVideo(completed, GEMINI_MODEL);
}

// ─── Gemini Reference Images to Video ───────────────────────────────────────
export async function geminiReferenceToVideo(
  apiKey: string,
  params: {
    prompt: string;
    image_urls: string[];
    aspect_ratio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    duration_seconds?: number;
    negative_prompt?: string;
    seed?: number;
  }
): Promise<VideoGenerationResult> {
  // Fetch and inline all reference images
  const referenceImages = await Promise.all(
    params.image_urls.map(async (url) => {
      const res = await fetch(url);
      const buf = await res.arrayBuffer();
      const mime = res.headers.get("content-type") ?? "image/jpeg";
      return { inlineData: { mimeType: mime, data: Buffer.from(buf).toString("base64") } };
    })
  );

  const videoConfig: Record<string, unknown> = {};
  if (params.aspect_ratio) videoConfig["aspectRatio"] = params.aspect_ratio;
  if (params.resolution) videoConfig["resolution"] = params.resolution;
  if (params.duration_seconds) videoConfig["durationSeconds"] = params.duration_seconds;
  if (params.negative_prompt) videoConfig["negativePrompt"] = params.negative_prompt;
  if (params.seed !== undefined) videoConfig["seed"] = params.seed;

  const body: Record<string, unknown> = {
    model: GEMINI_MODEL,
    prompt: params.prompt,
    referenceImages,
  };
  if (Object.keys(videoConfig).length > 0) body["config"] = videoConfig;

  const op = (await geminiPost(
    `models/${GEMINI_MODEL}:predictLongRunning`,
    body,
    apiKey
  )) as GeminiVideoOperation;

  const completed = await pollOperation(op.name, apiKey);
  return extractGeminiVideo(completed, GEMINI_MODEL);
}

// ─── Gemini Video Extension ──────────────────────────────────────────────────
// NOTE: Gemini API video extension via REST (API key auth) is NOT currently supported.
// Extension requires:
//   1. Google Cloud Storage (GCS) URIs — regular URLs don't work
//   2. Vertex AI with OAuth2 service account (not Gemini API keys)
//   3. An allowlist approval from Google for veo-3.1 extension
// Source: https://discuss.ai.google.dev/t/veo-3-1-rest-api-no-struct-value-found-error/107935
//
// Use fal.ai (FAL_KEY) for video extension — it wraps Vertex AI behind the scenes
// and is the recommended path for Gemini API key users.
export async function geminiExtendVideo(
  _apiKey: string,
  _params: {
    prompt: string;
    video_url: string;
    resolution?: "720p";
    negative_prompt?: string;
    seed?: number;
  }
): Promise<VideoGenerationResult> {
  throw new Error(
    "Video extension is not available via the Gemini REST API with an API key.\n\n" +
    "Reasons:\n" +
    "  - Extension requires Google Cloud Storage (GCS) URIs, not regular URLs\n" +
    "  - Extension requires Vertex AI with OAuth2 service account auth (not Gemini API keys)\n" +
    "  - Veo 3.1 extension requires a Google allowlist approval\n\n" +
    "Solution: Use a fal.ai key (FAL_KEY) instead - it handles Vertex AI behind the scenes.\n" +
    "Get a fal.ai key at https://fal.ai/dashboard/keys, then run veo_setup_api_key with provider=fal."
  );
}
