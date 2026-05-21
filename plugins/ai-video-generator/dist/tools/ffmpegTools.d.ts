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
export declare function registerFfmpegTools(server: McpServer): void;
//# sourceMappingURL=ffmpegTools.d.ts.map