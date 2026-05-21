/**
 * Google Gemini Veo 3.1 client using the REST API directly.
 * Uses long-running operations with polling (no persistent SDK session needed).
 */
import type { VideoGenerationResult } from "../types.js";
export declare function geminiTextToVideo(apiKey: string, params: {
    prompt: string;
    aspect_ratio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    duration_seconds?: number;
    negative_prompt?: string;
    seed?: number;
}): Promise<VideoGenerationResult>;
export declare function geminiImageToVideo(apiKey: string, params: {
    prompt: string;
    image_url?: string;
    image_base64?: string;
    image_mime_type?: string;
    aspect_ratio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    duration_seconds?: number;
    negative_prompt?: string;
    seed?: number;
}): Promise<VideoGenerationResult>;
export declare function geminiFirstLastFrameToVideo(apiKey: string, params: {
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
}): Promise<VideoGenerationResult>;
export declare function geminiReferenceToVideo(apiKey: string, params: {
    prompt: string;
    image_urls: string[];
    aspect_ratio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    duration_seconds?: number;
    negative_prompt?: string;
    seed?: number;
}): Promise<VideoGenerationResult>;
export declare function geminiExtendVideo(_apiKey: string, _params: {
    prompt: string;
    video_url: string;
    resolution?: "720p";
    negative_prompt?: string;
    seed?: number;
}): Promise<VideoGenerationResult>;
//# sourceMappingURL=geminiClient.d.ts.map