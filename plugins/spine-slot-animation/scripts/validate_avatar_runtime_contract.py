#!/usr/bin/env python3
"""Validate avatar runtime ownership/state/event contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path

SCHEMA = "spine_slot_animation_avatar_runtime_contract_report_v1"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if contract.get("schema") != "spine_slot_animation_avatar_runtime_contract_v1":
        errors.append("schema must be spine_slot_animation_avatar_runtime_contract_v1")
    owner = contract.get("runtime_owner")
    if not isinstance(owner, dict) or not owner.get("team") or not owner.get("approver"):
        errors.append("runtime_owner.team and runtime_owner.approver are required")
    states = contract.get("states")
    if not isinstance(states, list) or not states:
        errors.append("at least one avatar state is required")
        state_ids: set[int] = set()
    else:
        state_ids = set()
        for state in states:
            if not isinstance(state, dict):
                errors.append("state entries must be objects")
                continue
            state_id = state.get("id")
            if not isinstance(state_id, int):
                errors.append("state.id must be an integer")
                continue
            if state_id in state_ids:
                errors.append(f"duplicate state id: {state_id}")
            state_ids.add(state_id)
            if not state.get("idle_animation"):
                errors.append(f"state {state_id} missing idle_animation")
    default_state = contract.get("default_state")
    if isinstance(default_state, int) and default_state not in state_ids:
        errors.append("default_state must exist in states")
    for transition in contract.get("transitions") or []:
        if transition.get("from") not in state_ids or transition.get("to") not in state_ids:
            errors.append(f"transition references unknown state: {transition}")
    event_names = set()
    for event in contract.get("events") or []:
        name = event.get("name")
        if not name:
            errors.append("event.name is required")
            continue
        if name in event_names:
            errors.append(f"duplicate event name: {name}")
        event_names.add(name)
        if not event.get("consumer"):
            errors.append(f"event {name} missing consumer")
    acceptance = contract.get("runtime_acceptance")
    if not isinstance(acceptance, dict):
        errors.append("runtime_acceptance is required")
    elif not acceptance.get("verified"):
        errors.append("runtime_acceptance.verified must be true before avatar runtime claims")
    return {
        "schema": SCHEMA,
        "status": "ok" if not errors else "blocked",
        "errors": errors,
        "state_count": len(state_ids),
        "event_count": len(event_names),
        "runtime_consumer_verified": not errors and bool(contract.get("runtime_acceptance", {}).get("verified")),
        "claim_boundary": "Avatar runtime claims require game-owner state/event consumption proof, not only Spine data.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate avatar runtime contract JSON.")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_contract(_load_json(args.contract))
    out = ensure_safe_write_path(args.out, "avatar runtime contract report")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
