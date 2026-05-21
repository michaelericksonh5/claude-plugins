/**
 * File upload tool — lets users upload local images/videos to fal.ai storage
 * and get back a public URL suitable for use in video generation calls.
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { resolveProvider } from "../services/keyManager.js";
import { configureFal, falUploadFile } from "../services/falClient.js";

export function registerUploadTools(server: McpServer): void {
  server.registerTool(
    "veo_upload_file",
    {
      title: "Upload File to fal.ai Storage",
      description: `Upload a local image or video file to fal.ai's storage and get a public URL.
Use this when users drop an image or video file into the conversation and you need to
use it as a reference image, starting frame, or ending frame for video generation.

After uploading, use the returned URL in any of the video generation tools:
  - As image_url for veo_image_to_video
  - As first_frame_url / last_frame_url for veo_first_last_frame_to_video
  - As one of the image_urls in veo_reference_to_video or veo_happy_horse_reference_to_video
  - As video_url for veo_extend_video or veo_seedance_image_to_video

Supported formats:
  - Images: JPEG, JPG, PNG, WEBP, BMP (max 10 MB for most models)
  - Videos: MP4, MOV (max 50 MB, max 8s for veo extend)
  - Audio: MP3, WAV (Seedance reference only)

Args:
  - file_path: Absolute path to the local file to upload

Returns:
  {
    "url": string,       // Public URL to use in generation calls
    "file_path": string  // The original local path
  }

Error: "Error: fal.ai key not configured" — run veo_setup_api_key first.`,
      inputSchema: z.object({
        file_path: z
          .string()
          .min(1)
          .describe("Absolute path to the local file to upload (e.g. /Users/you/Desktop/photo.jpg)"),
      }),
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
      },
    },
    async ({ file_path }) => {
      try {
        const { key } = resolveProvider("fal");
        configureFal(key);
        const url = await falUploadFile(file_path);
        const output = { url, file_path };
        return {
          content: [
            {
              type: "text" as const,
              text: `✅ File uploaded successfully!\n\nURL: ${url}\n\nYou can now use this URL in any video generation tool.`,
            },
          ],
          structuredContent: JSON.parse(JSON.stringify(output)) as Record<string, unknown>,
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text" as const,
              text: `Error uploading file: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    }
  );
}
