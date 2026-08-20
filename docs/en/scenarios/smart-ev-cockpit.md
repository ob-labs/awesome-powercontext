# Smart EV Cockpit Memory

Smart EV Cockpit Memory is a workshop scenario for a vehicle assistant backed by live PowerContext operations.

The scenario covers:

- Person and seat-aware memory retrieval
- Cabin preference and driving routine recall
- Capability boundaries for unsupported vehicle features
- Masked location and relationship memories
- Child-safe media and safety policy memories
- Vehicle state diffs and proactive care events
- Memory lifecycle states across a 90-day demonstration

The frontend starts with no memory hits. After a presenter submits an utterance, the backend searches PowerContext, applies privacy projection, updates vehicle state when appropriate, and returns a trace with evidence for the developer drawer.

See `smart-ev-cockpit-playbook.md` for the workshop act sequence.
