#!/usr/bin/env python3
"""Deterministic recipe-family classifier for slot-machine Spine animation work.

Given a folder of per-layer PNG names, a single asset name, or a list of layer
names, propose the most likely recipe family from the 15 implementable families
in the slot-animation taxonomy. Output is a JSON object with the family key, a
confidence score, and the evidence that drove the decision.

USE
  python classify_family.py --layer-dir <path>
  python classify_family.py --name HP1_head
  python classify_family.py --names HP1_BG HP1_head HP1_head_eyes_blink

EVIDENCE
  Three signals are weighed:
    1. Filename / layer-name prefix (strongest single signal)
    2. Layer composition (presence of head/eyes/laugh/etc indicates character symbol)
    3. State naming patterns (StateN, intro/outro, MeterIdle, etc)

  Visual style alone is never used. A premium-looking King card is still lp_symbol.

OUTPUT
  {
    "family": "hp_symbol",
    "confidence": 0.85,
    "evidence": [
      {"signal": "prefix", "match": "HP", "weight": 0.5},
      {"signal": "composition", "match": "head + eyes_blink", "weight": 0.35}
    ],
    "alternatives": [
      {"family": "special_feature_symbol", "confidence": 0.45}
    ],
    "warnings": []
  }

Confidence above 0.7 is high; 0.5-0.7 is medium and a user check is recommended;
below 0.5 means the signals are ambiguous and the user should classify manually.

EXIT
  0 on successful classification (regardless of confidence).
  2 on unparseable / empty input.
  3 on a review-gated family detection (BL row blocker, unknown).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

# Prefix → family. Match against the leading token of each layer name.
# Order matters when prefixes overlap (e.g. WYS before WY).
PREFIX_TO_FAMILY = [
    (r"^HP(\d+)?", "hp_symbol", 0.55),
    (r"^MP(\d+)?", "mp_symbol", 0.55),
    (r"^LP(\d+)?", "lp_symbol", 0.55),
    (r"^WD(\d+)?", "wild_symbol", 0.55),
    (r"^WILD", "wild_symbol", 0.55),
    (r"^SC(\d+)?", "scatter_symbol", 0.55),
    (r"^SCATTER", "scatter_symbol", 0.55),
    (r"^SF(\d+)?", "special_feature_symbol", 0.55),
    (r"^JP(\d+)?", "jackpot_symbol", 0.55),
    (r"^JACKPOT", "jackpot_symbol", 0.55),
    (r"^TIER(\d+)?", "jackpot_symbol", 0.40),
    (r"^WYS(\d+)?", "value_symbol", 0.55),
    (r"^WY(\d+)?", "value_symbol", 0.50),
    (r"^CASH", "value_symbol", 0.50),
    (r"^BO(\d+)?", "bonus_symbol", 0.50),
    (r"^BONUS", "bonus_symbol", 0.55),
    (r"^BL(\d+)?", "blocker_or_bonus_symbol", 0.55),
    (r"^BLOCKER", "blocker_or_bonus_symbol", 0.55),
    (r"^WINFRAME", "winframe_explode", 0.60),
    (r"^FRAME_EXPLODE", "winframe_explode", 0.60),
    (r"^METER", "meter", 0.55),
    (r"^STATE\d+COLLECT", "meter", 0.50),
    (r"^INTRO", "transition", 0.40),
    (r"^OUTRO", "transition", 0.40),
    (r"^FB_TRANSITION", "transition", 0.60),
    (r"^SB_TRANSITION", "transition", 0.60),
    (r"^TRANSITION", "transition", 0.50),
    (r"^CELEBRATION", "celebration", 0.55),
    (r"^GRANDJACKPOT", "celebration", 0.55),
    (r"^TIER_\d", "celebration", 0.45),
    (r"^BURST", "celebration", 0.40),
    (r"^AVATAR", "avatar", 0.55),
    (r"^STATE\d+(IDLE|TO\d+|AWARDED|CLOSE)", "avatar", 0.55),
]

# Composition signals: pairs of (substring patterns to find) → (family, weight).
# Multiple matches accumulate up to a cap.
COMPOSITION_SIGNALS = [
    # Character symbol layer composition
    ({"head", "eyes"}, "hp_symbol", 0.20),
    ({"head", "laugh"}, "hp_symbol", 0.20),
    ({"head", "hand"}, "hp_symbol", 0.20),
    ({"head", "arm"}, "hp_symbol", 0.15),
    ({"hat_top"}, "hp_symbol", 0.10),
    # Letter card composition
    ({"letter"}, "lp_symbol", 0.30),
    # Wild composition
    ({"shimmer"}, "wild_symbol", 0.20),
    # Value composition
    ({"value_text", "cash"}, "value_symbol", 0.20),
    # Meter composition
    ({"meter_bar", "state_collect"}, "meter", 0.30),
    # Avatar composition
    ({"state", "awarded"}, "avatar", 0.30),
]

REVIEW_GATED = {"blocker_or_bonus_symbol", "non_symbol_or_unknown"}


def _normalize(name: str) -> str:
    """Strip path, extension, and lower-case for comparison."""
    return Path(name).stem.upper()


def _strip_symbol_prefix(name: str) -> str:
    """Strip the per-asset symbol-code prefix to get the role suffix.

    HP1_head_eyes_blink → head_eyes_blink
    """
    upper = name.upper()
    m = re.match(r"^(HP|MP|LP|WD|SC|SF|JP|WYS|WY|CASH|BO|BL)\d*[_-]?", upper)
    if m:
        return upper[m.end():]
    return upper


def _detect_prefix(names: Iterable[str]) -> tuple[str | None, str | None, float]:
    """Vote on family by prefix across all layer names.

    Returns (family, matched_prefix, weight). The most-frequent prefix wins.
    """
    counts: dict[tuple[str, str], int] = {}
    weights: dict[tuple[str, str], float] = {}
    for raw in names:
        upper = _normalize(raw)
        for pattern, family, weight in PREFIX_TO_FAMILY:
            if re.match(pattern, upper):
                key = (family, pattern)
                counts[key] = counts.get(key, 0) + 1
                weights[key] = max(weights.get(key, 0.0), weight)
                break  # Only first matching prefix per name
    if not counts:
        return None, None, 0.0
    best_key = max(counts, key=lambda k: (counts[k], weights[k]))
    family, pattern = best_key
    # Confidence scales with how many layers shared this prefix.
    fraction = counts[best_key] / max(1, len(list(names)))
    return family, pattern, weights[best_key] * (0.5 + 0.5 * fraction)


def _detect_composition(names: list[str]) -> list[tuple[str, str, float]]:
    """Detect composition signals (head+eyes, head+laugh, etc).

    Returns list of (family, evidence_label, weight).
    """
    joined = " ".join(_strip_symbol_prefix(n).lower() for n in names)
    hits: list[tuple[str, str, float]] = []
    for needles, family, weight in COMPOSITION_SIGNALS:
        if all(needle in joined for needle in needles):
            hits.append((family, " + ".join(sorted(needles)), weight))
    return hits


def _collect_names(args: argparse.Namespace) -> list[str]:
    if args.layer_dir:
        d = Path(args.layer_dir)
        if not d.exists() or not d.is_dir():
            print(json.dumps({"error": f"layer_dir not found or not a directory: {d}"}))
            sys.exit(2)
        return [p.name for p in sorted(d.iterdir()) if p.is_file() and p.suffix.lower() == ".png"]
    if args.name:
        return [args.name]
    if args.names:
        return list(args.names)
    print(json.dumps({"error": "provide --layer-dir, --name, or --names"}))
    sys.exit(2)


def classify(names: list[str]) -> dict:
    """Run the classification pipeline and return a result dict."""
    if not names:
        return {
            "family": "non_symbol_or_unknown",
            "confidence": 0.0,
            "evidence": [],
            "alternatives": [],
            "warnings": ["empty input — no layer names supplied"],
        }

    family, matched_prefix, prefix_weight = _detect_prefix(names)
    composition_hits = _detect_composition(names)

    evidence: list[dict] = []
    alternatives: list[dict] = []
    warnings: list[str] = []

    if family:
        evidence.append({"signal": "prefix", "match": matched_prefix, "weight": round(prefix_weight, 3)})
    # Compose: composition signals can either reinforce or contest the prefix decision.
    composition_for_family: dict[str, float] = {}
    for hit_family, label, weight in composition_hits:
        composition_for_family[hit_family] = composition_for_family.get(hit_family, 0.0) + weight
        evidence.append({"signal": "composition", "match": label, "family": hit_family, "weight": round(weight, 3)})

    # If composition picks a different family than the prefix, surface it as an alternative.
    if family is None and composition_for_family:
        family = max(composition_for_family, key=composition_for_family.get)
        prefix_weight = 0.0

    score = prefix_weight + composition_for_family.get(family or "", 0.0)
    score = max(0.0, min(1.0, score))

    for alt_family, alt_weight in composition_for_family.items():
        if alt_family != family:
            alternatives.append({"family": alt_family, "confidence": round(min(1.0, alt_weight), 3)})

    if family is None:
        family = "non_symbol_or_unknown"
        warnings.append("no prefix or composition signals matched — manual classification required")

    if family in REVIEW_GATED:
        warnings.append(f"{family} is review-gated; no deterministic compiler template exists. Surface for human triage.")

    if family == "hp_symbol" and "laugh" not in " ".join(names).lower() and "eyes_blink" not in " ".join(names).lower():
        # Likely a proof HP, not a layered character HP.
        evidence.append({"signal": "note", "match": "no expression overlay layers — likely proof scaffold, not layered character"})

    return {
        "family": family,
        "confidence": round(score, 3),
        "evidence": evidence,
        "alternatives": sorted(alternatives, key=lambda a: -a["confidence"])[:3],
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify slot-symbol asset into one of 15 implementable recipe families.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--layer-dir", help="Folder containing per-layer PNG files.")
    group.add_argument("--name", help="Single layer or asset name (e.g., HP1_head).")
    group.add_argument("--names", nargs="+", help="Space-separated list of layer/asset names.")
    args = parser.parse_args()

    names = _collect_names(args)
    result = classify(names)
    print(json.dumps(result, indent=2))

    if result["family"] in REVIEW_GATED:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
