// ─── API Provider ──────────────────────────────────────────────────────────
export type ApiProvider = "fal" | "gemini";

// ─── Shared Video Result ───────────────────────────────────────────────────
export interface VideoResult {
  url: string;
  content_type?: string;
  file_name?: string;
  file_size?: number;
  width?: number;
  height?: number;
  fps?: number;
  duration?: number;
  num_frames?: number;
}

export interface VideoGenerationResult {
  provider: ApiProvider;
  model: string;
  video: VideoResult;
  seed?: number;
  request_id?: string;
}

// ─── fal.ai Types ─────────────────────────────────────────────────────────
export interface FalVideoOutput {
  video: {
    url: string;
    content_type?: string;
    file_name?: string;
    file_size?: number;
    width?: number;
    height?: number;
    fps?: number;
    duration?: number;
    num_frames?: number;
  };
  seed?: number;
}

// ─── Gemini Types ─────────────────────────────────────────────────────────
export interface GeminiVideoOperation {
  name: string;
  done?: boolean;
  response?: {
    generateVideoResponse?: {
      generatedSamples?: Array<{
        video?: { uri: string };
      }>;
    };
    generatedVideos?: Array<{
      video?: { uri: string; name?: string };
    }>;
  };
  error?: {
    code: number;
    message: string;
  };
}

// ─── Key Status ────────────────────────────────────────────────────────────
export interface ApiKeyStatus {
  fal_configured: boolean;
  gemini_configured: boolean;
  active_provider: ApiProvider | "none";
}
