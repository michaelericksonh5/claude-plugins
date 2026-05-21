// ─── API Configuration ─────────────────────────────────────────────────────
export const FAL_API_BASE = "https://fal.run";
export const GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta";
export const GEMINI_POLL_INTERVAL_MS = 5000;
export const GEMINI_MAX_POLL_ATTEMPTS = 120; // 10 minutes
// ─── fal.ai Model IDs ──────────────────────────────────────────────────────
export const FAL_MODELS = {
    VEO_TEXT_TO_VIDEO: "fal-ai/veo3.1",
    VEO_EXTEND_VIDEO: "fal-ai/veo3.1/extend-video",
    VEO_FIRST_LAST_FRAME: "fal-ai/veo3.1/first-last-frame-to-video",
    VEO_IMAGE_TO_VIDEO: "fal-ai/veo3.1/image-to-video",
    VEO_REFERENCE_TO_VIDEO: "fal-ai/veo3.1/reference-to-video",
    HAPPY_HORSE_IMAGE: "alibaba/happy-horse/image-to-video",
    HAPPY_HORSE_REFERENCE: "alibaba/happy-horse/reference-to-video",
    SEEDANCE_IMAGE: "bytedance/seedance-2.0/image-to-video",
    SEEDANCE_REFERENCE: "bytedance/seedance-2.0/reference-to-video",
};
// ─── Gemini Model IDs ──────────────────────────────────────────────────────
export const GEMINI_MODEL = "veo-3.1-generate-preview";
// ─── Shared Defaults ───────────────────────────────────────────────────────
export const CHARACTER_LIMIT = 25000;
//# sourceMappingURL=constants.js.map