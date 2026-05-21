#!/usr/bin/env python3
"""Group numbered VFX frames into Spine 4.2 Sequence attachments.

Slot games are full of frame-sequence VFX: a sparkle that animates through
12 frames, a coin-flip with 8 frames, a fireball with 30 frames. Each frame
is a separate PNG layer with a numeric suffix:

  HP1_sparkle_001.png
  HP1_sparkle_002.png
  ...
  HP1_sparkle_012.png

Spine 4.2 added native Sequence attachment support: one slot holds a
sequence, the runtime advances the frame index automatically. This is more
efficient than 12 separate attachments swapped by an attachment timeline.

JSON SHAPE
  In the slot's attachment definition:
    {
      "type": "region",                  // or "mesh"
      "path": "HP1_sparkle_",            // frame prefix; runtime appends 001, 002...
      "sequence": {
        "count": 12,                     // total frames
        "start": 1,                      // starting frame index
        "digits": 3,                     // zero-padded width (001 vs 1)
        "setup": 0                       // which frame shows at setup
      },
      "width": 64,
      "height": 64
    }

The attachment's `path` is the frame prefix; the runtime looks up
`<path>001`, `<path>002`, etc. from the atlas at runtime.

ANIMATION TIMELINE
  A sequence timeline on the slot drives the frame index over time:
    "slots": {
      "sparkle_slot": {
        "sequence": [
          { "time": 0,    "delay": 0, "mode": "forward",  "index": 0  },
          { "time": 1.0,  "delay": 0, "mode": "hold" }
        ]
      }
    }

  Modes: hold, once, loop, pingpong, onceReverse, loopReverse, pingpongReverse

USE
  python sequence_attachments.py --layer-dir <path> --out <sequences.json>

DETECTION
  Walks the layer-dir for PNGs matching `<base>_(\d{2,4})\.png` and groups by
  base. Returns:
    {
      "<base>": {
        "frames": ["<base>_001.png", "<base>_002.png", ...],
        "count": N,
        "start": 1,
        "digits": 3
      },
      ...
    }
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

FRAME_RE = re.compile(r"^(?P<base>.+?)_(?P<idx>\d{2,4})$")


def detect_sequences(layer_dir: Path) -> dict[str, dict]:
    """Walk the layer dir and group numbered PNGs into sequence specs."""
    groups: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for p in sorted(layer_dir.iterdir()):
        if not p.is_file() or p.suffix.lower() != ".png":
            continue
        m = FRAME_RE.match(p.stem)
        if not m:
            continue
        base = m.group("base")
        idx = int(m.group("idx"))
        digits = len(m.group("idx"))
        groups[base].append((idx, p.name))

    sequences: dict[str, dict] = {}
    for base, frames in groups.items():
        if len(frames) < 2:
            continue  # single-frame isn't a sequence
        frames.sort()
        # Verify the sequence is contiguous (no holes)
        indices = [idx for idx, _ in frames]
        if max(indices) - min(indices) + 1 != len(indices):
            print(f"  warning: sequence {base!r} has gaps: indices {indices}; skipping")
            continue
        # Recover digit width from the file name's index
        digit_width = len(re.match(FRAME_RE, frames[0][1].replace(".png", "")).group("idx"))
        sequences[base] = {
            "frames": [name for _, name in frames],
            "count": len(frames),
            "start": min(indices),
            "digits": digit_width,
        }
    return sequences


def build_sequence_spec(base_name: str, info: dict, setup_index: int | None = None) -> dict:
    """Return the JSON spec for an attachment's `sequence` block."""
    return {
        "count": info["count"],
        "start": info["start"],
        "digits": info["digits"],
        "setup": setup_index if setup_index is not None else 0,
    }


def build_sequence_timeline(
    duration: float,
    mode: str = "loop",
    delay: float = 0.0,
    setup_index: int = 0,
) -> list[dict]:
    """Build a slot.sequence timeline for an animation.

    Modes:
      - hold:       hold setup index
      - once:       play once forward, then hold
      - loop:       play repeatedly forward
      - pingpong:   forward then reverse, repeating
      - onceReverse, loopReverse, pingpongReverse: same but reversed
    """
    return [
        {"time": 0, "mode": mode, "delay": delay, "index": setup_index},
        {"time": duration, "mode": "hold"},
    ]


def main() -> int:
    p = argparse.ArgumentParser(description="Detect numbered VFX frame sequences in a layer dir.")
    p.add_argument("--layer-dir", required=True, help="Folder of PNG layers.")
    p.add_argument("--out", required=True, help="Output sequence specs JSON.")
    args = p.parse_args()
    sequences = detect_sequences(Path(args.layer_dir))
    Path(args.out).write_text(json.dumps(sequences, indent=2))
    print(f"wrote {args.out}")
    print(f"  detected {len(sequences)} sequence(s)")
    for base, info in sequences.items():
        print(f"    {base}: {info['count']} frames ({info['start']}-{info['start']+info['count']-1}, digits={info['digits']})")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
