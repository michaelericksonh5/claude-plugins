/**
 * Image measurement library — OKLCH color analysis, fill %, edge density,
 * and background uniformity for slot art QA.
 *
 * Pure JS using pngjs. No native deps. Designed to run on 2K–4K images in
 * under ~2 seconds by downsampling to 256×256 before color clustering.
 *
 * Public API:
 *   measureImage(absolutePath) → { measured_iteration, dominant_color_oklch,
 *                                  fill_pct, bg_uniformity_score, edge_density,
 *                                  ... + detailed metrics }
 *   writeSidecar(absolutePath, metrics) → writes <basename>.metrics.json
 *
 * The MCP server exposes this via nb2_measure (and optional measure: true
 * flag on gen/edit/upscale tools). Opt-in per the v1.5.6 contract.
 */

import * as fs from "fs";
import * as path from "path";
import { PNG } from "pngjs";

// ---------------------------------------------------------------------------
// Color space conversions: sRGB byte → OKLCH
// Björn Ottosson's Oklab matrix, then polar→OKLCH.
// ---------------------------------------------------------------------------

function srgbToLinear(c) {
  c = c / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function linearRGBToOklab(r, g, b) {
  const lLong = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b;
  const mLong = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b;
  const sLong = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b;
  const l_ = Math.cbrt(lLong);
  const m_ = Math.cbrt(mLong);
  const s_ = Math.cbrt(sLong);
  return {
    L: 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
    a: 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
    b: 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
  };
}

function oklabToOklch(L, a, b) {
  const c = Math.sqrt(a * a + b * b);
  let h = (Math.atan2(b, a) * 180) / Math.PI;
  if (h < 0) h += 360;
  return { l: L, c, h };
}

function srgbBytesToOklch(r, g, b) {
  const lab = linearRGBToOklab(
    srgbToLinear(r),
    srgbToLinear(g),
    srgbToLinear(b),
  );
  return oklabToOklch(lab.L, lab.a, lab.b);
}

// ---------------------------------------------------------------------------
// PNG read
// ---------------------------------------------------------------------------

function readPNG(absolutePath) {
  const buf = fs.readFileSync(absolutePath);
  const png = PNG.sync.read(buf);
  return png;
}

// ---------------------------------------------------------------------------
// Downsample to max edge × max edge using box averaging.
// Returns { width, height, pixels: Uint8Array (RGBA) }.
// ---------------------------------------------------------------------------

function downsample(png, maxEdge = 256) {
  const { width: W, height: H, data } = png;
  const scale = Math.max(W, H) / maxEdge;
  if (scale <= 1) {
    return { width: W, height: H, pixels: data, originalScale: 1 };
  }
  const newW = Math.max(1, Math.round(W / scale));
  const newH = Math.max(1, Math.round(H / scale));
  const out = new Uint8Array(newW * newH * 4);

  for (let y = 0; y < newH; y++) {
    const y0 = Math.floor((y / newH) * H);
    const y1 = Math.min(H, Math.floor(((y + 1) / newH) * H));
    for (let x = 0; x < newW; x++) {
      const x0 = Math.floor((x / newW) * W);
      const x1 = Math.min(W, Math.floor(((x + 1) / newW) * W));
      let sumR = 0,
        sumG = 0,
        sumB = 0,
        sumA = 0,
        count = 0;
      for (let yy = y0; yy < y1; yy++) {
        for (let xx = x0; xx < x1; xx++) {
          const idx = (yy * W + xx) * 4;
          sumR += data[idx];
          sumG += data[idx + 1];
          sumB += data[idx + 2];
          sumA += data[idx + 3];
          count++;
        }
      }
      const oi = (y * newW + x) * 4;
      out[oi] = Math.round(sumR / count);
      out[oi + 1] = Math.round(sumG / count);
      out[oi + 2] = Math.round(sumB / count);
      out[oi + 3] = Math.round(sumA / count);
    }
  }
  return { width: newW, height: newH, pixels: out, originalScale: scale };
}

// ---------------------------------------------------------------------------
// K-means clustering in OKLCH space.
// Distance metric: Euclidean in (L, c·cos(h), c·sin(h)) — proper polar.
// ---------------------------------------------------------------------------

function oklchToCartesian({ l, c, h }) {
  const rad = (h * Math.PI) / 180;
  return [l, c * Math.cos(rad), c * Math.sin(rad)];
}

function cartesianToOklch([l, x, y]) {
  const c = Math.sqrt(x * x + y * y);
  let h = (Math.atan2(y, x) * 180) / Math.PI;
  if (h < 0) h += 360;
  return { l, c, h };
}

function dist3(a, b) {
  const dx = a[0] - b[0],
    dy = a[1] - b[1],
    dz = a[2] - b[2];
  return dx * dx + dy * dy + dz * dz;
}

function kmeansOklch(samples, k = 8, maxIters = 12) {
  if (samples.length === 0) return [];
  if (samples.length <= k) {
    return samples.map((s) => ({ centroid: s, members: [s] }));
  }

  // kmeans++ init: pick first centroid uniform, subsequent weighted by sq-dist
  const cartesians = samples.map(oklchToCartesian);
  const centroidsCart = [];
  centroidsCart.push(cartesians[Math.floor(Math.random() * cartesians.length)]);

  while (centroidsCart.length < k) {
    const distances = cartesians.map((p) =>
      Math.min(...centroidsCart.map((c) => dist3(p, c))),
    );
    const sum = distances.reduce((a, b) => a + b, 0);
    if (sum === 0) break;
    let r = Math.random() * sum;
    let pickedIdx = 0;
    for (let i = 0; i < distances.length; i++) {
      r -= distances[i];
      if (r <= 0) {
        pickedIdx = i;
        break;
      }
    }
    centroidsCart.push(cartesians[pickedIdx]);
  }

  // Lloyd iterations
  let assignments = new Array(cartesians.length);
  for (let iter = 0; iter < maxIters; iter++) {
    let changed = false;
    for (let i = 0; i < cartesians.length; i++) {
      let bestIdx = 0;
      let bestDist = Infinity;
      for (let c = 0; c < centroidsCart.length; c++) {
        const d = dist3(cartesians[i], centroidsCart[c]);
        if (d < bestDist) {
          bestDist = d;
          bestIdx = c;
        }
      }
      if (assignments[i] !== bestIdx) {
        assignments[i] = bestIdx;
        changed = true;
      }
    }
    if (!changed && iter > 0) break;

    const newCentroids = centroidsCart.map(() => [0, 0, 0, 0]);
    for (let i = 0; i < cartesians.length; i++) {
      const a = assignments[i];
      newCentroids[a][0] += cartesians[i][0];
      newCentroids[a][1] += cartesians[i][1];
      newCentroids[a][2] += cartesians[i][2];
      newCentroids[a][3] += 1;
    }
    for (let c = 0; c < newCentroids.length; c++) {
      const [sx, sy, sz, n] = newCentroids[c];
      if (n > 0) centroidsCart[c] = [sx / n, sy / n, sz / n];
    }
  }

  // Tally members per cluster
  const counts = new Array(centroidsCart.length).fill(0);
  for (const a of assignments) counts[a]++;

  return centroidsCart.map((c, i) => ({
    centroid: cartesianToOklch(c),
    count: counts[i],
  }));
}

// ---------------------------------------------------------------------------
// Background detection — sample 4 corners + thin border ring.
// Returns { color: {r,g,b,a}, uniformity_score: 0-1 }
// ---------------------------------------------------------------------------

function analyzeBorder(downsampled) {
  const { width: W, height: H, pixels } = downsampled;
  const samples = [];
  const ringDepth = Math.max(1, Math.floor(Math.min(W, H) * 0.03));

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const onTop = y < ringDepth;
      const onBot = y >= H - ringDepth;
      const onLeft = x < ringDepth;
      const onRight = x >= W - ringDepth;
      if (!(onTop || onBot || onLeft || onRight)) continue;
      const i = (y * W + x) * 4;
      samples.push([pixels[i], pixels[i + 1], pixels[i + 2], pixels[i + 3]]);
    }
  }

  if (samples.length === 0) {
    return {
      color: { r: 0, g: 0, b: 0, a: 255 },
      uniformity_score: 1,
    };
  }

  let sumR = 0,
    sumG = 0,
    sumB = 0,
    sumA = 0;
  for (const s of samples) {
    sumR += s[0];
    sumG += s[1];
    sumB += s[2];
    sumA += s[3];
  }
  const meanR = sumR / samples.length;
  const meanG = sumG / samples.length;
  const meanB = sumB / samples.length;
  const meanA = sumA / samples.length;

  let varSum = 0;
  for (const s of samples) {
    const dr = s[0] - meanR;
    const dg = s[1] - meanG;
    const db = s[2] - meanB;
    varSum += dr * dr + dg * dg + db * db;
  }
  const variance = varSum / samples.length;
  const stddev = Math.sqrt(variance);

  // Normalize: stddev=0 → uniformity=1; stddev=50 (RGB) → ~0.5; clamp to [0,1].
  const uniformity_score = Math.max(0, Math.min(1, 1 - stddev / 64));

  return {
    color: {
      r: Math.round(meanR),
      g: Math.round(meanG),
      b: Math.round(meanB),
      a: Math.round(meanA),
    },
    uniformity_score,
  };
}

// ---------------------------------------------------------------------------
// Subject mask (foreground/background separation).
// If image has alpha → opaque pixels are subject.
// If no alpha → "not BG color" pixels are subject (RGB distance threshold).
// ---------------------------------------------------------------------------

function buildSubjectMask(downsampled, bgColor) {
  const { width: W, height: H, pixels } = downsampled;
  const mask = new Uint8Array(W * H);
  const threshold = 32; // RGB distance threshold for "not BG"
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const a = pixels[i + 3];
      if (a < 128) {
        mask[y * W + x] = 0;
        continue;
      }
      const dr = pixels[i] - bgColor.r;
      const dg = pixels[i + 1] - bgColor.g;
      const db = pixels[i + 2] - bgColor.b;
      const d = Math.sqrt(dr * dr + dg * dg + db * db);
      mask[y * W + x] = d > threshold ? 1 : 0;
    }
  }
  return mask;
}

function fillStats(mask, W, H) {
  let count = 0;
  let minX = W,
    minY = H,
    maxX = -1,
    maxY = -1;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      if (mask[y * W + x]) {
        count++;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  const fillPct = count / (W * H);
  const bbox =
    count > 0
      ? { x: minX, y: minY, w: maxX - minX + 1, h: maxY - minY + 1 }
      : null;
  return { fill_pct: fillPct, bounding_box: bbox };
}

// ---------------------------------------------------------------------------
// Sobel edge density. Operates on downsampled grayscale.
// Returns mean gradient magnitude normalized to [0, 1].
// ---------------------------------------------------------------------------

function edgeDensity(downsampled) {
  const { width: W, height: H, pixels } = downsampled;
  const gray = new Float32Array(W * H);
  for (let i = 0; i < W * H; i++) {
    const p = i * 4;
    gray[i] =
      0.2126 * pixels[p] + 0.7152 * pixels[p + 1] + 0.0722 * pixels[p + 2];
  }
  let sumMag = 0;
  let count = 0;
  for (let y = 1; y < H - 1; y++) {
    for (let x = 1; x < W - 1; x++) {
      const tl = gray[(y - 1) * W + (x - 1)];
      const tc = gray[(y - 1) * W + x];
      const tr = gray[(y - 1) * W + (x + 1)];
      const ml = gray[y * W + (x - 1)];
      const mr = gray[y * W + (x + 1)];
      const bl = gray[(y + 1) * W + (x - 1)];
      const bc = gray[(y + 1) * W + x];
      const br = gray[(y + 1) * W + (x + 1)];
      const gx = -tl - 2 * ml - bl + tr + 2 * mr + br;
      const gy = -tl - 2 * tc - tr + bl + 2 * bc + br;
      sumMag += Math.sqrt(gx * gx + gy * gy);
      count++;
    }
  }
  const meanMag = count > 0 ? sumMag / count : 0;
  // Sobel max per pixel ≈ 4 * 255 = 1020 — normalize to [0, 1]
  return Math.min(1, meanMag / 1020);
}

// ---------------------------------------------------------------------------
// Pixel sampler for k-means — skips BG, takes up to maxSamples.
// ---------------------------------------------------------------------------

function samplePixelsForClustering(
  downsampled,
  mask,
  maxSamples = 4000,
) {
  const { width: W, height: H, pixels } = downsampled;
  const subjectPixels = [];
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      if (mask[y * W + x]) {
        const i = (y * W + x) * 4;
        subjectPixels.push([pixels[i], pixels[i + 1], pixels[i + 2]]);
      }
    }
  }
  if (subjectPixels.length === 0) return [];
  let chosen = subjectPixels;
  if (subjectPixels.length > maxSamples) {
    chosen = [];
    const step = subjectPixels.length / maxSamples;
    for (let i = 0; i < maxSamples; i++) {
      chosen.push(subjectPixels[Math.floor(i * step)]);
    }
  }
  return chosen.map(([r, g, b]) => srgbBytesToOklch(r, g, b));
}

// ---------------------------------------------------------------------------
// Top-level: measureImage(absolutePath)
// ---------------------------------------------------------------------------

export async function measureImage(absolutePath) {
  if (!path.isAbsolute(absolutePath)) {
    throw new Error(
      `measureImage requires an absolute path. Got: "${absolutePath}"`,
    );
  }
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Image not found: ${absolutePath}`);
  }

  const png = readPNG(absolutePath);
  const W = png.width,
    H = png.height;

  const down = downsample(png, 256);
  const border = analyzeBorder(down);
  const mask = buildSubjectMask(down, border.color);
  const { fill_pct, bounding_box } = fillStats(mask, down.width, down.height);
  const edge_density = edgeDensity(down);
  const samples = samplePixelsForClustering(down, mask);

  const clusters = kmeansOklch(samples, 8);
  const totalCount = clusters.reduce((acc, c) => acc + (c.count || 0), 0) || 1;
  const dominant = clusters
    .filter((c) => c.count > 0)
    .map((c) => ({
      l: round3(c.centroid.l),
      c: round3(c.centroid.c),
      h: Math.round(c.centroid.h),
      pct: round3(c.count / totalCount),
    }))
    .sort((a, b) => b.pct - a.pct);

  const bgOklch = srgbBytesToOklch(border.color.r, border.color.g, border.color.b);

  return {
    measured_iteration: path.basename(absolutePath),
    last_measured: new Date().toISOString(),

    width: W,
    height: H,

    // SUMMARY fields (embedded into project.json.assets.*.metrics_summary):
    dominant_color_oklch: dominant.slice(0, 6),
    fill_pct: round3(fill_pct),
    bg_uniformity_score: round3(border.uniformity_score),
    edge_density: round3(edge_density),

    // DETAILED fields (sidecar only):
    bounding_box,
    background: {
      rgb: border.color,
      oklch: {
        l: round3(bgOklch.l),
        c: round3(bgOklch.c),
        h: Math.round(bgOklch.h),
      },
      uniformity_score: round3(border.uniformity_score),
    },
    cluster_count: dominant.length,
  };
}

function round3(n) {
  return Math.round(n * 1000) / 1000;
}

// ---------------------------------------------------------------------------
// Sidecar writer: writes <basename>.metrics.json next to the image
// ---------------------------------------------------------------------------

export function writeSidecar(imagePath, metrics) {
  const sidecarPath = imagePath.replace(/\.png$/i, ".metrics.json");
  fs.writeFileSync(sidecarPath, JSON.stringify(metrics, null, 2));
  return sidecarPath;
}

// ---------------------------------------------------------------------------
// metricsSummary(metrics) — extract the subset for project.json embedding
// ---------------------------------------------------------------------------

export function metricsSummary(metrics, iterationPath) {
  return {
    measured_iteration: iterationPath,
    last_measured: metrics.last_measured,
    dominant_color_oklch: metrics.dominant_color_oklch,
    fill_pct: metrics.fill_pct,
    bg_uniformity_score: metrics.bg_uniformity_score,
    edge_density: metrics.edge_density,
  };
}
