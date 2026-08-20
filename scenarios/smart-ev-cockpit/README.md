# Smart EV Cockpit Memory

This scenario demonstrates a live PowerContext-backed smart EV cockpit assistant with privacy-safe synthetic data, memory lifecycle management, and inspectable evidence traces across **ten deterministic acts**.

## Demo flow

| Act | Endpoint | Notes |
|-----|----------|-------|
| Acts 1–8 | `POST /api/scenarios/smart-ev-cockpit/utter` | Send `act_key`, `actor_id`, `seat_position`, `text` |
| Act 9 | `POST /api/scenarios/smart-ev-cockpit/events/vehicle` | Low-SOC proactive care; **not** available via `/utter` |
| Act 10 | `POST /api/scenarios/smart-ev-cockpit/lifecycle/run` | Day-90 lifecycle UPDATE/DELETE audit |

Presenter scripts: `docs/demo-playbook.en.md`, `docs/demo-playbook.zh.md`, and the full workshop playbooks under `docs/en/scenarios/` and `docs/zh/scenarios/`.

## Verification

```bash
# Backend (run from this scenario's backend directory)
cd scenarios/smart-ev-cockpit/backend
python -m pytest tests -q
python -m ruff check app tests

# Frontend
cd ../frontend
npm test -- --run
npm run build
```

The connected acceptance test `tests/test_ten_act_demo.py` drives Acts 1–10 through the same API sequence documented for presenters.
