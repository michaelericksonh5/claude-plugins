/**
 * fal.ai API client — wraps @fal-ai/client with typed helpers.
 * All requests use the queue-based polling approach for reliability.
 */
import { fal } from "@fal-ai/client";
import { FAL_MODELS } from "../constants.js";
let falConfigured = false;
export function configureFal(apiKey) {
    if (!falConfigured) {
        fal.config({ credentials: apiKey });
        falConfigured = true;
    }
}
function extractVideoResult(data, modelId, requestId) {
    return {
        provider: "fal",
        model: modelId,
        video: {
            url: data.video.url,
            content_type: data.video.content_type,
            file_name: data.video.file_name,
            file_size: data.video.file_size,
            width: data.video.width,
            height: data.video.height,
            fps: data.video.fps,
            duration: data.video.duration,
            num_frames: data.video.num_frames,
        },
        seed: data.seed,
        request_id: requestId,
    };
}
function progressLogger(update) {
    if (update.status === "IN_PROGRESS" && update.logs) {
        update.logs.forEach((log) => process.stderr.write(`[fal] ${log.message}\n`));
    }
}
// ─── Text-to-Video ──────────────────────────────────────────────────────────
export async function falTextToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.VEO_TEXT_TO_VIDEO, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.VEO_TEXT_TO_VIDEO, result.requestId);
}
// ─── Extend Video ───────────────────────────────────────────────────────────
export async function falExtendVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.VEO_EXTEND_VIDEO, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.VEO_EXTEND_VIDEO, result.requestId);
}
// ─── First + Last Frame to Video ─────────────────────────────────────────────
export async function falFirstLastFrameToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.VEO_FIRST_LAST_FRAME, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.VEO_FIRST_LAST_FRAME, result.requestId);
}
// ─── Image to Video ─────────────────────────────────────────────────────────
export async function falImageToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.VEO_IMAGE_TO_VIDEO, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.VEO_IMAGE_TO_VIDEO, result.requestId);
}
// ─── Reference Images to Video ──────────────────────────────────────────────
export async function falReferenceToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.VEO_REFERENCE_TO_VIDEO, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.VEO_REFERENCE_TO_VIDEO, result.requestId);
}
// ─── Happy Horse: Image to Video ─────────────────────────────────────────────
export async function falHappyHorseImageToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.HAPPY_HORSE_IMAGE, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.HAPPY_HORSE_IMAGE, result.requestId);
}
// ─── Happy Horse: Reference to Video ─────────────────────────────────────────
export async function falHappyHorseReferenceToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.HAPPY_HORSE_REFERENCE, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.HAPPY_HORSE_REFERENCE, result.requestId);
}
// ─── Seedance 2.0: Image to Video ────────────────────────────────────────────
export async function falSeedanceImageToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.SEEDANCE_IMAGE, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.SEEDANCE_IMAGE, result.requestId);
}
// ─── Seedance 2.0: Reference to Video ────────────────────────────────────────
export async function falSeedanceReferenceToVideo(params) {
    const result = await fal.subscribe(FAL_MODELS.SEEDANCE_REFERENCE, {
        input: params,
        logs: true,
        onQueueUpdate: progressLogger,
    });
    return extractVideoResult(result.data, FAL_MODELS.SEEDANCE_REFERENCE, result.requestId);
}
// ─── File Upload ─────────────────────────────────────────────────────────────
export async function falUploadFile(filePath) {
    const { readFile } = await import("node:fs/promises");
    const { extname } = await import("node:path");
    const ext = extname(filePath).toLowerCase();
    const mimeTypes = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".bmp": "image/bmp",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    };
    const mimeType = mimeTypes[ext] ?? "application/octet-stream";
    const buffer = await readFile(filePath);
    const file = new File([buffer], filePath.split("/").pop() ?? "upload", { type: mimeType });
    const url = await fal.storage.upload(file);
    return url;
}
//# sourceMappingURL=falClient.js.map