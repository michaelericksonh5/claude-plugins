/**
 * Key Manager — reads API keys from environment variables only.
 * Keys are NEVER logged, stored in files, or returned to callers in plain text.
 */
import type { ApiKeyStatus, ApiProvider } from "../types.js";
export declare function getFalKey(): string | undefined;
export declare function getGeminiKey(): string | undefined;
export declare function getApiKeyStatus(): ApiKeyStatus;
/**
 * Resolve which provider to use.
 * If the caller requests a specific provider, use that (and error if key missing).
 * If "auto", prefer fal.ai then gemini.
 */
export declare function resolveProvider(requested: "fal" | "gemini" | "auto"): {
    provider: ApiProvider;
    key: string;
};
//# sourceMappingURL=keyManager.d.ts.map