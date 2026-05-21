/**
 * MOV conversion helpers.
 * All 9 video generation tools route their result through formatResult() which
 * downloads the MP4, rewraps it losslessly to a local .mov, and writes a
 * .meta.json sidecar containing the full prompt and asset metadata.
 *
 * File naming priority:
 *   1. asset_name + animation_type   → HP1_idle_1747234567890.mov
 *   2. asset_name only               → HP1_1747234567890.mov
 *   3. Slugified prompt              → Zeus_dragon_breathes_1747234567890.mov
 *   4. Model name fallback           → fal_ai_veo_1747234567890.mov
 *
 * ffmpeg is sourced in priority order:
 *   1. Managed install at ~/.h5g-ai-video/node_modules/ffmpeg-static/ffmpeg[.exe]
 *   2. System ffmpeg (detected via `where` / `which`)
 *   3. Auto-installed to ~/.h5g-ai-video/ via `npm install ffmpeg-static` on first run
 *
 * Sidecar format matches the slot-art plugin's h5g_asset.meta.v1 schema (adapted
 * for video: schema = "h5g_video.meta.v1").
 */
import type { VideoGenerationResult } from "../types.js";
export interface VideoFormatOpts {
    prompt?: string;
    assetName?: string;
    animationType?: string;
    sourceImageUrl?: string;
}
export declare function ensureFfmpegStatic(): Promise<string | null>;
export declare function formatResult(result: VideoGenerationResult, opts?: VideoFormatOpts): Promise<string>;
//# sourceMappingURL=movConverter.d.ts.map