# Architecture

The Smart EV Cockpit Memory scenario is split into a FastAPI backend, a Vite React frontend, and synthetic scenario data.

Backend responsibilities:

- Load synthetic vehicle, dialogue, navigation, media, relationship, and state events.
- Own a live PowerContext Builtin Runtime for the FastAPI process lifetime.
- Capture each imported item as a Source and flush it through the cockpit candidate pipeline into a cited Memory revision.
- Search the current Memory head with PowerContext FTS, then apply actor, seat, vehicle, and lifecycle filters.
- Map lifecycle updates to immutable revisions and deletions to retained-history retirement.
- Project returned memories before sending them to the browser.
- Apply vehicle state patches and expose before/after diffs.
- Append replayable trace evidence for each scenario action.

Frontend responsibilities:

- Submit utterances to the backend.
- Render only backend-returned memory hits, vehicle diffs, and trace evidence.
- Show a live-mode error when PowerContext is not connected.
- Provide presenter controls and developer evidence panels for a workshop flow.

The adapter keeps the existing synchronous scenario services on top of PowerContext's asynchronous Runtime by owning a dedicated event-loop thread. The backend is the only layer that talks to PowerContext. The frontend receives already-projected data and never fabricates fallback memories.
