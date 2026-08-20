.PHONY: install-backend test-backend backend frontend test-frontend lint-backend

PYTHON ?= python3
POWERCONTEXT_SOURCE ?= $(abspath ../powercontext)

install-backend:
	@if [ -d "$(POWERCONTEXT_SOURCE)" ]; then \
		$(PYTHON) -m pip install -e "$(POWERCONTEXT_SOURCE)[builtin]"; \
	fi
	cd scenarios/smart-ev-cockpit/backend && $(PYTHON) -m pip install -e ".[dev]"

test-backend:
	cd scenarios/smart-ev-cockpit/backend && $(PYTHON) -m pytest -q

lint-backend:
	cd scenarios/smart-ev-cockpit/backend && $(PYTHON) -m ruff check app tests

backend:
	cd scenarios/smart-ev-cockpit/backend && $(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

frontend:
	cd scenarios/smart-ev-cockpit/frontend && npm run dev -- --host 127.0.0.1 --port 5173

test-frontend:
	cd scenarios/smart-ev-cockpit/frontend && npm test -- --run
