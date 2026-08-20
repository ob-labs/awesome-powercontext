# Overview

awesome-powercontext is a scenario-driven reference project for PowerContext. It demonstrates how an application can retrieve, write, project, and audit memory in a realistic product workflow.

The first scenario is Smart EV Cockpit Memory. It models a privacy-safe cockpit assistant that uses live PowerContext operations to personalize cabin controls, recommendations, media choices, and lifecycle behavior.

The demo has three goals:

- Show that memory retrieval can be grounded in actor, seat, vehicle, and lifecycle metadata.
- Keep sensitive facts out of the presenter view through redaction and frontend projection.
- Expose trace evidence so every assistant action can be replayed and inspected.

The frontend does not generate fake memory hits. If PowerContext is unavailable, the backend returns a live-mode error and the UI shows that error.
