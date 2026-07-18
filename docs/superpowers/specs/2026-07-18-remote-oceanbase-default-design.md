# Remote OceanBase Default Configuration Design

## Objective

Make the repository's copied environment template use a remote OceanBase instance as PowerMem's vector store by default. The change is limited to configuration examples and documentation; application initialization code and runtime behavior remain unchanged.

## Scope

The implementation will update:

- `.env.example`
- `README.md`
- `README_CN.md`
- `docs/zh/scenarios/smart-ev-cockpit-operation-guide.md`

It will not modify Python application code, dependency declarations, generated lock files, frontend code, or existing PowerMem failure handling.

## Configuration Design

The template will use PowerMem 1.1.7's supported environment variables:

- `DATABASE_PROVIDER=oceanbase`
- `OCEANBASE_HOST=REPLACE_ME`
- `OCEANBASE_PORT=2881`
- `OCEANBASE_USER=root@test`
- `OCEANBASE_PASSWORD=REPLACE_ME`
- `OCEANBASE_DATABASE=smart_ev_cockpit`
- `OCEANBASE_COLLECTION=memories`
- `OCEANBASE_EMBEDDING_MODEL_DIMS=1024`

The unsupported project-specific variables `POWERMEM_STORAGE_PROVIDER` and `POWERMEM_SQLITE_PATH` will be removed from the template and documentation. `POWERMEM_BACKEND=local_sdk` remains because it documents the scenario's PowerMem integration mode, even though vector storage selection is controlled by `DATABASE_PROVIDER`.

`REPLACE_ME` keeps the template free of real infrastructure details and makes missing required connection settings visible. A non-empty host selects PowerMem's remote OceanBase connection path rather than embedded SeekDB.

## Optional SQLite Configuration

SQLite remains documented as an explicit opt-in alternative:

```dotenv
DATABASE_PROVIDER=sqlite
SQLITE_PATH=./data/powermem_smart_ev.db
SQLITE_COLLECTION=memories
```

No automatic fallback to SQLite will be introduced. If the configured OceanBase instance is unavailable, the existing application behavior continues: PowerMem initialization fails, live mode is disabled, and the UI reports the live-mode error.

## Documentation Changes

The English and Chinese quick-start sections will state that copying `.env.example` selects remote OceanBase and requires valid OceanBase connection details. Their architecture diagrams and configuration tables will identify OceanBase as the default vector store and use the environment variable names recognized by PowerMem.

The existing expandable OceanBase configuration example will become an SQLite opt-in example. The Chinese operation guide will likewise describe OceanBase as the default and align its preflight instructions with the template.

The word "default" applies only after `.env.example` has been copied to `.env`. Running the application without a `.env` file remains governed by the installed PowerMem SDK's own defaults.

## Verification

Verification will include:

1. Load a controlled environment derived from the new template through PowerMem 1.1.7's `auto_config()` and confirm that the vector store provider is `oceanbase`, the host is non-empty, and the collection and embedding dimensions are preserved.
2. Search the affected repository documentation for stale claims that SQLite is the default or for the removed `POWERMEM_STORAGE_PROVIDER` and `POWERMEM_SQLITE_PATH` names.
3. Review the final diff to confirm that no application code or unrelated user changes were modified.

