/**
 * fal.ai API client — wraps @fal-ai/client with typed helpers.
 * All requests use the queue-based polling approach for reliability.
 */
import type { VideoGenerationResult } from "../types.js";
export declare function configureFal(apiKey: string): void;
export declare function falTextToVideo(params: {
    prompt: string;
    aspect_ratio?: "16:9" | "9:16";
    duration?: "4s" | "6s" | "8s";
    negative_prompt?: string;
    resolution?: "720p" | "1080p" | "4k";
    generate_audio?: boolean;
    seed?: number;
    auto_fix?: boolean;
    safety_tolerance?: "1" | "2" | "3" | "4" | "5" | "6";
}): Promise<VideoGenerationResult>;
export declare function falExtendVideo(params: {
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
}): Promise<VideoGenerationResult>;
export declare function falFirstLastFrameToVideo(params: {
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
}): Promise<VideoGenerationResult>;
export declare function falImageToVideo(params: {
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
}): Promise<VideoGenerationResult>;
export declare function falReferenceToVideo(params: {
    prompt: string;
    image_urls: string[];
    aspect_ratio?: "16:9" | "9:16";
    duration?: string;
    resolution?: "720p" | "1080p" | "4k";
    generate_audio?: boolean;
    auto_fix?: boolean;
    safety_tolerance?: "1" | "2" | "3" | "4" | "5" | "6";
    seed?: number;
}): Promise<VideoGenerationResult>;
export declare function falHappyHorseImageToVideo(params: {
    image_url: string;
    prompt?: string;
    resolution?: "720p" | "1080p";
    duration?: number;
    seed?: number;
    enable_safety_checker?: boolean;
}): Promise<VideoGenerationResult>;
export declare function falHappyHorseReferenceToVideo(params: {
    prompt: string;
    image_urls: string[];
    aspect_ratio?: "16:9" | "9:16" | "1:1" | "4:3" | "3:4";
    resolution?: "720p" | "1080p";
    duration?: number;
    seed?: number;
    enable_safety_checker?: boolean;
}): Promise<VideoGenerationResult>;
export declare function falSeedanceImageToVideo(params: {
    prompt: string;
    image_url: string;
    end_image_url?: string;
    resolution?: "480p" | "720p" | "1080p";
    duration?: "auto" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "11" | "12" | "13" | "14" | "15";
    aspect_ratio?: "auto" | "21:9" | "16:9" | "4:3" | "1:1" | "3:4" | "9:16";
    generate_audio?: boolean;
    seed?: number;
}): Promise<VideoGenerationResult>;
export declare function falSeedanceReferenceToVideo(params: {
    prompt: string;
    image_urls?: string[];
    video_urls?: string[];
    audio_urls?: string[];
    resolution?: "480p" | "720p" | "1080p";
    duration?: "auto" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "11" | "12" | "13" | "14" | "15";
    aspect_ratio?: "auto" | "21:9" | "16:9" | "4:3" | "1:1" | "3:4" | "9:16";
    generate_audio?: boolean;
    seed?: number;
}): Promise<VideoGenerationResult>;
export declare function falUploadFile(filePath: string): Promise<string>;
//# sourceMappingURL=falClient.d.ts.map