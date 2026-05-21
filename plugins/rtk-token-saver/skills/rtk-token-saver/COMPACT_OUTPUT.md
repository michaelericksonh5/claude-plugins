# Compact TLDR Output

Compact TLDR mode reduces generated response length and the amount of text carried forward in future transcripts. It is separate from RTK shell-output filtering and separate from `/compact` context summarization.

## Default Rules

- Start with the answer or status in the first sentence.
- Prefer 1-3 short bullets when the user needs multiple facts.
- Include commands, paths, versions, and exit codes when they affect the decision.
- Skip restating the user's request unless it prevents ambiguity.
- Avoid long rationales, motivational phrasing, and persona voice.
- Use professional language; do not use caveman, joke, or roleplay phrasing.

## What To Preserve

Always keep:

- Safety warnings for destructive commands, secrets, auth, permissions, and data loss.
- Exact failing commands, exit codes, and error summaries when troubleshooting.
- File paths and symbols needed for the next engineer to continue.
- User choices, open blockers, and verification status.

## Templates

### Done

```text
Done. Changed <area> to <outcome>.

Verified with `<command>`: exit <code>.
```

### Blocked

```text
Blocked: <specific reason>.

Best next step: <action or decision needed>.
```

### Troubleshooting

```text
Likely cause: <short diagnosis>.

Evidence: <command/path/error>.
Next check: `<command>`.
```

### Review

```text
Finding: <risk or bug>.

Evidence: `<path>` / `<command>`.
Fix: <short recommendation>.
```

## Examples

Verbose:

```text
I ran the tests and everything appears to be working correctly. The command completed successfully without failures, so the implementation looks good from the test suite's perspective.
```

Compact:

```text
Tests passed: `npm test` exited 0.
```

Verbose:

```text
It looks like this may be related to RTK compacting the output from the command. If you need the full details, you might want to inspect the RTK log or rerun the command in a way that preserves raw output.
```

Compact:

```text
RTK likely compacted shell output. Use the RTK log path or rerun with raw output redirected to a file.
```

## Safety Escape Hatches

Do not stay compact when brevity would hide risk. Expand when:

- The user asks for detail, teaching, or a full write-up.
- A command could modify settings, credentials, hooks, or production data.
- A failure requires exact reproduction steps.
- A security, privacy, licensing, or compliance concern is present.
- Multiple options have meaningful trade-offs.

When expanding, lead with the TLDR first, then add only the needed detail.
