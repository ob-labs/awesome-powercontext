# Remote OceanBase Default Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the copied repository environment template select a remote OceanBase vector store by default and make all user-facing setup instructions match that behavior.

**Architecture:** Keep PowerMem initialization unchanged and express storage selection entirely through the environment variable names consumed by PowerMem 1.1.7. Update the English and Chinese entry-point documentation plus the Chinese operation guide, while preserving SQLite as an explicit opt-in configuration.

**Tech Stack:** dotenv configuration, PowerMem 1.1.7 `auto_config()`, Markdown documentation, shell-based verification

---

## File Map

- Modify `.env.example`: define the default remote OceanBase connection and remove unsupported storage aliases.
- Modify `README.md`: describe remote OceanBase as the default and SQLite as opt-in.
- Modify `README_CN.md`: keep the Chinese quick start and configuration reference consistent with the template.
- Modify `docs/zh/scenarios/smart-ev-cockpit-operation-guide.md`: align the presenter architecture and connectivity checks with remote OceanBase.

The operation guide already contains an unrelated staged user edit to the Act 10 description. Preserve that line exactly. Do not commit the implementation files in this session because committing that file would also capture the user's pre-existing staged change.

### Task 1: Replace the storage configuration template

**Files:**
- Modify: `.env.example:1-11`

- [ ] **Step 1: Run a baseline assertion that demonstrates the old template**

```bash
python3 - <<'PY'
from pathlib import Path

text = Path(".env.example").read_text()
assert "DATABASE_PROVIDER=oceanbase" in text
assert "OCEANBASE_HOST=REPLACE_ME" in text
assert "POWERMEM_STORAGE_PROVIDER" not in text
assert "POWERMEM_SQLITE_PATH" not in text
PY
```

Expected: FAIL on the missing `DATABASE_PROVIDER=oceanbase` assertion.

- [ ] **Step 2: Replace the top storage block with supported PowerMem variables**

The start of `.env.example` must be exactly:

```dotenv
POWERMEM_BACKEND=local_sdk

# PowerMem uses a remote OceanBase instance as the default vector store.
DATABASE_PROVIDER=oceanbase
OCEANBASE_HOST=REPLACE_ME
OCEANBASE_PORT=2881
OCEANBASE_USER=root@test
OCEANBASE_PASSWORD=REPLACE_ME
OCEANBASE_DATABASE=smart_ev_cockpit
OCEANBASE_COLLECTION=memories
OCEANBASE_EMBEDDING_MODEL_DIMS=1024

# Any OpenAI-compatible endpoint works, e.g. DashScope compatible mode or https://api.openai.com/v1
```

Leave the existing LLM, embedding, scenario, and privacy settings unchanged.

- [ ] **Step 3: Verify that PowerMem parses the template as remote OceanBase**

```bash
set -a
. ./.env.example
set +a
python3 - <<'PY'
from powermem import auto_config

vector_store = auto_config()["vector_store"]
config = vector_store["config"]
assert vector_store["provider"] == "oceanbase"
assert config["host"] == "REPLACE_ME"
assert config["collection_name"] == "memories"
assert config["embedding_model_dims"] == 1024
print("remote OceanBase template parsed successfully")
PY
```

Expected: PASS and print `remote OceanBase template parsed successfully` without opening a database connection.

### Task 2: Align the English and Chinese README files

**Files:**
- Modify: `README.md:29-105`
- Modify: `README_CN.md:29-105`

- [ ] **Step 1: Confirm the stale defaults are currently documented**

```bash
rg -n "SQLite \(default\)|SQLite（默认|POWERMEM_STORAGE_PROVIDER|POWERMEM_SQLITE_PATH" README.md README_CN.md
```

Expected: matches in both architecture diagrams, quick-start text, and configuration tables.

- [ ] **Step 2: Update the English README**

Apply these exact content changes:

```text
Architecture storage labels:
storage: OceanBase (default)
         or SQLite (opt-in)

Additional prerequisite:
- A reachable remote OceanBase instance

Configure command comment:
# edit .env: set the OceanBase connection, model API keys, and provider base URLs

Quick-start explanation:
The copied template uses a remote OceanBase instance as PowerMem's vector store. Set the `OCEANBASE_*` connection values before starting the backend. To use a local SQLite file instead, see [Configuration](#configuration).
```

Replace the storage rows in the configuration table with:

```markdown
| `DATABASE_PROVIDER` | PowerMem vector store provider | `oceanbase` |
| `OCEANBASE_HOST` / `OCEANBASE_PORT` | Remote OceanBase address | `REPLACE_ME` / `2881` |
| `OCEANBASE_USER` / `OCEANBASE_PASSWORD` | Remote OceanBase credentials | `root@test` / `REPLACE_ME` |
| `OCEANBASE_DATABASE` / `OCEANBASE_COLLECTION` | Database and memory collection | `smart_ev_cockpit` / `memories` |
| `OCEANBASE_EMBEDDING_MODEL_DIMS` | OceanBase vector dimensions; must match `EMBEDDING_DIMS` | `1024` |
```

Replace the existing OceanBase details block with:

````markdown
<details>
<summary>Using SQLite instead</summary>

```bash
DATABASE_PROVIDER=sqlite
SQLITE_PATH=./data/powermem_smart_ev.db
SQLITE_COLLECTION=memories
```

</details>
````

- [ ] **Step 3: Apply the equivalent Chinese documentation**

Use these Chinese strings and the same variable names/defaults:

```text
架构存储标签：
存储：OceanBase（默认）
      或 SQLite（显式启用）

新增环境要求：
- 一个可访问的远程 OceanBase 实例

配置命令注释：
# 编辑 .env：填写 OceanBase 连接信息、模型 API Key 和服务 base URL

快速开始说明：
复制后的配置模板默认使用远程 OceanBase 作为 PowerMem 向量存储。启动后端前请填写 `OCEANBASE_*` 连接参数。如需改用本地 SQLite 文件，见[配置说明](#配置说明)。

折叠区标题：
改用 SQLite
```

The Chinese configuration table must use the same five storage rows as the English table, with Chinese descriptions. The SQLite block must remain byte-for-byte identical to the English variable block.

```markdown
| `DATABASE_PROVIDER` | PowerMem 向量存储后端 | `oceanbase` |
| `OCEANBASE_HOST` / `OCEANBASE_PORT` | 远程 OceanBase 地址 | `REPLACE_ME` / `2881` |
| `OCEANBASE_USER` / `OCEANBASE_PASSWORD` | 远程 OceanBase 凭证 | `root@test` / `REPLACE_ME` |
| `OCEANBASE_DATABASE` / `OCEANBASE_COLLECTION` | 数据库和记忆集合 | `smart_ev_cockpit` / `memories` |
| `OCEANBASE_EMBEDDING_MODEL_DIMS` | OceanBase 向量维度，必须与 `EMBEDDING_DIMS` 一致 | `1024` |
```

````markdown
<details>
<summary>改用 SQLite</summary>

```bash
DATABASE_PROVIDER=sqlite
SQLITE_PATH=./data/powermem_smart_ev.db
SQLITE_COLLECTION=memories
```

</details>
````

### Task 3: Align the Chinese presenter operation guide

**Files:**
- Modify: `docs/zh/scenarios/smart-ev-cockpit-operation-guide.md:9-38`

- [ ] **Step 1: Update the storage architecture row**

Replace the current storage row with:

```markdown
| 记忆存储 | 远程 OceanBase（默认） | 由 `.env` 中的 `DATABASE_PROVIDER` 和 `OCEANBASE_*` 参数配置；SQLite 需显式启用 |
```

- [ ] **Step 2: Load `.env` before connectivity checks and make OceanBase checking the default**

Replace the environment-check introduction and shell block with:

````markdown
在演示机上依次执行。先从项目根目录加载 `.env`，再检查其中配置的 OceanBase、LLM 和 Embedding 服务：

```bash
# 加载 .env，供后续检查命令读取连接参数
set -a
source .env
set +a

# ① 后端健康检查，期望返回 {"status":"ok",...}
curl -s http://127.0.0.1:8000/api/health

# ② 前端是否在监听 5173
ss -tlnp | grep 5173

# ③ LLM 服务连通性，期望 HTTP 200
curl -s -o /dev/null -w "%{http_code}\n" "$OPENAI_LLM_BASE_URL/models" \
  -H "Authorization: Bearer $LLM_API_KEY"

# ④ 默认远程 OceanBase 数据库端口可达性
timeout 5 bash -c "</dev/tcp/${OCEANBASE_HOST}/${OCEANBASE_PORT}" && echo 可达
```
````

Do not change the existing Act 10 description or any later operation-guide content.

### Task 4: Verify the complete documentation-only change

**Files:**
- Verify: `.env.example`
- Verify: `README.md`
- Verify: `README_CN.md`
- Verify: `docs/zh/scenarios/smart-ev-cockpit-operation-guide.md`

- [ ] **Step 1: Confirm stale names and default claims are gone from active docs**

```bash
if rg -n "SQLite \(default\)|SQLite（默认|POWERMEM_STORAGE_PROVIDER|POWERMEM_SQLITE_PATH" \
  .env.example README.md README_CN.md \
  docs/zh/scenarios/smart-ev-cockpit-operation-guide.md; then
  exit 1
fi
```

Expected: no output and exit code 0.

- [ ] **Step 2: Confirm the new defaults are present everywhere intended**

```bash
rg -n "DATABASE_PROVIDER|OCEANBASE_HOST|OceanBase \(default\)|OceanBase（默认" \
  .env.example README.md README_CN.md \
  docs/zh/scenarios/smart-ev-cockpit-operation-guide.md
```

Expected: `.env.example` contains the remote OceanBase values; both README files and the operation guide identify OceanBase as the default.

- [ ] **Step 3: Check formatting and review only the target-file diff**

```bash
git diff --check -- .env.example README.md README_CN.md \
  docs/zh/scenarios/smart-ev-cockpit-operation-guide.md
git diff -- .env.example README.md README_CN.md \
  docs/zh/scenarios/smart-ev-cockpit-operation-guide.md
```

Expected: `git diff --check` produces no output. The diff contains only storage configuration/documentation edits plus the pre-existing staged Act 10 change when the staged diff is viewed separately.

- [ ] **Step 4: Leave implementation changes uncommitted for user review**

Do not stage, unstage, or commit the four implementation files. Report that `docs/zh/scenarios/smart-ev-cockpit-operation-guide.md` retained its pre-existing staged Act 10 edit and that the new OceanBase documentation hunk remains unstaged.
