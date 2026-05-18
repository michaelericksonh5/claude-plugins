# CEO Summary

Claude spend rises when routine work accidentally runs on expensive models, users leave large contexts open for unrelated tasks, or automation repeatedly rediscovers the same project state.

`token-saver` addresses this with a Sonnet-first default, Haiku guidance for simple tasks, Opus/OpusPlan guidance for planning only, status-line visibility, conservative output-filtering hooks, reusable skills, and Claude Code settings examples for self-serve or managed rollout.

Expected impact:

- Fewer accidental Opus sessions for routine coding.
- Fewer repeated large-context turns.
- Better resume-friendly and cache-friendly workflows.
- More consistent team language around when to use Haiku, Sonnet, OpusPlan, and Opus.

Limits:

- Claude Cowork model enforcement is not exposed like Claude Code settings.
- Cowork rollout should use plugin guidance plus Team/Enterprise analytics and extra usage limits.
- Strict Claude Code settings should be piloted before broad enforcement so useful expert workflows are not blocked.
