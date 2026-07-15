# Architecture

The Smart EV Cockpit Memory scenario is split into a FastAPI backend, a Vite React frontend, and synthetic scenario data.

Backend responsibilities:

- Load synthetic vehicle, dialogue, navigation, media, relationship, and state events.
- Wrap the live PowerMem SDK boundary.
- Build search queries from actor and seat context.
- Project returned memories before sending them to the browser.
- Apply vehicle state patches and expose before/after diffs.
- Append replayable trace evidence for each scenario action.

Frontend responsibilities:

- Submit utterances to the backend.
- Render only backend-returned memory hits, vehicle diffs, and trace evidence.
- Show a live-mode error when PowerMem is not connected.
- Provide presenter controls and developer evidence panels for a workshop flow.

The backend is the only layer that talks to PowerMem. The frontend receives already-projected data and never fabricates fallback memories.
