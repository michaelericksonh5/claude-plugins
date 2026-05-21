#!/usr/bin/env python3
"""Creature topology detector.

Given an interpreted layer set, classify the rig's topology so the
animation composer can apply topology-appropriate motion primitives.

Topologies recognized:
  - humanoid:    head + body + arms + hands (2 each). The default; most slot
                  character HP symbols.
  - quadruped:   head + body + 4 legs (often with tail). Lions, tigers, dogs,
                  wolves, foxes.
  - many_legged: 3+ legs OR named tentacles. Spiders (8), insects (6),
                  octopi (8 tentacles).
  - serpentine: body chain or no limbs. Snakes, dragons-without-arms, fish.
  - winged:      torso + wings. Birds, dragons, fairies, bats.
  - tailed:      humanoid-ish but with a tail (foxes-as-character, mermaids).
                  Modifier — combines with humanoid/quadruped.
  - prop:        no character at all. Letters, badges, frames, abstract VFX.
                  This is the topology for LP / JP / value / meter / etc.

Each topology suggests different motion primitives in the animation composer:
  - humanoid:    head bob, hand sway, breathing on body (current default)
  - quadruped:   leg-pair gait (front-back alternation), head bob, tail wag
  - many_legged: asynchronous leg/tentacle wave (sinusoidal phase offsets)
  - serpentine: body undulation along the chain
  - winged:      wing flap + body bob
  - prop:        scale pulse + sheen sweep on body (current LP/JP behavior)

USE
  python detect_topology.py --interpretation <layer_interpretation.json>
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


# Patterns indicating each topology component
LEG_PATTERNS = [re.compile(r"_leg_?\d*$", re.I), re.compile(r"_foot_?[LR]?$", re.I)]
TENTACLE_PATTERNS = [re.compile(r"_tentacle_?\d*$", re.I), re.compile(r"_arm_?\d+$", re.I)]
ARM_PATTERNS = [re.compile(r"_arm_[LR]$", re.I)]
HAND_PATTERNS = [re.compile(r"_hand_[LR]$", re.I), re.compile(r"_hand$", re.I)]
WING_PATTERNS = [re.compile(r"_wing_?[LR]?$", re.I), re.compile(r"_wings?$", re.I)]
TAIL_PATTERNS = [re.compile(r"_tail(_tip|_base|_\d+)?$", re.I)]
BODY_SEGMENT_PATTERNS = [re.compile(r"_body_?\d+$", re.I), re.compile(r"_segment_?\d+$", re.I)]


def _match_any(name: str, patterns) -> bool:
    return any(p.search(name) for p in patterns)


def _stem(name: str) -> str:
    """Strip file extension (and any path) for regex matching."""
    from pathlib import Path
    return Path(name).stem.lower() if name else ""


def detect_topology(interpretation: dict) -> dict:
    """Classify the rig topology from layer interpretations."""
    layers = interpretation.get("layers", [])
    names = [_stem(L.get("name", "")) for L in layers]
    semantic_roles = [(L.get("semantic_role", "") or "").lower() for L in layers]

    legs = sum(1 for n in names if _match_any(n, LEG_PATTERNS))
    tentacles = sum(1 for n in names if _match_any(n, TENTACLE_PATTERNS))
    arms = sum(1 for n in names if _match_any(n, ARM_PATTERNS))
    hands = sum(1 for n in names if _match_any(n, HAND_PATTERNS) or "hand_l" in n or "hand_r" in n)
    wings = sum(1 for n in names if _match_any(n, WING_PATTERNS))
    tails = sum(1 for n in names if _match_any(n, TAIL_PATTERNS))
    body_segments = sum(1 for n in names if _match_any(n, BODY_SEGMENT_PATTERNS))

    has_head = any(r in {"head", "character_body"} for r in semantic_roles)

    # Heuristic classification
    evidence: list[str] = []
    modifiers: list[str] = []
    topology = "prop"  # default

    if (not has_head and arms == 0 and hands == 0 and legs == 0
            and tentacles == 0 and body_segments == 0 and wings == 0):
        topology = "prop"
        evidence.append("no head / arms / legs / tentacles / body segments / wings — abstract decorative asset")
    elif tentacles >= 3:
        topology = "many_legged"
        evidence.append(f"{tentacles} tentacles — octopus-like topology")
    elif legs >= 6:
        topology = "many_legged"
        evidence.append(f"{legs} legs — insect-like topology")
    elif legs >= 4:
        topology = "quadruped"
        evidence.append(f"{legs} legs — quadruped topology")
    elif body_segments >= 2 and arms == 0 and hands == 0 and legs == 0:
        topology = "serpentine"
        evidence.append(f"{body_segments} body segments with no limbs — serpentine topology")
    elif wings >= 1 and (arms <= 1 and hands <= 1):
        topology = "winged"
        evidence.append(f"{wings} wings present, no proper arms — winged topology")
    elif has_head and (arms >= 1 or hands >= 1):
        topology = "humanoid"
        evidence.append(f"head + {arms} arms + {hands} hands — humanoid topology")
    elif has_head:
        topology = "humanoid"
        evidence.append("head present, no limb art — degenerate humanoid (head-only character)")

    if tails >= 1 and topology in {"humanoid", "quadruped", "winged"}:
        modifiers.append("tailed")
        evidence.append(f"{tails} tail layer(s) — adding tailed modifier")
    if wings >= 1 and topology == "humanoid":
        modifiers.append("winged_humanoid")
        evidence.append("wings on humanoid — adding winged_humanoid modifier")

    return {
        "schema": "spine_slot_animation_topology_v1",
        "topology": topology,
        "modifiers": modifiers,
        "limb_counts": {
            "legs": legs,
            "arms": arms,
            "hands": hands,
            "wings": wings,
            "tentacles": tentacles,
            "body_segments": body_segments,
            "tails": tails,
        },
        "evidence": evidence,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Detect creature topology from layer interpretations.")
    p.add_argument("--interpretation", required=True,
                   help="Path to interpret_layers.py output JSON.")
    p.add_argument("--out", help="Optional output path; else print to stdout.")
    args = p.parse_args()
    interp = json.loads(Path(args.interpretation).read_text())
    result = detect_topology(interp)
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    print(text)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
