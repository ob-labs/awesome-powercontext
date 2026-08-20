# awesome-powercontext

**English** | [简体中文](README_CN.md)

Scenario-driven examples for [PowerContext](https://github.com/oceanbase/powercontext) — a context runtime with persistent, revisioned Memory for agent applications.

Instead of API snippets, this repository shows PowerContext working inside realistic product workflows. Every demo captures real Sources, creates cited Memory revisions, performs live search/revision/retirement operations, and exposes inspectable trace evidence over privacy-safe synthetic data. The frontend never fabricates memory hits.

## Scenarios

| Scenario | Description | Status |
|---|---|---|
| [Smart EV Cockpit Memory](scenarios/smart-ev-cockpit/) | A privacy-safe in-car assistant that personalizes cabin controls, media, navigation, and proactive care using long-term memory, demonstrated across ten deterministic acts | ✅ Available |

## Scenario 1: Smart EV Cockpit Memory

A cockpit assistant remembers a driver's preferences over 90 simulated days and demonstrates:

- **Memory grounding** — retrieval is filtered by actor, seat position, vehicle state, and lifecycle metadata. The same utterance ("I feel a bit cold") produces different, safety-aware actions for the driver, a front passenger, and a child in the rear seat.
- **Privacy by projection** — precise addresses, anniversary dates, and child identities are redacted or generalized before they reach the browser. The presenter view never shows raw sensitive facts.
- **Memory lifecycle** — short-lived context decays and is cleaned up at day 90 while long-term preferences stay active, with every `UPDATE`/`DELETE` captured in an audit trail.
- **Full traceability** — every assistant action can be replayed and exported as a trace JSON, including search filters, selected memory IDs, and vehicle-state diffs.

The demo runs through **ten acts** (memory creation → per-occupant disambiguation → control routines → capability boundaries → location recall → media preferences → anniversary suggestions → driving-mode advice → proactive low-battery care → day-90 lifecycle review). See the [presenter playbook](docs/en/scenarios/smart-ev-cockpit-playbook.md) for the full script.

### Architecture

```
Browser (Vite + React)  ──/api proxy──►  FastAPI backend  ──Builtin Runtime──► PowerContext
     renders only                        capture Source,                    SQLite (default)
  backend-returned                       recall/revise/retire                 or OceanBase
  memories & traces                      project/redact
```

The backend is the only layer that talks to PowerContext. The frontend receives already-projected data. See [architecture](docs/en/architecture.md) for details.

## Quick Start

### Prerequisites

- Python **3.11+**
- Node.js **18+**
- [`uv`](https://docs.astral.sh/uv/) or `pip`
- Optional: an OpenAI-compatible LLM endpoint for generated assistant replies

### 1. Configure

```bash
cp .env.example .env
# the default SQLite + FTS configuration works without model credentials
```

The copied template stores PowerContext data in a local SQLite database. Set `POWERCONTEXT_DATABASE_URL` to an official `mysql+aoceanbase` URL when you want to use [OceanBase](https://github.com/oceanbase/oceanbase).

### 2. Run the backend

```bash
make install-backend # uses ../powercontext when that source checkout exists
make backend        # FastAPI on http://127.0.0.1:8000, docs at /docs
```

### 3. Run the frontend

```bash
cd scenarios/smart-ev-cockpit/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://localhost:5173`. When developing on a remote machine, forward ports `5173` and `8000` (the dev server proxies `/api` to the backend).

### 4. Seed demo data

Acts 5–9 retrieve historical memories, so seed the memory store first: in the top data bar of the UI, click **Generate** (1,200 reproducible synthetic memory events, seed 42) and then **Import**. Each imported item is captured as a PowerContext Source and materialized as a cited Memory entry.

Then use **Next → Send** to step through the ten acts, and open the **Evidence** panel to inspect memory hits, vehicle-state diffs, privacy masking, and the audit log.

## Configuration

All configuration lives in `.env` (see [.env.example](.env.example)):

| Variable | Description | Default |
|---|---|---|
| `POWERCONTEXT_BACKEND` | PowerContext integration mode | `builtin` |
| `POWERCONTEXT_SCOPE_ID` | Isolated Source and Memory scope | `smart-ev-cockpit` |
| `POWERCONTEXT_DATABASE_URL` | SQLite or OceanBase async SQLAlchemy URL | `sqlite+aiosqlite:///data/powercontext_smart_ev.db` |
| `POWERCONTEXT_OPERATION_TIMEOUT_SECONDS` | Runtime call timeout | `30` |
| `LLM_PROVIDER` / `LLM_MODEL` | Optional chat reply model | `openai` / — |
| `LLM_API_KEY`, `OPENAI_LLM_BASE_URL` | Credentials and endpoint of your OpenAI-compatible provider | — |
| `DEMO_PRIVACY_MODE` | Privacy projection strictness | `strict` |

## Testing

```bash
make test-backend     # pytest, includes the ten-act acceptance test
make lint-backend     # ruff
make test-frontend    # vitest
```

## Repository Layout

```
awesome-powercontext/
├── docs/                       # Project docs (en + zh): overview, architecture, privacy, playbooks
├── scenarios/
│   └── smart-ev-cockpit/
│       ├── backend/            # FastAPI app wrapping the PowerContext Builtin Runtime
│       ├── frontend/           # Vite + React cockpit UI
│       ├── data/synthetic/     # Synthetic scenario events (no real PII)
│       └── docs/               # Scenario presenter playbooks
├── Makefile
└── .env.example
```

## Documentation

- [Overview](docs/en/overview.md) · [Architecture](docs/en/architecture.md) · [Privacy](docs/en/privacy.md) · [Live evidence](docs/en/live-evidence.md) · [Development](docs/en/development.md)
- [Smart EV Cockpit scenario guide](docs/en/scenarios/smart-ev-cockpit.md) · [Presenter playbook](docs/en/scenarios/smart-ev-cockpit-playbook.md)
- 中文文档: [docs/zh/](docs/zh/)

## Privacy

All scenario data is synthetic. No real automotive brands, user identities, vehicle identifiers, addresses, phone numbers, or credentials appear in this repository. See [privacy](docs/en/privacy.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing

Contributions of new PowerContext scenarios are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Code, comments, paths, API fields, and commit messages use English; public data must stay synthetic.

## License

Apache License 2.0 — the same license as [PowerContext](https://github.com/oceanbase/powercontext).
