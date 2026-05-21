#!/usr/bin/env python3
"""Capture feedback on a built Spine package.

Usage patterns:

  # Accept a build as-is
  python capture_feedback.py <project_dir> --build <out_dir> --accept

  # Note a revision the user requested
  python capture_feedback.py <project_dir> --build <out_dir> --revise \
      --controls '{"bounce_strength": 1.4}' --note "art lead wanted more bouncy"

  # Reject a build (escape hatch — distillation excludes from defaults)
  python capture_feedback.py <project_dir> --build <out_dir> --reject \
      --note "WebGL preview shows hat seam; needs --composite-expressions"

Feedback is appended to LEARNING_LOG.jsonl. The pattern distiller picks it up
on the next `distill_patterns.py` run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import learning_log as ll
import project_context as pc


def main() -> int:
    p = argparse.ArgumentParser(description="Capture feedback on a built Spine package.")
    p.add_argument("project_dir", help="Project root (will host LEARNING_LOG.jsonl).")
    p.add_argument("--build", required=True, help="Path to the build's output directory.")
    disp = p.add_mutually_exclusive_group(required=True)
    disp.add_argument("--accept", action="store_true", help="Mark this build accepted as-is.")
    disp.add_argument("--revise", action="store_true", help="Mark this build revised; supply --controls / --note.")
    disp.add_argument("--reject", action="store_true", help="Mark this build rejected.")
    p.add_argument("--note", default="", help="Free-form user note.")
    p.add_argument("--controls", help="JSON of control overrides applied during the revision.")
    args = p.parse_args()

    disposition = "accepted" if args.accept else ("revised" if args.revise else "rejected")
    revisions: dict = {}
    if args.controls:
        revisions = json.loads(args.controls)

    payload = {
        "build_out_dir": str(Path(args.build).resolve()),
        "disposition": disposition,
        "note": args.note,
    }
    if revisions:
        payload["revisions_applied"] = revisions

    project_dir = Path(args.project_dir)
    ctx_path = pc.find_context(project_dir)
    ll.log_feedback(project_dir, payload, ctx_path)
    print(f"recorded {disposition} feedback for {args.build}")
    if ctx_path:
        print(f"  project context: {ctx_path}")
    print(f"  run 'distill_patterns.py {project_dir} --update-context' to roll learnings into defaults")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
