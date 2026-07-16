# Development

Run backend checks from the repository root:

```bash
make install-backend
make test-backend
make lint-backend
```

Run frontend checks from the scenario frontend directory:

```bash
cd scenarios/smart-ev-cockpit/frontend
npm install
npm test -- --run
npm run lint
npm run build
```

Start the backend:

```bash
make backend
```

Start the frontend:

```bash
make frontend
```

The default API URL is `http://127.0.0.1:8000`, and the default Vite URL is `http://127.0.0.1:5173`.
