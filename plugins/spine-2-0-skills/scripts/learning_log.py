#!/usr/bin/env python3
"""Append-only learning log for the spine-slot-animation skill.

Every build of a Spine package writes one line to LEARNING_LOG.jsonl. Every
feedback event (the user accepting, revising, or rejecting a result) also
writes one line. The log is JSONL so it can be appended atomically without
parsing the whole file.

The log is the source of truth for the pattern distiller. It captures
enough detail to:
  - track defaults the user converges on
  - spot recurring failure modes
  - identify project-specific overrides
  - measure the skill's effectiveness over time

ENTRY SCHEMA (one JSON object per line):
{
  "schema": "spine_slot_animation_learning_log_entry_v1",
  "timestamp": "2026-05-17T16:30:00Z",
  "event_type": "build" | "feedback" | "validation_failure" | "context_update",
  "project_context_path": "...",
  "build": {                              // present when event_type == "build"
    "layer_dir": "...",
    "family": "hp_symbol",
    "rank": 3,
    "controls_applied": {...},
    "flags_enabled": ["composite_expressions", "render_qa_frames"],
    "out_dir": "...",
    "validation_status": "ok" | "failed",
    "bones_count": 10,
    "slots_count": 9,
    "animations": ["HP3", "HP3idle", ...]
  },
  "feedback": {                           // present when event_type == "feedback"
    "build_out_dir": "...",
    "disposition": "accepted" | "revised" | "rejected",
    "note": "free-form user note",
    "revisions_applied": {...}            // if disposition == "revised"
  },
  "validation_failure": {                 // present when event_type == "validation_failure"
    "errors": ["..."],
    "warnings": ["..."],
    "package_dir": "..."
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

LOG_FILENAME = "LEARNING_LOG.jsonl"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def log_entry(project_dir: Path, event_type: str, payload: dict, project_context_path: Path | None = None) -> None:
    """Append a single entry. Creates the log file if missing."""
    ensure_safe_write_path(project_dir, "project_dir")
    project_dir.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "schema": "spine_slot_animation_learning_log_entry_v1",
        "timestamp": _now(),
        "event_type": event_type,
        "project_context_path": str(project_context_path) if project_context_path else None,
    }
    entry[event_type] = payload
    log_path = project_dir / LOG_FILENAME
    ensure_safe_write_path(log_path, "log path")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_build(project_dir: Path, build_payload: dict, project_context_path: Path | None = None) -> None:
    log_entry(project_dir, "build", build_payload, project_context_path)


def log_feedback(project_dir: Path, feedback_payload: dict, project_context_path: Path | None = None) -> None:
    log_entry(project_dir, "feedback", feedback_payload, project_context_path)


def log_validation_failure(project_dir: Path, failure_payload: dict, project_context_path: Path | None = None) -> None:
    log_entry(project_dir, "validation_failure", failure_payload, project_context_path)


def log_context_update(project_dir: Path, update_payload: dict, project_context_path: Path | None = None) -> None:
    log_entry(project_dir, "context_update", update_payload, project_context_path)


def read_log(project_dir: Path) -> list[dict]:
    """Read all entries. Returns [] if the log doesn't exist."""
    log_path = project_dir / LOG_FILENAME
    if not log_path.exists():
        return []
    out: list[dict] = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Append a learning-log entry.")
    p.add_argument("dir", help="Project root.")
    p.add_argument("--event", required=True,
                   choices=["build", "feedback", "validation_failure", "context_update"])
    p.add_argument("--payload", required=True, help="JSON payload file path or inline JSON.")
    p.add_argument("--context-path", help="Optional project-context path to record.")
    args = p.parse_args()

    payload_arg = args.payload
    payload_path = Path(payload_arg)
    if payload_path.is_file():
        payload = json.loads(payload_path.read_text())
    else:
        payload = json.loads(payload_arg)
    ctx_path = Path(args.context_path) if args.context_path else None
    log_entry(Path(args.dir), args.event, payload, ctx_path)
    print(f"appended {args.event} entry to {Path(args.dir) / LOG_FILENAME}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
