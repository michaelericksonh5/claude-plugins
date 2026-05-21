# skill-auditor

A Claude skill that audits other skills against an 8-dimension quality rubric,
returning a structured **READY / NEEDS WORK / DRAFT** report.

## What it checks

| # | Dimension | What it looks for |
|---|-----------|-------------------|
| 1 | Frontmatter | Valid YAML; `name` and `description` present |
| 2 | Description quality | Specific trigger phrases; concrete scope; not generic |
| 3 | Instruction clarity | Imperative steps; no unexplained ALL-CAPS directives |
| 4 | Reference integrity | Every file referenced in SKILL.md exists on disk |
| 5 | Completeness | No `TODO`, `FIXME`, `TBD`, or `[INSERT` placeholders |
| 6 | Output specification | Format, structure, and delivery method are defined |
| 7 | Evals coverage | `evals/` directory present (SKIP if absent — not a blocker) |
| 8 | Security / content | No malicious code or surprising content |

## Install

### Claude Code (CLI / IDE)

```
/plugin marketplace add michaelericksonh5/claude-plugins
/plugin install skill-auditor@h5g-plugins
```

Or from a shell:

```
claude plugin marketplace add michaelericksonh5/claude-plugins
claude plugin install skill-auditor@h5g-plugins
```

## Usage

Just ask Claude to audit a skill by path:

```
audit my skill at path/to/my-skill
is this skill ready to ship? path/to/skill-dir
review my SKILL.md — path/to/skill
check if my skill looks good: ./my-skill
```

Claude will read the skill directory, run all 8 checks, and produce a report like:

```
## Overall Status: NEEDS WORK

| # | Dimension         | Status | Notes                                    |
|---|-------------------|--------|------------------------------------------|
| 1 | Frontmatter       | PASS   | name and description present             |
| 2 | Description quality | WARN | Trigger phrases present but thin         |
| 4 | Reference integrity | FAIL | scripts/helper.py referenced but missing |
...

### Priority Fixes
1. [HIGH] Create scripts/helper.py — referenced in Step 2, skill cannot run without it
2. [MED]  Add 2–3 more trigger phrases to the description
```

## Part of the h5g-plugins marketplace

This plugin is listed in the
[michaelericksonh5/claude-plugins](https://github.com/michaelericksonh5/claude-plugins)
marketplace alongside the slot-art-creator-node and other High 5 Games tooling.
