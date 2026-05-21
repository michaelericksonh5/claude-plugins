#!/usr/bin/env python3
"""Distill the learning log into PATTERNS.md + update the context's
preferred-defaults block.

Patterns identified:
  - Most-common controls per family (median of accepted builds)
  - Most-used flags (e.g., always-on composite_expressions for this project)
  - Recurring validation failures (so the skill can preempt them)
  - Recurring user revisions ("this user always asks for more bouncy" — bake it in)
  - Naming overrides specific to this project

The distillation is non-destructive: it only updates the context's
`preferred_defaults` and `feedback_summary` blocks. Hand-written context
fields (project_name, role_overrides, naming) are not touched.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import learning_log as ll
import project_context as pc

PATTERNS_FILENAME = "PATTERNS.md"


def distill(project_dir: Path) -> dict:
    entries = ll.read_log(project_dir)
    builds = [e["build"] for e in entries if e.get("event_type") == "build" and e.get("build")]
    feedback = [e["feedback"] for e in entries if e.get("event_type") == "feedback" and e.get("feedback")]
    failures = [e["validation_failure"] for e in entries if e.get("event_type") == "validation_failure"]

    # Accepted builds (no feedback marking them revised/rejected)
    accepted_dirs = {f["build_out_dir"] for f in feedback if f.get("disposition") == "accepted"}
    revised_dirs = {f["build_out_dir"] for f in feedback if f.get("disposition") == "revised"}

    # Controls per family — median of accepted builds (fall back to all builds if no accepted)
    controls_by_family: dict[str, list[dict]] = defaultdict(list)
    for b in builds:
        fam = b.get("family")
        if not fam:
            continue
        ctrls = b.get("controls_applied") or {}
        # If we have explicit acceptance info, prefer accepted builds
        if accepted_dirs:
            if b.get("out_dir") in accepted_dirs:
                controls_by_family[fam].append(ctrls)
        else:
            controls_by_family[fam].append(ctrls)

    median_controls: dict[str, dict[str, float]] = {}
    for fam, ctrl_list in controls_by_family.items():
        if not ctrl_list:
            continue
        keys = set()
        for c in ctrl_list:
            keys.update(c.keys())
        medians: dict[str, float] = {}
        for k in keys:
            values = [c[k] for c in ctrl_list if isinstance(c.get(k), (int, float))]
            if not values:
                continue
            med = statistics.median(values)
            if abs(med - 1.0) > 0.05:  # only emit non-default values
                medians[k] = round(med, 3)
        if medians:
            median_controls[fam] = medians

    # Flag frequency
    flag_counts: Counter = Counter()
    for b in builds:
        for flag in b.get("flags_enabled", []):
            flag_counts[flag] += 1
    total_builds = max(1, len(builds))
    common_flags = {flag: True for flag, c in flag_counts.items() if c / total_builds >= 0.5}

    # Recurring failures
    failure_summary: Counter = Counter()
    for f in failures:
        for err in f.get("errors", []):
            # Categorize by the first ~60 chars of the error message
            key = err[:60]
            failure_summary[key] += 1
    common_failures = [{"error": k, "occurrences": c} for k, c in failure_summary.most_common(5)]

    # Common revisions
    revision_summary: Counter = Counter()
    for fb in feedback:
        if fb.get("disposition") != "revised":
            continue
        for k, v in (fb.get("revisions_applied") or {}).items():
            revision_summary[k] += 1
    common_revisions = [{"control": k, "occurrences": c} for k, c in revision_summary.most_common(5)]

    return {
        "total_builds": len(builds),
        "accepted_builds": len(accepted_dirs),
        "revised_builds": len(revised_dirs),
        "median_controls": median_controls,
        "common_flags": common_flags,
        "common_failures": common_failures,
        "common_revisions": common_revisions,
    }


def write_patterns_md(project_dir: Path, summary: dict) -> Path:
    lines: list[str] = []
    lines.append("# Project Patterns (auto-distilled)")
    lines.append("")
    lines.append(f"- Total builds: {summary['total_builds']}")
    lines.append(f"- Accepted builds: {summary['accepted_builds']}")
    lines.append(f"- Revised builds: {summary['revised_builds']}")
    lines.append("")

    lines.append("## Median controls per family (across accepted builds)")
    if summary["median_controls"]:
        for fam, ctrls in summary["median_controls"].items():
            lines.append(f"- **{fam}**: " + ", ".join(f"`{k}={v}`" for k, v in ctrls.items()))
    else:
        lines.append("- (none yet — controls are default 1.0)")
    lines.append("")

    lines.append("## Flags commonly enabled (≥50% of builds)")
    if summary["common_flags"]:
        for flag in summary["common_flags"]:
            lines.append(f"- `--{flag.replace('_', '-')}`")
    else:
        lines.append("- (none yet)")
    lines.append("")

    if summary["common_revisions"]:
        lines.append("## Recurring revisions (user asks for these often)")
        for r in summary["common_revisions"]:
            lines.append(f"- `{r['control']}` revised {r['occurrences']} times")
        lines.append("")
        lines.append("Consider rolling these into `preferred_defaults` for this project.")
        lines.append("")

    if summary["common_failures"]:
        lines.append("## Recurring validation failures")
        for f in summary["common_failures"]:
            lines.append(f"- `{f['error']}` × {f['occurrences']}")
        lines.append("")
        lines.append("Investigate root cause; consider a context override to preempt these.")
        lines.append("")

    out_path = project_dir / PATTERNS_FILENAME
    out_path.write_text("\n".join(lines) + "\n")
    return out_path


def update_context_defaults(ctx_path: Path, summary: dict) -> None:
    ctx = pc.load_context(ctx_path)
    # Roll median controls into preferred defaults (only if there are accepted samples)
    if summary["accepted_builds"] > 0 and summary["median_controls"]:
        ctx.setdefault("preferred_defaults", {}).setdefault("controls", {})
        for fam, ctrls in summary["median_controls"].items():
            existing = ctx["preferred_defaults"]["controls"].get(fam, {})
            existing.update(ctrls)
            ctx["preferred_defaults"]["controls"][fam] = existing
    # Roll common flags
    ctx.setdefault("preferred_defaults", {}).setdefault("flags", {})
    for flag in summary["common_flags"]:
        ctx["preferred_defaults"]["flags"][flag] = True
    # Feedback summary
    ctx["feedback_summary"] = {
        "successful_builds": summary["accepted_builds"],
        "revised_builds": summary["revised_builds"],
        "common_revisions": summary["common_revisions"],
    }
    import datetime as _dt
    ctx["history"]["last_distilled"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    pc.save_context(ctx_path, ctx)


def main() -> int:
    p = argparse.ArgumentParser(description="Distill the learning log into PATTERNS.md.")
    p.add_argument("dir", help="Project root containing LEARNING_LOG.jsonl.")
    p.add_argument("--update-context", action="store_true",
                   help="Also roll median controls and common flags into PROJECT_CONTEXT.json.")
    args = p.parse_args()

    project_dir = Path(args.dir)
    summary = distill(project_dir)
    patterns_path = write_patterns_md(project_dir, summary)
    print(f"wrote {patterns_path}")
    print(f"  total_builds={summary['total_builds']}")
    print(f"  accepted={summary['accepted_builds']}, revised={summary['revised_builds']}")
    print(f"  families with learned defaults: {list(summary['median_controls'].keys())}")

    if args.update_context:
        ctx_path = pc.find_context(project_dir)
        if not ctx_path:
            print("warning: no PROJECT_CONTEXT.json found; bootstrapping one")
            ctx_path = pc.bootstrap_context(project_dir)
        update_context_defaults(ctx_path, summary)
        print(f"  updated defaults in {ctx_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
