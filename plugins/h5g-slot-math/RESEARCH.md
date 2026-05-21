# Research Basis

This plugin was built from:

- Official Claude Code plugin docs: plugin manifest at `.claude-plugin/plugin.json`; skills in `skills/<name>/SKILL.md`; hooks in `hooks/hooks.json`; plugin paths must be relative to plugin root and start with `./` when declared in the manifest.
- Official Claude Code skills docs: keep `SKILL.md` concise, use frontmatter descriptions for discovery, use supporting files for progressive disclosure, keep references one level deep, use `disable-model-invocation: true` for manually triggered side-effect workflows.
- Official Claude Code skills docs confirm `when_to_use` is appended to `description` for skill discovery, and the combined text is truncated at 1,536 characters. The plugin therefore uses concise trigger-rich `description` plus `when_to_use` fields instead of bloating skill bodies.
- Official Claude Code hooks docs: plugin hooks live in `hooks/hooks.json`; `UserPromptSubmit` can add `additionalContext`; hook output is capped; hooks should be fast because they run before prompts.
- Official Claude Desktop docs: the Desktop app has Chat, Cowork, and Code tabs; plugin skills can be invoked from the prompt UI; plugins are available in local and SSH Code sessions but not remote Code sessions.
- Official Cowork plugin docs: plugins are available in Cowork and Code, not Chat; plugins can bundle skills, connectors, agents, and hooks; users install from marketplace, organization-managed plugin lists, or uploaded plugin packages.
- Official marketplace docs: team distribution should use a `.claude-plugin/marketplace.json` catalog with plugin entries pointing to plugin sources. Relative plugin paths work when the marketplace is added from a directory or Git repository.
- Installed plugin examples:
  - `slot-art-creator-node` uses `.claude-plugin/plugin.json`, `skills`, `agents`, `hooks`, and MCP server declarations.
  - `skill-auditor` uses a simple manifest with explicit skill paths.
  - `hookify` uses plugin hook configuration with command hooks.
- H5G math research in `C:\Users\merickson\Claude Slot Math`, including global/project rules, dependent probability playbook, and Confluence research.

Design decisions:

- Six focused skills are used instead of one large skill to preserve context.
- Detailed examples and checklists are supporting files, loaded only when needed.
- A `UserPromptSubmit` hook injects a compact reminder only when prompt terms indicate slot math.
- Natural-language invocation is implemented through skill metadata first and hook reinforcement second. The hook catches explicit terms like RTP/RMG/PAR/Test Harness and broader combinations like math/probability/simulation plus game/slot/reel/pay/bonus context.
- The plugin includes `DESKTOP.md` and a parent local marketplace catalog so the same package can be tested through CLI and prepared for Claude Desktop/Cowork distribution.
- No production H5G math is inferred. Feature names trigger requests for GDD, math spec, PAR sheet, engine config, or internal process artifacts.

