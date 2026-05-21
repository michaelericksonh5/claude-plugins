---
name: rules-install
description: Install or update Claude global and project markdown rules for H5G probability-based slot math. Use when the user asks to add global rules, project rules, CLAUDE.md, .claude/rules, probability rules, RTP rules, Monte Carlo rules, or dependent-probability guidance.
when_to_use: Invoke only when the user asks to write, install, update, sync, or repair rule files. Do not auto-run for ordinary math/RTP discussion; use slot-math-core, probability-model, dependency-audit, rtp-verification, and internal-h5g-evidence instead.
disable-model-invocation: true
---

# Rules Install

Use this skill to install/update rules from this plugin into Claude rule files.

## Targets

Global/user rule:

- `~/.claude/CLAUDE.md` or `~/.claude/rules/h5g-slot-math.md`

Project rule:

- `.claude/rules/h5g-slot-math/probability-model.md`

## Workflow

1. Ask whether the user wants global rules, project rules, or both if not already clear.
2. Read existing target files if present.
3. Preserve unrelated existing content.
4. Insert or update a clearly delimited H5G slot math section.
5. Use [global-rule-template.md](global-rule-template.md) and [project-rule-template.md](project-rule-template.md).
6. For project rules, keep path frontmatter.
7. Verify the file exists and contains the probability-first, dependency-proof, and simulation-verification requirements.

## Delimiter

Use this delimiter for idempotent updates:

```markdown
<!-- BEGIN H5G SLOT MATH RULES -->
...
<!-- END H5G SLOT MATH RULES -->
```

Do not overwrite unrelated user or project rules.

