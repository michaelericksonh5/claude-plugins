/**
 * Happy Horse and Seedance 2.0 video generation tools.
 * These are fal.ai-only (no Gemini counterpart).
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { resolveProvider } from "../services/keyManager.js";
import {
  configureFal,
  falHappyHorseImageToVideo,
  falHappyHorseReferenceToVideo,
  falSeedanceImageToVideo,
  falSeedanceReferenceToVideo,
} from "../services/falClient.js";
import { formatResult } from "../services/movConverter.js";

export function registerAlternativeTools(server: McpServer): void {

  // ── Happy Horse: Image to Video ───────────────────────────────────────────
  server.registerTool(
    "veo_happy_horse_image_to_video",
    {
      title: "Happy Horse — Image to Video (Alibaba)",
      description: `Animate a still image using Alibaba's Happy Horse (happyhorse-1.0-i2v) model.
Excellent for bringing portrait, product, and lifestyle photos to life.
fal.ai only (requires FAL_KEY).

Image requirements:
  - Formats: JPEG, JPG, PNG, BMP, WEBP
  - Min dimensions: 300×300px
  - Aspect ratio between 1:2.5 and 2.5:1
  - Max 10 MB

Args:
  - image_url (required): URL of the image to animate (use veo_upload_file for local)
  - prompt: Optional text guiding the animation. Max 2500 chars
  - resolution: "720p" or "1080p". Default: "1080p"
  - duration: 3–15 seconds as integer. Default: 5
  - seed: 0–2147483647 for reproducibility
  - enable_safety_checker: Default true

Returns: Animated video URL and metadata.`,
      inputSchema: z.object({
        image_url: z.string().url().describe("URL of the image to animate"),
        prompt: z.string().max(2500).optional().describe("Optional animation guidance (max 2500 chars)"),
        resolution: z.enum(["720p", "1080p"]).default("1080p").describe("Output resolution"),
        duration: z.number().int().min(3).max(15).default(5).describe("Duration in seconds (3–15)"),
        seed: z.number().int().min(0).max(2147483647).optional().describe("Seed for reproducibility"),
        enable_safety_checker: z.boolean().default(true).describe("Enable content moderation"),
        asset_name: z.string().optional().describe("Slot asset being animated (e.g. 'HP1', 'HP2', 'BG_base', 'WD1'). Sets the output filename."),
        animation_type: z.enum(["idle", "win", "land", "ambient", "intro", "outro", "bonus", "jackpot", "general"]).optional().describe("Animation type for slot game use — idle, win, land, ambient, etc. Sets the filename suffix."),
      }),
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
    },
    async (params) => {
      try {
        const { key } = resolveProvider("fal");
        configureFal(key);
        const result = await falHappyHorseImageToVideo(params);
        return { content: [{ type: "text" as const, text: await formatResult(result, { prompt: params.prompt, assetName: params.asset_name, animationType: params.animation_type }) }], structuredContent: JSON.parse(JSON.stringify(result)) as Record<string, unknown> };
      } catch (e) {
        return { content: [{ type: "text" as const, text: `Error: ${e instanceof Error ? e.message : String(e)}` }] };
      }
    }
  );

  // ── Happy Horse: Reference to Video ──────────────────────────────────────
  server.registerTool(
    "veo_happy_horse_reference_to_video",
    {
      title: "Happy Horse — Reference Images to Video (Alibaba)",
      description: `Generate a video from 1–9 reference images using Happy Horse.
Reference subjects in the prompt as character1, character2, ... (order matches image_urls).
fal.ai only (requires FAL_KEY).

Image requirements:
  - Formats: JPEG, JPG, PNG, WEBP
  - Min shortest side: 400px (720p+ recommended)
  - Max 10 MB each

Args:
  - prompt (required): Describe the video. Use "character1", "character2" etc. to reference subjects.
  - image_urls (required): 1–9 reference image URLs (upload with veo_upload_file if local)
  - aspect_ratio: "16:9", "9:16", "1:1", "4:3", "3:4". Default: "16:9"
  - resolution: "720p" or "1080p". Default: "1080p"
  - duration: 3–15 seconds. Default: 5
  - seed, enable_safety_checker: standard options

Returns: Video URL and metadata.`,
      inputSchema: z.object({
        prompt: z
          .string()
          .min(1)
          .max(2500)
          .describe("Describe the video. Use 'character1', 'character2' etc. to reference subjects"),
        image_urls: z
          .array(z.string().url())
          .min(1)
          .max(9)
          .describe("1–9 reference image URLs"),
        aspect_ratio: z
          .enum(["16:9", "9:16", "1:1", "4:3", "3:4"])
          .default("16:9")
          .describe("Video aspect ratio"),
        resolution: z.enum(["720p", "1080p"]).default("1080p").describe("Output resolution"),
        duration: z.number().int().min(3).max(15).default(5).describe("Duration in seconds (3–15)"),
        seed: z.number().int().min(0).max(2147483647).optional().describe("Seed for reproducibility"),
        enable_safety_checker: z.boolean().default(true).describe("Enable content moderation"),
        asset_name: z.string().optional().describe("Slot asset being animated (e.g. 'HP1', 'HP2', 'BG_base', 'WD1'). Sets the output filename."),
        animation_type: z.enum(["idle", "win", "land", "ambient", "intro", "outro", "bonus", "jackpot", "general"]).optional().describe("Animation type for slot game use — idle, win, land, ambient, etc. Sets the filename suffix."),
      }),
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
    },
    async (params) => {
      try {
        const { key } = resolveProvider("fal");
        configureFal(key);
        const result = await falHappyHorseReferenceToVideo(params);
        return { content: [{ type: "text" as const, text: await formatResult(result, { prompt: params.prompt, assetName: params.asset_name, animationType: params.animation_type }) }], structuredContent: JSON.parse(JSON.stringify(result)) as Record<string, unknown> };
      } catch (e) {
        return { content: [{ type: "text" as const, text: `Error: ${e instanceof Error ? e.message : String(e)}` }] };
      }
    }
  );

  // ── Seedance 2.0: Image to Video ─────────────────────────────────────────
  server.registerTool(
    "veo_seedance_image_to_video",
    {
      title: "Seedance 2.0 — Image to Video (ByteDance)",
      description: `Generate a video from a starting image using ByteDance's Seedance 2.0 model.
Optionally specify an end_image_url to create a transition between two images.
Includes synchronized audio generation (speech, sound effects, ambient).
fal.ai only (requires FAL_KEY).

Image requirements: JPEG, PNG, WebP; max 30 MB.

Args:
  - prompt (required): Describe the motion and action
  - image_url (required): Starting frame URL (use veo_upload_file for local)
  - end_image_url: Optional ending frame URL for image-to-image transitions
  - resolution: "480p" (fast), "720p" (balanced), or "1080p" (highest quality). Default: "720p"
  - duration: "auto" or 4–15 seconds. Default: "auto"
  - aspect_ratio: "auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16". Default: "auto"
  - generate_audio: Include speech, sound effects, ambient. Default: true
  - seed: Seed for reproducibility

Returns: Video URL and metadata.`,
      inputSchema: z.object({
        prompt: z.string().min(1).describe("Describe the motion and action"),
        image_url: z.string().url().describe("Starting frame URL"),
        end_image_url: z.string().url().optional().describe("Optional ending frame for transitions"),
        resolution: z
          .enum(["480p", "720p", "1080p"])
          .default("720p")
          .describe("Video resolution (480p=fast, 720p=balanced, 1080p=quality)"),
        duration: z
          .enum(["auto", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"])
          .default("auto")
          .describe("Duration in seconds or 'auto'"),
        aspect_ratio: z
          .enum(["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"])
          .default("auto")
          .describe("Video aspect ratio"),
        generate_audio: z.boolean().default(true).describe("Generate synchronized audio"),
        seed: z.number().int().optional().describe("Seed for reproducibility"),
        asset_name: z.string().optional().describe("Slot asset being animated (e.g. 'HP1', 'HP2', 'BG_base', 'WD1'). Sets the output filename."),
        animation_type: z.enum(["idle", "win", "land", "ambient", "intro", "outro", "bonus", "jackpot", "general"]).optional().describe("Animation type for slot game use — idle, win, land, ambient, etc. Sets the filename suffix."),
      }),
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
    },
    async (params) => {
      try {
        const { key } = resolveProvider("fal");
        configureFal(key);
        const result = await falSeedanceImageToVideo(params);
        return { content: [{ type: "text" as const, text: await formatResult(result, { prompt: params.prompt, assetName: params.asset_name, animationType: params.animation_type }) }], structuredContent: JSON.parse(JSON.stringify(result)) as Record<string, unknown> };
      } catch (e) {
        return { content: [{ type: "text" as const, text: `Error: ${e instanceof Error ? e.message : String(e)}` }] };
      }
    }
  );

  // ── Seedance 2.0: Reference to Video ─────────────────────────────────────
  server.registerTool(
    "veo_seedance_reference_to_video",
    {
      title: "Seedance 2.0 — Reference to Video (ByteDance)",
      description: `Generate a video from reference images, videos, and/or audio using Seedance 2.0.
Reference assets in the prompt as @Image1, @Image2, @Video1, @Audio1 (order matches respective arrays).
fal.ai only (requires FAL_KEY).

Limits:
  - Images (image_urls): Up to 9, JPEG/PNG/WebP, max 30MB each
  - Videos (video_urls): Up to 3, MP4/MOV, combined 2–15s, each ~480p–720p, under 50MB total
  - Audio (audio_urls): Up to 3, MP3/WAV, combined max 15s, max 15MB each
  - If audio provided, at least one image or video is required
  - Total assets: max 12

Args:
  - prompt (required): Describe the video. Use @Image1, @Video1, @Audio1 etc. to reference assets.
  - image_urls: Reference image URLs (upload with veo_upload_file for local)
  - video_urls: Reference video URLs
  - audio_urls: Reference audio URLs
  - resolution: "480p", "720p", or "1080p". Default: "720p"
  - duration: "auto" or 4–15 seconds. Default: "auto"
  - aspect_ratio: "auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16". Default: "auto"
  - generate_audio, seed: standard options

Returns: Video URL and metadata.`,
      inputSchema: z.object({
        prompt: z
          .string()
          .min(1)
          .describe("Describe the video. Use @Image1, @Video1, @Audio1 etc. to reference assets"),
        image_urls: z
          .array(z.string().url())
          .max(9)
          .optional()
          .describe("Reference image URLs (max 9)"),
        video_urls: z
          .array(z.string().url())
          .max(3)
          .optional()
          .describe("Reference video URLs (max 3, combined 2–15s)"),
        audio_urls: z
          .array(z.string().url())
          .max(3)
          .optional()
          .describe("Reference audio URLs (max 3, combined max 15s)"),
        resolution: z
          .enum(["480p", "720p", "1080p"])
          .default("720p")
          .describe("Video resolution"),
        duration: z
          .enum(["auto", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"])
          .default("auto")
          .describe("Duration in seconds or 'auto'"),
        aspect_ratio: z
          .enum(["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"])
          .default("auto")
          .describe("Video aspect ratio"),
        generate_audio: z.boolean().default(true).describe("Generate synchronized audio"),
        seed: z.number().int().optional().describe("Seed for reproducibility"),
        asset_name: z.string().optional().describe("Slot asset being animated (e.g. 'HP1', 'HP2', 'BG_base', 'WD1'). Sets the output filename."),
        animation_type: z.enum(["idle", "win", "land", "ambient", "intro", "outro", "bonus", "jackpot", "general"]).optional().describe("Animation type for slot game use — idle, win, land, ambient, etc. Sets the filename suffix."),
      }),
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
    },
    async (params) => {
      try {
        const { key } = resolveProvider("fal");
        configureFal(key);
        const result = await falSeedanceReferenceToVideo(params);
        return { content: [{ type: "text" as const, text: await formatResult(result, { prompt: params.prompt, assetName: params.asset_name, animationType: params.animation_type }) }], structuredContent: JSON.parse(JSON.stringify(result)) as Record<string, unknown> };
      } catch (e) {
        return { content: [{ type: "text" as const, text: `Error: ${e instanceof Error ? e.message : String(e)}` }] };
      }
    }
  );
}
