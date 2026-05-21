/**
 * ffmpeg post-processing tools — lossless conversion and resize.
 *
 * These operate on already-generated local video files.
 * No AI generation; pure ffmpeg operations.
 *
 * Tools:
 *   veo_convert_video — lossless container rewrap (MP4↔MOV, etc.)
 *   veo_resize_video  — resize to exact dimensions with fill/fit/stretch modes
 *
 * Both tools reuse the ensureFfmpegStatic() bootstrap from movConverter
 * so no separate ffmpeg install is needed.
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import * as fs from "node:fs";
import * as path from "node:path";
import * as child_process from "node:child_process";
import { ensureFfmpegStatic } from "../services/movConverter.js";

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function runFfmpeg(ffmpegBin: string, args: string[]): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    child_process.execFile(
      ffmpegBin,
      args,
      { timeout: 300_000 },
      (err) => (err ? reject(new Error(`ffmpeg: ${err.message}`)) : resolve())
    );
  });
}

function fileSizeMB(filePath: string): string {
  return (fs.statSync(filePath).size / 1024 / 1024).toFixed(1);
}

// ─── Register ────────────────────────────────────────────────────────────────

export function registerFfmpegTools(server: McpServer): void {

  // ── Convert Video ──────────────────────────────────────────────────────────
  server.registerTool(
    "veo_convert_video",
    {
      title: "Convert Video — Lossless Container Rewrap",
      description: `Losslessly rewrap a video to a different container format without re-encoding.
Copies the video and audio streams as-is — instant and quality-lossless.

Use this to:
  - Convert MP4 → MOV for After Effects or game engine delivery
  - Convert MOV → MP4 for web/mobile delivery

Args:
  - input_path (required): Absolute path to the source video file
  - output_format: "mov" or "mp4". Default: "mov"
  - output_path: Where to save the result. Default: same directory as input, new extension

Returns: Path to the converted file and its size.`,
      inputSchema: z.object({
        input_path: z.string().describe("Absolute path to the source video file"),
        output_format: z.enum(["mov", "mp4"]).default("mov").describe("Output container format"),
        output_path: z.string().optional().describe("Output file path (default: input dir, new extension)"),
      }),
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    async (params) => {
      try {
        if (!fs.existsSync(params.input_path)) {
          return { content: [{ type: "text" as const, text: `Error: File not found: ${params.input_path}` }] };
        }

        const ffmpegBin = await ensureFfmpegStatic();
        if (!ffmpegBin) {
          return { content: [{ type: "text" as const, text: "Error: ffmpeg not available. Generate a video first to trigger auto-install." }] };
        }

        const ext = params.output_format;
        const outPath = params.output_path ?? (() => {
          const dir = path.dirname(params.input_path);
          const base = path.basename(params.input_path, path.extname(params.input_path));
          return path.join(dir, `${base}.${ext}`);
        })();

        fs.mkdirSync(path.dirname(outPath), { recursive: true });

        await runFfmpeg(ffmpegBin, ["-i", params.input_path, "-c", "copy", "-y", outPath]);

        return {
          content: [{
            type: "text" as const,
            text: [
              `✅ Conversion complete (lossless rewrap)`,
              ``,
              `**Input**: ${params.input_path}`,
              `**Output**: ${outPath}`,
              `**Size**: ${fileSizeMB(outPath)} MB`,
            ].join("\n"),
          }],
        };
      } catch (e) {
        return { content: [{ type: "text" as const, text: `Error: ${e instanceof Error ? e.message : String(e)}` }] };
      }
    }
  );

  // ── Resize Video ───────────────────────────────────────────────────────────
  server.registerTool(
    "veo_resize_video",
    {
      title: "Resize Video — Scale to Exact Dimensions",
      description: `Resize a video to exact pixel dimensions for game or production delivery.
Re-encodes the video stream; audio is stream-copied when possible.

Fit modes:
  - "fill" (default): Scale to fill the entire frame, center-crop any overflow.
    Best for game assets — exact target dimensions, no black bars.
  - "fit": Scale to fit within the frame, pad with black bars if needed (letterbox/pillarbox).
  - "stretch": Force exact dimensions without preserving aspect ratio (distorts if ratios differ).

Codec options:
  - "prores" (default for MOV): Apple ProRes 422 HQ — broadcast/game-engine quality.
    Visually lossless, large files. Standard for AE and game engine delivery.
  - "h264" (default for MP4): H.264 CRF 18 — high quality, smaller files, widely compatible.
  - "h265": H.265 CRF 20 — smallest files, modern platforms only.

Args:
  - input_path (required): Absolute path to the source video
  - width (required): Target width in pixels (e.g. 1280)
  - height (required): Target height in pixels (e.g. 852)
  - fit_mode: "fill" | "fit" | "stretch". Default: "fill"
  - codec: "prores" | "h264" | "h265". Default: prores for MOV, h264 for MP4
  - output_format: "mov" or "mp4". Default: "mov"
  - output_path: Output file path. Default: input dir with resolution suffix (e.g. HP1_idle_1280x852.mov)

Returns: Path to the resized file and metadata.`,
      inputSchema: z.object({
        input_path: z.string().describe("Absolute path to the source video"),
        width: z.number().int().positive().describe("Target width in pixels"),
        height: z.number().int().positive().describe("Target height in pixels"),
        fit_mode: z.enum(["fill", "fit", "stretch"]).default("fill").describe("Aspect ratio handling: fill (scale+crop), fit (letterbox), stretch"),
        codec: z.enum(["prores", "h264", "h265"]).optional().describe("Video codec (default: prores for MOV, h264 for MP4)"),
        output_format: z.enum(["mov", "mp4"]).default("mov").describe("Output container format"),
        output_path: z.string().optional().describe("Output file path (default: input dir, resolution suffix)"),
      }),
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    async (params) => {
      try {
        if (!fs.existsSync(params.input_path)) {
          return { content: [{ type: "text" as const, text: `Error: File not found: ${params.input_path}` }] };
        }

        const ffmpegBin = await ensureFfmpegStatic();
        if (!ffmpegBin) {
          return { content: [{ type: "text" as const, text: "Error: ffmpeg not available. Generate a video first to trigger auto-install." }] };
        }

        const W = params.width;
        const H = params.height;
        const fmt = params.output_format;
        const codec = params.codec ?? (fmt === "mov" ? "prores" : "h264");
        // ProRes requires MOV container — override silently
        const effectiveFmt = codec === "prores" ? "mov" : fmt;

        // Scale/crop filter
        let vf: string;
        switch (params.fit_mode) {
          case "fill":
            vf = `scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H}`;
            break;
          case "fit":
            vf = `scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:trunc((ow-iw)/2):trunc((oh-ih)/2):color=black`;
            break;
          case "stretch":
          default:
            vf = `scale=${W}:${H}`;
            break;
        }

        // Codec args
        let videoArgs: string[];
        switch (codec) {
          case "prores":
            videoArgs = ["-c:v", "prores_ks", "-profile:v", "3"];
            break;
          case "h265":
            videoArgs = ["-c:v", "libx265", "-crf", "20", "-preset", "slow"];
            break;
          case "h264":
          default:
            videoArgs = ["-c:v", "libx264", "-crf", "18", "-preset", "slow"];
            break;
        }

        const base = path.basename(params.input_path, path.extname(params.input_path));
        const dir = path.dirname(params.input_path);
        const outPath = params.output_path ?? path.join(dir, `${base}_${W}x${H}.${effectiveFmt}`);
        fs.mkdirSync(path.dirname(outPath), { recursive: true });

        await runFfmpeg(ffmpegBin, [
          "-i", params.input_path,
          "-vf", vf,
          ...videoArgs,
          "-c:a", "copy",
          "-y", outPath,
        ]);

        return {
          content: [{
            type: "text" as const,
            text: [
              `✅ Resize complete`,
              ``,
              `**Input**: ${params.input_path}`,
              `**Output**: ${outPath}`,
              `**Dimensions**: ${W}×${H}`,
              `**Fit mode**: ${params.fit_mode}`,
              `**Codec**: ${codec}`,
              `**Size**: ${fileSizeMB(outPath)} MB`,
            ].join("\n"),
          }],
        };
      } catch (e) {
        return { content: [{ type: "text" as const, text: `Error: ${e instanceof Error ? e.message : String(e)}` }] };
      }
    }
  );
}
