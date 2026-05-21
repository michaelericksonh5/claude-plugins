#!/usr/bin/env python3
"""Per-project context for the spine-slot-animation skill.

A `PROJECT_CONTEXT.json` lives at the project root (e.g., next to a folder of
PSDs or a research/ tree). The skill reads it on every invocation and uses
it to:

  - apply preferred defaults the user has converged on (e.g., bounce=1.1 by
    default for this game's HP characters)
  - honor naming conventions specific to this game (e.g., the rank ordering
    for jackpot tiers — GRAND/MAJOR/MINOR/MINI vs custom)
  - skip steps that aren't relevant (e.g., this game has no avatars; the
    skill should not classify anything as 'avatar')
  - pre-fill controls / events / IK plans from learned patterns

If the context file is missing on first invocation, the skill bootstraps a
minimal one from the family classification and the inputs.

SCHEMA (PROJECT_CONTEXT.json)
{
  "schema": "spine_slot_animation_project_context_v1",
  "project_name": "Santa Pop Win / 4451 Buffalo Pop & Win Clone",
  "game_id": "4451",
  "studio_id": "h5g",
  "spine_version": "4.3.04",
  "doc_dimensions": {"width": 178, "height": 178},
  "fps": 24,
  "naming": {
    "hp_pattern": "HP{rank}",
    "lp_pattern": "LP{rank}",
    "jackpot_tier_order": ["GRAND", "MAJOR", "MINOR", "MINI"]
  },
  "role_overrides": {
    "<symbol_code>": "<recipe_family>"   // override classification for a specific symbol
  },
  "preferred_defaults": {
    "controls": {                          // family → controls JSON
      "hp_symbol": {"bounce_strength": 1.1, "motion_strength": 1.05}
    },
    "flags": {                             // gated features turned on by default
      "composite_expressions": false,
      "render_qa_frames": true,
      "enable_ik": false,
      "enable_events": false
    }
  },
  "motion_profile_fit": {                  // family → fitted amplitudes from real exports
    "hp_symbol": {"translate_px_max": 3.0, "rotate_deg_max": 5.0, "scale_max": 1.04}
  },
  "feedback_summary": {                    // distilled from LEARNING_LOG.jsonl
    "successful_builds": 0,
    "revised_builds": 0,
    "common_revisions": []
  },
  "history": {                             // pointers to logs and patterns
    "log_path": "LEARNING_LOG.jsonl",
    "patterns_path": "PATTERNS.md",
    "last_distilled": null
  }
}
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path

CONTEXT_FILENAME = "PROJECT_CONTEXT.json"


def default_context(project_name: str = "(unnamed project)") -> dict:
    return {
        "schema": "spine_slot_animation_project_context_v1",
        "project_name": project_name,
        "game_id": None,
        "studio_id": None,
        "spine_version": "4.3.04",
        "doc_dimensions": {"width": None, "height": None},
        "fps": 24,
        "naming": {
            "hp_pattern": "HP{rank}",
            "lp_pattern": "LP{rank}",
            "jackpot_tier_order": ["GRAND", "MAJOR", "MINOR", "MINI"],
        },
        "role_overrides": {},
        "preferred_defaults": {
            "controls": {},
            "flags": {
                "composite_expressions": False,
                "render_qa_frames": False,
                "enable_ik": False,
                "enable_events": False,
                "enable_transform_constraints": False,
            },
        },
        "motion_profile_fit": {},
        "feedback_summary": {
            "successful_builds": 0,
            "revised_builds": 0,
            "common_revisions": [],
        },
        "history": {
            "log_path": "LEARNING_LOG.jsonl",
            "patterns_path": "PATTERNS.md",
            "last_distilled": None,
            "bootstrapped_at": None,
        },
    }


def find_context(start_dir: Path, max_parents: int = 5) -> Path | None:
    """Walk up from start_dir to find a PROJECT_CONTEXT.json. Returns the path
    or None if not found within max_parents levels."""
    cur = start_dir.resolve()
    for _ in range(max_parents + 1):
        candidate = cur / CONTEXT_FILENAME
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def load_context(path: Path) -> dict:
    return json.loads(path.read_text())


def save_context(path: Path, ctx: dict) -> None:
    ensure_safe_write_path(path, "context path")
    path.write_text(json.dumps(ctx, indent=2))


def bootstrap_context(project_dir: Path, project_name: str | None = None) -> Path:
    """Create a default PROJECT_CONTEXT.json in project_dir. Returns the path."""
    ensure_safe_write_path(project_dir, "project_dir")
    project_dir.mkdir(parents=True, exist_ok=True)
    ctx = default_context(project_name or project_dir.name)
    ctx["history"]["bootstrapped_at"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    path = project_dir / CONTEXT_FILENAME
    save_context(path, ctx)
    return path


def merge_overrides(ctx: dict, overrides: dict) -> dict:
    """Deep-merge an overrides dict into the context. Returns the merged ctx."""
    def _deep_merge(base, top):
        for k, v in top.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                _deep_merge(base[k], v)
            else:
                base[k] = v
        return base
    _deep_merge(ctx, overrides)
    return ctx


def apply_to_args(ctx: dict, args: argparse.Namespace) -> dict:
    """Apply context defaults to argparse args where the user didn't override.

    Returns a dict describing what was applied (for logging / transparency).
    """
    applied: dict[str, Any] = {}
    flags = ctx.get("preferred_defaults", {}).get("flags", {})
    for name, key in [
        ("composite_expressions", "composite_expressions"),
        ("render_qa_frames", "render_qa_frames"),
        ("enable_ik", "enable_ik"),
        ("enable_transform_constraints", "enable_transform_constraints"),
    ]:
        if flags.get(name) and not getattr(args, key, False):
            setattr(args, key, True)
            applied[key] = True

    # Doc dimensions: apply only when user hasn't supplied
    dd = ctx.get("doc_dimensions") or {}
    if getattr(args, "doc_width", None) is None and dd.get("width"):
        args.doc_width = float(dd["width"])
        applied["doc_width"] = args.doc_width
    if getattr(args, "doc_height", None) is None and dd.get("height"):
        args.doc_height = float(dd["height"])
        applied["doc_height"] = args.doc_height
    return applied


def family_default_controls(ctx: dict, family: str) -> dict:
    """Return preferred-default controls for a family (may be empty)."""
    return dict(ctx.get("preferred_defaults", {}).get("controls", {}).get(family, {}))


def main() -> int:
    p = argparse.ArgumentParser(description="Manage per-project spine-slot-animation context.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create a PROJECT_CONTEXT.json in a directory.")
    p_init.add_argument("dir", help="Project root directory.")
    p_init.add_argument("--name", help="Project name.")

    p_show = sub.add_parser("show", help="Print the current context for a project.")
    p_show.add_argument("dir", help="Project root (or any descendant).")

    p_set = sub.add_parser("set", help="Apply an overrides JSON file to the context.")
    p_set.add_argument("dir", help="Project root.")
    p_set.add_argument("--overrides", required=True, help="JSON file with deep-merged overrides.")

    args = p.parse_args()
    cwd = Path(args.dir)

    if args.cmd == "init":
        path = bootstrap_context(cwd, args.name)
        print(f"bootstrapped context at {path}")
        return 0
    if args.cmd == "show":
        ctx_path = find_context(cwd)
        if not ctx_path:
            print(f"no PROJECT_CONTEXT.json found near {cwd}")
            return 1
        ctx = load_context(ctx_path)
        print(f"# {ctx_path}")
        print(json.dumps(ctx, indent=2))
        return 0
    if args.cmd == "set":
        ctx_path = find_context(cwd)
        if not ctx_path:
            ctx_path = bootstrap_context(cwd)
        ctx = load_context(ctx_path)
        overrides = json.loads(Path(args.overrides).read_text())
        merge_overrides(ctx, overrides)
        save_context(ctx_path, ctx)
        print(f"merged overrides into {ctx_path}")
        return 0
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
