# Live Evidence

The Smart EV Cockpit Memory scenario runs in live PowerMem mode. If PowerMem is not connected, the scenario action fails and the frontend shows a live-mode error.

Each interaction exposes:

- Request ID, endpoint, timestamp, and latency
- Privacy redaction count and redacted input
- PowerMem search query, filters, limit, and duration
- Memory IDs, scores, metadata, and masked content
- Selected memory IDs and reason codes
- Vehicle command payload and before/after state diff
- PowerMem write result when ADD, UPDATE, ARCHIVE, or DELETE runs

Presenter Mode and Developer Evidence Mode use the same backend response. The frontend does not generate fake memory hits.
