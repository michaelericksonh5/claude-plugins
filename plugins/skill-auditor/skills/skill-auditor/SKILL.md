---
name: skill-auditor
description: Audit a skill's SKILL.md and bundled resources to determine whether it is ready to use. Use this skill when a user asks you to audit, review, check, or validate a skill they've built or are about to install. Trigger on phrases like "audit my skill", "is this skill ready", "check my skill", "review this skill", "validate my skill", or when the user provides a path to a skill directory and wants a quality assessment. Also trigger when a user asks whether a skill "looks good" or is "ready to deploy". Do NOT trigger for general code review, PR review, or evaluating non-skill artifacts — this skill is specifically for assessing Claude skill files.
---

# Skill Auditor

Audit a skill directory against a standard 8-dimension rubric and produce a structured report with an overall status, per-dimension findings, priority fixes, and a verdict.

## Overall statuses

- **READY** — All required dimensions pass. Skill is deployable as-is.
- **NEEDS WORK** — One or more dimensions fail, but the skill is structurally present and could be fixed.
- **DRAFT** — The skill is incomplete or has placeholder content. Do not use until resolved.

## The 8 audit dimensions

| # | Dimension | What to check |
|---|-----------|---------------|
| 1 | Frontmatter | YAML is valid; `name` and `description` fields are present |
| 2 | Description quality | Description includes specific trigger phrases, defines scope, avoids generic language |
| 3 | Instruction clarity | Steps are imperative, logical, concrete; minimal unexplained ALL-CAPS directives |
| 4 | Reference integrity | Every file referenced in SKILL.md exists on disk in the skill directory |
| 5 | Completeness | No `TODO`, `FIXME`, `TBD`, `[INSERT`, or other placeholder markers anywhere in the skill |
| 6 | Output specification | The skill defines what Claude should produce: format, structure, and delivery method |
| 7 | Evals coverage | An `evals/` directory exists with test cases (SKIP — not a blocker — if absent) |
| 8 | Security / content | No malicious code, exploit patterns, or content that would surprise a reasonable user |

Per-dimension statuses: **PASS**, **FAIL**, **WARN** (concern but not blocking), **SKIP** (not applicable or optional).

## How to audit

### Step 1: Read the SKILL.md

Read `SKILL.md` in the provided skill directory. If the file does not exist, set all applicable dimensions to FAIL and set overall status to DRAFT. Document the missing file as the first priority fix.

### Step 2: Check frontmatter (Dimension 1)

Parse the YAML frontmatter block. Verify:
- `name` is present and follows kebab-case
- `description` is present and non-empty

FAIL if either field is missing or the YAML is malformed.

### Step 3: Assess description quality (Dimension 2)

Read the description value. A passing description:
- Names what the skill does concretely (not just "helps with things")
- Includes at least 2–3 specific trigger phrases or request patterns that a real user would type
- Defines scope or names what the skill does NOT do (either in the description or in the SKILL.md body)

FAIL if the description is vague, uses only generic language, or contains no trigger context. WARN if trigger phrases are present but thin.

### Step 4: Assess instruction clarity (Dimension 3)

Read the body of SKILL.md. A passing body:
- Uses numbered steps or clear imperative phrasing ("Do X", "Produce Y")
- Avoids unexplained ALL-CAPS directives (MUST, ALWAYS, NEVER used as emphasis substitutes rather than genuine constraints with stated rationale)
- Has a logical flow — does not jump between unrelated concerns

WARN if ALL-CAPS are overused without rationale. FAIL if the instructions are so ambiguous that a model following them would have no clear path.

### Step 5: Check reference integrity (Dimension 4)

Scan SKILL.md for any file paths referenced in the body (e.g., `scripts/foo.py`, `references/bar.md`, `assets/template.xlsx`). For each path found:
- Check whether the file exists in the skill directory
- Record each missing file with its severity (HIGH if the skill cannot function without it)

FAIL if any referenced file is missing. PASS if no external files are referenced (single-file skill is fine).

### Step 6: Check completeness (Dimension 5)

Scan all files in the skill directory for placeholder markers: `TODO`, `FIXME`, `TBD`, `[INSERT`, `<placeholder>`, HTML comments with stub content. Use case-insensitive search.

FAIL if any placeholder is found. PASS if none are found.

### Step 7: Check output specification (Dimension 6)

Determine whether the skill tells Claude what to produce:
- Is there a report template, output format, or delivery instruction?
- Would a model following this skill know what the final artifact looks like?

FAIL if no output format is defined. WARN if the format exists but is underspecified (e.g., "write a report" with no structure).

### Step 8: Check evals (Dimension 7)

Check whether an `evals/` directory exists inside the skill folder.

SKIP (not FAIL) if no `evals/` directory exists — evals are recommended but not required. Note in the report that adding test cases is recommended for skills with verifiable outputs.

### Step 9: Check security/content (Dimension 8)

Read through the full skill content. Flag any:
- Executable payloads or exploit code
- Instructions to exfiltrate data or access unauthorized resources
- Content that would surprise a reasonable user given the skill's stated purpose

PASS in the normal case. FAIL if any concerning content is found.

## Report format

Always produce a report with this structure:

```
# Skill Audit Report

**Skill path:** `<path>`
**Skill name:** `<name from frontmatter, or "unknown">`
**Audit date:** <today>
**Auditor:** Claude Code (with skill-auditor guidance)

---

## Overall Status: <READY | NEEDS WORK | DRAFT>

<1–3 sentence summary of the finding>

---

## Dimension Breakdown

| # | Dimension | Status | Notes |
|---|-----------|--------|-------|
| 1 | Frontmatter | <status> | <brief note> |
| 2 | Description quality | <status> | <brief note> |
| 3 | Instruction clarity | <status> | <brief note> |
| 4 | Reference integrity | <status> | <brief note> |
| 5 | Completeness | <status> | <brief note> |
| 6 | Output specification | <status> | <brief note> |
| 7 | Evals coverage | <status> | <brief note> |
| 8 | Security / content | <status> | <brief note> |

---

## Dimension Details

<For each non-PASS dimension, write a short section with specific findings>

---

## Priority Fixes

<Group by priority: HIGH (must fix before deploying), MEDIUM, LOW>
<Each fix is concrete and actionable — not just "improve the description" but
 "add 3 trigger phrases covering X, Y, Z">

<Omit this section if status is READY>

---

## Strengths

<2–4 specific things the skill does well — always include this section>

---

## Verdict

<READY | NEEDS WORK | DRAFT> — <one sentence explaining the bottom line>
```

## Dimension status → overall status mapping

- SKILL.md missing → overall is DRAFT
- Any placeholder markers (TODO/FIXME/TBD) found → overall is DRAFT
- Any other dimension is FAIL → overall is NEEDS WORK
- Only WARNs, no FAILs → overall is NEEDS WORK (use judgment; minor WARNs may still allow READY)
- All dimensions are PASS or SKIP → overall is READY

## Notes on good auditing

- Be specific. "Description lacks trigger phrases" is weak. "Description says 'helps users with tasks' — add trigger phrases such as 'audit my skill', 'check if my skill is ready', and 'validate this skill'" is actionable.
- Check the actual filesystem, not just the SKILL.md text. Reference integrity requires reading directory contents.
- Distinguish between a skill that is broken and one that is merely incomplete. Missing files → NEEDS WORK. Placeholder markers → DRAFT.
- Always include strengths. Even a DRAFT-status skill has something worth acknowledging.
