#!/usr/bin/env python3
"""Avatar state-machine animation generator.

Takes a rig_layout.json whose layers have semantic_role 'avatar_state' or
'state_part' (e.g. State0Idle.png, State0to1.png, State1Awarded.png,
State1Close.png, State1Idle.png, ...) and emits the full state-graph
animation set:

  State<N>Idle           — looping idle for state N (each state attachment
                            visible while others are hidden)
  State<N>to<N+1>        — transition fading state N → state N+1
  State<N+1>Awarded      — awarded beat (pulse + glow)
  State<N+1>Close        — close beat (settle back to idle)

The state model assumes one PNG per state-graph keyframe. The compiler shows
the right state attachment by toggling slot color / attachment timelines so
the runtime only sees one state visible at a time.

USE
  python build_avatar_states.py --layout <rig_layout.json> \
      --controls <controls.json> --out <avatar_animations.json>

The output schema mirrors compose_animations.py.

This is FIRST-PASS state-machine support: real production avatar rigs (with
expression layers, IK, mesh/deform, persistent state across spins) require
additional review. The animation names and transitions emitted here are the
deterministic proof of the state graph, suitable for review and approval.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path

FPS = 24

STATE_RE = re.compile(
    r"^state(?P<idx>\d+)(?P<kind>idle|to(?P<target>\d+)|awarded|close)?$",
    re.IGNORECASE,
)


def _parse_state_layer(name: str) -> dict | None:
    """Return {idx: int, kind: 'idle'|'transition'|'awarded'|'close'|'base', target: int?} or None."""
    stem = Path(name).stem
    # Strip any leading 'avatar_' or 'AVATAR_' prefix
    stem = re.sub(r"^avatar[_-]?", "", stem, flags=re.IGNORECASE)
    m = STATE_RE.match(stem)
    if not m:
        return None
    kind_raw = (m.group("kind") or "base").lower()
    if kind_raw.startswith("to"):
        return {
            "idx": int(m.group("idx")),
            "kind": "transition",
            "target": int(m.group("target")),
        }
    return {"idx": int(m.group("idx")), "kind": kind_raw, "target": None}


def _bone_for_state_layer(layout: dict, layer_name: str) -> str | None:
    for s in layout["slots"]:
        if s.get("semantic_role") in ("avatar_state", "meter_state", "state_part"):
            if s["attachment"].endswith("/" + Path(layer_name).stem) or s["attachment"] == "parts/" + Path(layer_name).stem:
                return s["bone"]
    return None


def _slot_for_state_layer(layout: dict, layer_name: str) -> dict | None:
    for s in layout["slots"]:
        if s.get("semantic_role") in ("avatar_state", "meter_state", "state_part"):
            if s["attachment"].endswith("/" + Path(layer_name).stem) or s["attachment"] == "parts/" + Path(layer_name).stem:
                return s
    return None


def _attachment_path(slot: dict) -> str:
    return slot["attachment"]


def _state_layer_name(slot: dict) -> str:
    return slot["attachment"].split("/")[-1]


def _is_stateish_slot(slot: dict) -> bool:
    name = _state_layer_name(slot)
    stem = Path(name).stem.lower()
    return (
        slot.get("semantic_role") in ("avatar_state", "meter_state", "state_part")
        or stem.startswith("state")
        or stem.startswith("avatar_state")
    )


def _collect_state_layers(layout: dict) -> tuple[list[tuple[dict, dict]], list[str]]:
    state_layers: list[tuple[dict, dict]] = []
    malformed: list[str] = []
    for slot in layout["slots"]:
        if not _is_stateish_slot(slot):
            continue
        parsed = _parse_state_layer(_state_layer_name(slot))
        if parsed is None:
            parsed = _parse_state_layer(slot["name"].replace("_slot", ""))
        if parsed is None:
            malformed.append(_state_layer_name(slot))
            continue
        state_layers.append((slot, parsed))
    return state_layers, malformed


def _avatar_event_name_for(kind: str, idx: int, target: int | None = None) -> str:
    if kind == "transition":
        return f"avatar/state_{idx}_to_{target}"
    return f"avatar/state_{idx}_{kind}"


def build_avatar_state_manifest(
    layout: dict,
    animations: dict[str, dict],
    *,
    expression_support: dict | None = None,
    physics_candidates: list[dict] | None = None,
    physics_constraints_emitted: int = 0,
    physics_preview_required: bool = False,
    physics_enabled: bool = False,
    ik_candidates_count: int = 0,
    ik_constraints_emitted: int = 0,
    ik_enabled: bool = False,
    event_timelines_emitted: bool = False,
) -> tuple[dict, list[str]]:
    state_layers, malformed = _collect_state_layers(layout)
    base_idle_slots = [(s, m) for s, m in state_layers if m["kind"] in ("idle", "base")]
    transition_slots = [(s, m) for s, m in state_layers if m["kind"] == "transition"]
    awarded_slots = [(s, m) for s, m in state_layers if m["kind"] == "awarded"]
    close_slots = [(s, m) for s, m in state_layers if m["kind"] == "close"]

    issues: list[str] = []
    for name in malformed:
        issues.append(f"avatar state layer {name!r} does not match State<N>Idle, State<N>to<M>, State<N>Awarded, or State<N>Close")
    if not state_layers:
        issues.append("avatar family requires State<N> state-frame layers")
    if not any(m["idx"] == 0 for _s, m in base_idle_slots):
        issues.append("avatar default state requires State0Idle or State0")
    state_counts: dict[int, int] = {}
    for _slot, meta in base_idle_slots:
        state_counts[meta["idx"]] = state_counts.get(meta["idx"], 0) + 1
    for idx, count in sorted(state_counts.items()):
        if count > 1:
            issues.append(f"duplicate avatar state id 'state_{idx}' from {count} idle/base layers")
    state_indices = set(state_counts)
    for _slot, meta in sorted(transition_slots, key=lambda item: (item[1]["idx"], item[1]["target"])):
        from_idx = meta["idx"]
        to_idx = meta["target"]
        if from_idx not in state_indices:
            issues.append(
                f"avatar transition State{from_idx}to{to_idx} references missing from_state state_{from_idx} "
                f"(requires State{from_idx}Idle or State{from_idx})"
            )
        if to_idx not in state_indices:
            issues.append(
                f"avatar transition State{from_idx}to{to_idx} references missing to_state state_{to_idx} "
                f"(requires State{to_idx}Idle or State{to_idx})"
            )
    for section_name, slots, suffix in (
        ("awarded beat", awarded_slots, "Awarded"),
        ("close beat", close_slots, "Close"),
    ):
        for _slot, meta in sorted(slots, key=lambda item: item[1]["idx"]):
            idx = meta["idx"]
            if idx not in state_indices:
                issues.append(
                    f"avatar {section_name} State{idx}{suffix} references missing state state_{idx} "
                    f"(requires State{idx}Idle or State{idx})"
                )

    states = []
    for slot, meta in sorted(base_idle_slots, key=lambda item: item[1]["idx"]):
        idx = meta["idx"]
        states.append({
            "id": f"state_{idx}",
            "index": idx,
            "slot": slot["name"],
            "attachment": _attachment_path(slot),
            "idle_animation": f"State{idx}Idle",
            "awarded_animation": f"State{idx}Awarded" if f"State{idx}Awarded" in animations else None,
            "close_animation": f"State{idx}Close" if f"State{idx}Close" in animations else None,
        })

    transitions = []
    for slot, meta in sorted(transition_slots, key=lambda item: (item[1]["idx"], item[1]["target"])):
        from_idx = meta["idx"]
        to_idx = meta["target"]
        transitions.append({
            "from_state": f"state_{from_idx}",
            "to_state": f"state_{to_idx}",
            "animation": f"State{from_idx}to{to_idx}",
            "slot": slot["name"],
            "attachment": _attachment_path(slot),
            "event_name": _avatar_event_name_for("transition", from_idx, to_idx),
            "event_time": 0.2,
        })

    awarded_beats = []
    for slot, meta in sorted(awarded_slots, key=lambda item: item[1]["idx"]):
        idx = meta["idx"]
        awarded_beats.append({
            "state": f"state_{idx}",
            "animation": f"State{idx}Awarded",
            "slot": slot["name"],
            "attachment": _attachment_path(slot),
            "event_name": _avatar_event_name_for("awarded", idx),
            "event_time": 0.6,
        })

    close_beats = []
    for slot, meta in sorted(close_slots, key=lambda item: item[1]["idx"]):
        idx = meta["idx"]
        close_beats.append({
            "state": f"state_{idx}",
            "animation": f"State{idx}Close",
            "slot": slot["name"],
            "attachment": _attachment_path(slot),
            "event_name": _avatar_event_name_for("close", idx),
            "event_time": 0.4,
        })

    event_names = sorted({
        beat["event_name"]
        for beat in [*transitions, *awarded_beats, *close_beats]
    })

    expression_info = expression_support or {}
    expression_enabled = bool(expression_info.get("enabled"))
    physics_candidate_count = len(physics_candidates or [])
    physics_status = "not_requested"
    if physics_constraints_emitted:
        physics_status = "constraints_emitted_review_required"
    elif physics_candidate_count:
        physics_status = "candidates_reported"
    elif physics_enabled:
        physics_status = "enabled_no_candidates"
    ik_status = "not_requested"
    if ik_constraints_emitted:
        ik_status = "constraints_emitted_review_required"
    elif ik_candidates_count:
        ik_status = "candidates_reported"
    elif ik_enabled:
        ik_status = "enabled_no_candidates"
    manifest = {
        "schema": "spine_slot_animation_avatar_state_manifest_v1",
        "default_state": "state_0" if not issues or any(m["idx"] == 0 for _s, m in base_idle_slots) else None,
        "states": states,
        "transitions": transitions,
        "awarded_beats": awarded_beats,
        "close_beats": close_beats,
        "animations": {
            "boot": "Avatar" if "Avatar" in animations else None,
            "idles": [state["idle_animation"] for state in states if state["idle_animation"] in animations],
            "transitions": [item["animation"] for item in transitions if item["animation"] in animations],
            "awarded": [item["animation"] for item in awarded_beats if item["animation"] in animations],
            "close": [item["animation"] for item in close_beats if item["animation"] in animations],
        },
        "event_names": event_names,
        "event_timelines_emitted": event_timelines_emitted,
        "expression_support": {
            "status": "composited_expression_proof" if expression_enabled else "not_requested",
            "composite_expressions_enabled": expression_enabled,
            "composited_expressions": list(expression_info.get("expressions", [])),
            "preview_required": bool(expression_info.get("preview_required")),
            "art_approval_required": expression_enabled,
            "art_approval_claimed": False,
        },
        "physics_candidates": physics_candidates or [],
        "physics_support": {
            "status": physics_status,
            "enabled": physics_enabled,
            "candidate_count": physics_candidate_count,
            "constraints_emitted": physics_constraints_emitted,
            "preview_required": physics_preview_required,
            "art_approval_required": bool(physics_candidate_count or physics_constraints_emitted),
            "art_approval_claimed": False,
        },
        "ik_support": {
            "status": ik_status,
            "enabled": ik_enabled,
            "candidate_count": ik_candidates_count,
            "constraints_emitted": ik_constraints_emitted,
            "art_approval_required": bool(ik_candidates_count or ik_constraints_emitted),
            "production_approval_claimed": False,
        },
        "runtime_required": True,
        "runtime_consumer_verified": False,
        "persistent_state_owner": "game_runtime",
        "persistent_state_claimed_in_spine": False,
        "persistent_state_claimed": False,
        "preview_required": True,
        "art_approval_required": True,
        "art_approval_claimed": False,
        "issues": issues,
    }
    return manifest, issues


def avatar_expected_events(manifest: dict) -> dict[tuple[str, str], float]:
    expected: dict[tuple[str, str], float] = {}
    for section in ("transitions", "awarded_beats", "close_beats"):
        for item in manifest.get(section, []):
            expected[(item["animation"], item["event_name"])] = float(item["event_time"])
    return expected


def compose_avatar_animations(layout: dict, ctrls: dict[str, float]) -> dict[str, dict]:
    """Walk the layout, find all state layers, and emit the full state graph."""
    # Index state layers by (idx, kind, target)
    state_layers, _malformed = _collect_state_layers(layout)

    if not state_layers:
        return {}

    # Group all state attachments — we need to hide all of them at any moment
    # except the one we're showing
    all_state_slots = [s for s, _ in state_layers]
    base_idle_slots = [(s, m) for s, m in state_layers if m["kind"] in ("idle", "base")]
    transition_slots = [(s, m) for s, m in state_layers if m["kind"] == "transition"]
    awarded_slots = [(s, m) for s, m in state_layers if m["kind"] == "awarded"]
    close_slots = [(s, m) for s, m in state_layers if m["kind"] == "close"]

    animations: dict[str, dict] = {}

    # Avatar root-pose: optional; emit a "State0Idle" animation that shows only
    # the State0 idle attachment, and one State<N>Idle per discovered idle.
    for slot, meta in base_idle_slots:
        idx = meta["idx"]
        name = f"State{idx}Idle"
        anim_slots: dict[str, dict] = {}
        for s in all_state_slots:
            if s["name"] == slot["name"]:
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffffff"},
                        {"time": 1.0, "color": "ffffffff"},
                    ]
                }
            else:
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffff00"},
                        {"time": 1.0, "color": "ffffff00"},
                    ]
                }
        # Also add a gentle scale pulse to the visible attachment
        bone = slot["bone"]
        anim_bones = {
            bone: {
                "scale": [
                    {"time": 0, "x": 1, "y": 1},
                    {"time": 0.5, "x": 1.02, "y": 1.02},
                    {"time": 1.0, "x": 1, "y": 1},
                ]
            }
        }
        animations[name] = {"bones": anim_bones, "slots": anim_slots}

    # Transitions: State<N>to<N+1>
    for slot, meta in transition_slots:
        from_idx = meta["idx"]
        to_idx = meta["target"]
        name = f"State{from_idx}to{to_idx}"
        dur = 0.4
        anim_slots: dict[str, dict] = {}
        # Make all state attachments invisible except: at t=0, the from-state idle
        # is visible; transition fades in mid-time; at t=dur, the to-state idle
        # is visible.
        from_idle = next((s for s, m in base_idle_slots if m["idx"] == from_idx), None)
        to_idle = next((s for s, m in base_idle_slots if m["idx"] == to_idx), None)
        for s in all_state_slots:
            if s["name"] == (from_idle["name"] if from_idle else None):
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffffff"},
                        {"time": dur * 0.3, "color": "ffffffff"},
                        {"time": dur * 0.7, "color": "ffffff00"},
                        {"time": dur, "color": "ffffff00"},
                    ]
                }
            elif s["name"] == slot["name"]:
                # the transition attachment itself shows briefly mid-way
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffff00"},
                        {"time": dur * 0.3, "color": "ffffffff"},
                        {"time": dur * 0.7, "color": "ffffffff"},
                        {"time": dur, "color": "ffffff00"},
                    ]
                }
            elif s["name"] == (to_idle["name"] if to_idle else None):
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffff00"},
                        {"time": dur * 0.3, "color": "ffffff00"},
                        {"time": dur * 0.7, "color": "ffffffff"},
                        {"time": dur, "color": "ffffffff"},
                    ]
                }
            else:
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffff00"},
                        {"time": dur, "color": "ffffff00"},
                    ]
                }
        animations[name] = {"bones": {}, "slots": anim_slots}

    # Awarded: scale-pulse + glow on the awarded state attachment
    for slot, meta in awarded_slots:
        idx = meta["idx"]
        name = f"State{idx}Awarded"
        dur = 1.2
        anim_slots: dict[str, dict] = {}
        for s in all_state_slots:
            if s["name"] == slot["name"]:
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffffff"},
                        {"time": dur, "color": "ffffffff"},
                    ]
                }
            else:
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffff00"},
                        {"time": dur, "color": "ffffff00"},
                    ]
                }
        bone = slot["bone"]
        anim_bones = {
            bone: {
                "scale": [
                    {"time": 0, "x": 1, "y": 1},
                    {"time": dur * 0.5, "x": 1.10, "y": 1.10},
                    {"time": dur, "x": 1, "y": 1},
                ],
                "translate": [
                    {"time": 0, "x": 0, "y": 0},
                    {"time": dur * 0.5, "x": 0, "y": 4},
                    {"time": dur, "x": 0, "y": 0},
                ],
            }
        }
        animations[name] = {"bones": anim_bones, "slots": anim_slots}

    # Close: settle back to idle (mirror of awarded)
    for slot, meta in close_slots:
        idx = meta["idx"]
        name = f"State{idx}Close"
        dur = 0.8
        anim_slots: dict[str, dict] = {}
        for s in all_state_slots:
            if s["name"] == slot["name"]:
                anim_slots[s["name"]] = {
                    "rgba": [
                        {"time": 0, "color": "ffffffff"},
                        {"time": dur * 0.5, "color": "ffffffff"},
                        {"time": dur, "color": "ffffff00"},
                    ]
                }
            else:
                idle = next((s2 for s2, m2 in base_idle_slots if m2["idx"] == idx), None)
                if idle and s["name"] == idle["name"]:
                    anim_slots[s["name"]] = {
                        "rgba": [
                            {"time": 0, "color": "ffffff00"},
                            {"time": dur * 0.5, "color": "ffffff00"},
                            {"time": dur, "color": "ffffffff"},
                        ]
                    }
                else:
                    anim_slots[s["name"]] = {
                        "rgba": [
                            {"time": 0, "color": "ffffff00"},
                            {"time": dur, "color": "ffffff00"},
                        ]
                    }
        animations[name] = {"bones": {}, "slots": anim_slots}

    # Top-level Avatar animation: pick state 0 idle as the default boot animation
    if base_idle_slots:
        s0 = next((s for s, m in base_idle_slots if m["idx"] == 0), None) or base_idle_slots[0][0]
        avatar_slots: dict[str, dict] = {}
        for s in all_state_slots:
            avatar_slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": "ffffffff" if s["name"] == s0["name"] else "ffffff00"},
                    {"time": 1.0, "color": "ffffffff" if s["name"] == s0["name"] else "ffffff00"},
                ]
            }
        animations["Avatar"] = {"bones": {}, "slots": avatar_slots}

    return animations


def main() -> int:
    p = argparse.ArgumentParser(description="Compose avatar state-machine animations.")
    p.add_argument("--layout", required=True)
    p.add_argument("--controls", help="Optional controls JSON path.")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    layout = json.loads(Path(args.layout).read_text())
    ctrls = json.loads(Path(args.controls).read_text()) if args.controls else {}
    animations = compose_avatar_animations(layout, ctrls)

    out = {
        "schema": "spine_slot_animation_animations_v1",
        "family": "avatar",
        "fps": FPS,
        "animations": animations,
    }
    out_path = ensure_safe_write_path(Path(args.out), "out")
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {args.out}")
    print(f"  animations: {list(animations.keys())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
