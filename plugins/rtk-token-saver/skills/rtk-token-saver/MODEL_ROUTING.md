# Model Routing

RTK reduces noisy shell output. It does not decide which Claude model to use, so keep model discipline explicit.

| Task | Preferred model |
| --- | --- |
| Summary, extraction, classification, small rewrite | `haiku` |
| Routine coding, debugging, test fixes, implementation | `sonnet` |
| Architecture/planning where Opus reasoning is useful | `opusplan` |
| High-risk ambiguous reasoning after Sonnet is insufficient | `opus` |
| Long-context emergency only | `sonnet[1m]` or `opus[1m]` |

If Opus is active for small work, recommend switching to `sonnet` or `haiku`.

For team defaults, prefer Claude Code managed settings or user settings that make `sonnet` the default and keep 1M context disabled unless explicitly approved.
