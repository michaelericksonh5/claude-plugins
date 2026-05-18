# Model Routing

Use the cheapest model that is likely to preserve quality.

| Task type | Default model |
| --- | --- |
| Simple summary/classification | `haiku` |
| Routine coding/debugging | `sonnet` |
| Multi-file implementation | `sonnet` |
| Architectural planning | `opusplan` |
| Deep ambiguous reasoning | `opus` |
| Long-context emergency only | `sonnet[1m]` or `opus[1m]` when explicitly approved |

`opusplan` uses Opus in plan mode and Sonnet in execution mode. It is the preferred route when planning needs heavier reasoning but implementation should stay on Sonnet.

Do not make 1M context the default. Use `sonnet[1m]` or `opus[1m]` only when the user explicitly approves a truly huge context task.

Default effort should be `auto`, `low`, or `medium`. Raise effort only for complex tasks where the extra reasoning cost is justified.
