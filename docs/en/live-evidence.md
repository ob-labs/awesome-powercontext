# Live Evidence

The Smart EV Cockpit Memory scenario runs in live PowerContext mode. If PowerContext is not connected, the scenario action fails and the frontend shows a live-mode error.

Each interaction exposes:

- Request ID, endpoint, timestamp, and latency
- Privacy redaction count and redacted input
- PowerContext search query, filters, limit, and duration
- Memory IDs, scores, metadata, and masked content
- Selected memory IDs and reason codes
- Vehicle command payload and before/after state diff
- PowerContext Memory reference, entry version, source citation, and matched search channel
- UI operation result when Source capture creates an entry, a revision updates it, or retirement makes it inactive

Presenter Mode and Developer Evidence Mode use the same backend response. The frontend does not generate fake memory hits.
