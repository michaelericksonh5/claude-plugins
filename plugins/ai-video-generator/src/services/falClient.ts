/**
 * fal.ai API client — wraps @fal-ai/client with typed helpers.
 * All requests use the queue-based polling approach for reliability.
 */

import { fal } from "@fal-ai/client";
import type { VideoGenerationResult, FalVideoOutput } from "../types.js";
import { FAL_MODELS } from "../constants.js";

let falConfigured = false;

export function configureFal(apiKey: string): void {
  if (!falConfigured) {
    fal.config({ credentials: apiKey });
    falConfigured = true;
  }
}

function extractVideoResult(data: FalVideoOutput, modelId: string, requestId: string): VideoGenerationResult {
  return {
    provider: "fal",
    model: modelId,
    video: {
      url: data.video.url,
      content_type: data.video.content_type,
      file_name: data.video.file_name,
      file_size: data.video.file_size,
      width: data.video.width,
      height: data.video.height,
      fps: data.video.fps,
      duration: data.video.duration,
      num_frames: data.video.num_frames,
    },
    seed: data.seed,
    request_id: requestId,
  };
}

function progressLogger(update: { status: string; logs?: Array<{ message: string }> }) {
  if (update.status === "IN_PROGRESS" && update.logs) {
    update.logs.forEach((log) => process.stderr.write(`[fal] ${log.message}\n`));
  }
}

// ─── Text-to-Video ──────────────────────────────────────────────────────────
export async function falTextToVideo(params: {
  prompt: string;
  aspect_ratio?: "16:9" | "9:16";
  duration?: "4s" | "6s" | "8s";
  negative_prompt?: string;
  resolution?: "720p" | "1080p" | "4k";
  generate_audio?: boolean;
  seed?: number;
  auto_fix?: boolean;
  safety_tolerance?: "1" | "2" | "3" | "4" | "5" | "6";
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.VEO_TEXT_TO_VIDEO, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.VEO_TEXT_TO_VIDEO, result.requestId);
}

// ─── Extend Video ───────────────────────────────────────────────────────────
export async function falExtendVideo(params: {
  prompt: string;
  video_url: string;
  aspect_ratio?: "auto" | "16:9" | "9:16";
  duration?: string;
  negative_prompt?: string;
  resolution?: string;
  generate_audio?: boolean;
  seed?: number;
  auto_fix?: boolean;
  safety_tolerance?: "1" | "2" | "3" | "4" | "5" | "6";
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.VEO_EXTEND_VIDEO, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.VEO_EXTEND_VIDEO, result.requestId);
}

// ─── First + Last Frame to Video ─────────────────────────────────────────────
export async function falFirstLastFrameToVideo(params: {
  prompt: string;
  first_frame_url: string;
  last_frame_url: string;
  aspect_ratio?: "auto" | "16:9" | "9:16";
  duration?: "4s" | "6s" | "8s";
  negative_prompt?: string;
  resolution?: "720p" | "1080p" | "4k";
  generate_audio?: boolean;
  seed?: number;
  auto_fix?: boolean;
  safety_tolerance?: "1" | "2" | "3" | "4" | "5" | "6";
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.VEO_FIRST_LAST_FRAME, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.VEO_FIRST_LAST_FRAME, result.requestId);
}

// ─── Image to Video ─────────────────────────────────────────────────────────
export async function falImageToVideo(params: {
  prompt: string;
  image_url: string;
  aspect_ratio?: "auto" | "16:9" | "9:16";
  duration?: "4s" | "6s" | "8s";
  negative_prompt?: string;
  resolution?: "720p" | "1080p" | "4k";
  generate_audio?: boolean;
  seed?: number;
  auto_fix?: boolean;
  safety_tolerance?: "1" | "2" | "3" | "4" | "5" | "6";
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.VEO_IMAGE_TO_VIDEO, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.VEO_IMAGE_TO_VIDEO, result.requestId);
}

// ─── Reference Images to Video ──────────────────────────────────────────────
export async function falReferenceToVideo(params: {
  prompt: string;
  image_urls: string[];
  aspect_ratio?: "16:9" | "9:16";
  duration?: string;
  resolution?: "720p" | "1080p" | "4k";
  generate_audio?: boolean;
  auto_fix?: boolean;
  safety_tolerance?: "1" | "2" | "3" | "4" | "5" | "6";
  seed?: number;
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.VEO_REFERENCE_TO_VIDEO, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.VEO_REFERENCE_TO_VIDEO, result.requestId);
}

// ─── Happy Horse: Image to Video ─────────────────────────────────────────────
export async function falHappyHorseImageToVideo(params: {
  image_url: string;
  prompt?: string;
  resolution?: "720p" | "1080p";
  duration?: number;
  seed?: number;
  enable_safety_checker?: boolean;
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.HAPPY_HORSE_IMAGE, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.HAPPY_HORSE_IMAGE, result.requestId);
}

// ─── Happy Horse: Reference to Video ─────────────────────────────────────────
export async function falHappyHorseReferenceToVideo(params: {
  prompt: string;
  image_urls: string[];
  aspect_ratio?: "16:9" | "9:16" | "1:1" | "4:3" | "3:4";
  resolution?: "720p" | "1080p";
  duration?: number;
  seed?: number;
  enable_safety_checker?: boolean;
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.HAPPY_HORSE_REFERENCE, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.HAPPY_HORSE_REFERENCE, result.requestId);
}

// ─── Seedance 2.0: Image to Video ────────────────────────────────────────────
export async function falSeedanceImageToVideo(params: {
  prompt: string;
  image_url: string;
  end_image_url?: string;
  resolution?: "480p" | "720p" | "1080p";
  duration?: "auto" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "11" | "12" | "13" | "14" | "15";
  aspect_ratio?: "auto" | "21:9" | "16:9" | "4:3" | "1:1" | "3:4" | "9:16";
  generate_audio?: boolean;
  seed?: number;
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.SEEDANCE_IMAGE, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.SEEDANCE_IMAGE, result.requestId);
}

// ─── Seedance 2.0: Reference to Video ────────────────────────────────────────
export async function falSeedanceReferenceToVideo(params: {
  prompt: string;
  image_urls?: string[];
  video_urls?: string[];
  audio_urls?: string[];
  resolution?: "480p" | "720p" | "1080p";
  duration?: "auto" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "11" | "12" | "13" | "14" | "15";
  aspect_ratio?: "auto" | "21:9" | "16:9" | "4:3" | "1:1" | "3:4" | "9:16";
  generate_audio?: boolean;
  seed?: number;
}): Promise<VideoGenerationResult> {
  const result = await fal.subscribe(FAL_MODELS.SEEDANCE_REFERENCE, {
    input: params,
    logs: true,
    onQueueUpdate: progressLogger,
  });
  return extractVideoResult(result.data as FalVideoOutput, FAL_MODELS.SEEDANCE_REFERENCE, result.requestId);
}

// ─── File Upload ─────────────────────────────────────────────────────────────
export async function falUploadFile(filePath: string): Promise<string> {
  const { readFile } = await import("node:fs/promises");
  const { extname } = await import("node:path");
  const ext = extname(filePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".bmp": "image/bmp",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
  };
  const mimeType = mimeTypes[ext] ?? "application/octet-stream";
  const buffer = await readFile(filePath);
  const file = new File([buffer], filePath.split("/").pop() ?? "upload", { type: mimeType });
  const url = await fal.storage.upload(file);
  return url;
}
