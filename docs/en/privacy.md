# Privacy

The scenario uses three privacy layers.

Input scrubbing removes or tags sensitive user text before evidence is assembled. The backend exposes redaction count and redacted input so reviewers can inspect what was removed.

Memory projection controls what the browser receives. Sensitive content is replaced with masked content, deleted records are represented as tombstones, and hidden fields are listed explicitly.

Trace evidence is designed for replay without exposing raw private facts. It includes request context, PowerMem query details, selected memory IDs, reason codes, vehicle diffs, and write results.

The scenario data is synthetic. It is still treated as if it were user data so the architecture is useful for real product review.
