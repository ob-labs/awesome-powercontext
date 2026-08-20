# awesome-powercontext

[English](README.md) | **简体中文**

以真实场景展示 [PowerContext](https://github.com/oceanbase/powercontext)（带持久化、可修订 Memory 的上下文运行层）的示例项目集。

不同于 API 代码片段，本仓库把 PowerContext 放进真实产品工作流：采集真实 Source、形成带 citation 的 Memory revision，并执行实时检索、修订与停用。所有场景使用隐私安全的合成数据，前端不会伪造记忆命中结果。

## 场景列表

| 场景 | 说明 | 状态 |
|---|---|---|
| [智能电动车座舱记忆](scenarios/smart-ev-cockpit/) | 一个隐私安全的车载助手，利用长期记忆实现座舱控制、媒体、导航的个性化和主动关怀，通过十幕确定性剧本完整演示 | ✅ 可用 |

## 场景一：智能电动车座舱记忆

座舱助手在模拟的 90 天里持续记住驾驶员的偏好，重点演示：

- **记忆的上下文约束** —— 检索按说话人、座位、车辆状态和生命周期元数据过滤。同一句"有点冷"，主驾、前排乘客和后排儿童会得到各自不同且符合安全边界的车控动作。
- **投影式隐私保护** —— 精确地址、纪念日日期、儿童身份在到达浏览器之前就已脱敏或泛化，演示视图永远不暴露原始敏感事实。
- **记忆生命周期** —— 第 90 天时短期上下文自动衰减、清理，长期偏好保持有效，每一次 `UPDATE`/`DELETE` 都留有审计记录。
- **全程可追溯** —— 助手的每个动作都可以回放，并导出为 trace JSON，包含检索过滤条件、命中的 memory ID 和车辆状态 diff。

演示共**十幕**（建立记忆 → 同一句话不同人 → 组合车控例程 → 车辆能力边界 → 地点回忆 → 多媒体偏好 → 纪念日推荐 → 驾驶模式建议 → 低电量主动关怀 → 第 90 天生命周期审查）。完整演示话术见[演示手册](docs/zh/scenarios/smart-ev-cockpit-playbook.md)，操作步骤见[操作指引](docs/zh/scenarios/smart-ev-cockpit-operation-guide.md)。

### 架构

```
浏览器 (Vite + React)  ──/api 代理──►  FastAPI 后端  ──Builtin Runtime──► PowerContext
    只渲染后端                          采集 Source、                    SQLite（默认）
  返回的记忆与                          检索/修订/停用、                   或 OceanBase
   trace 证据                           投影/脱敏
```

后端是唯一与 PowerContext 交互的层，前端拿到的都是已投影脱敏的数据。详见[架构文档](docs/zh/architecture.md)。

## 快速开始

### 环境要求

- Python **3.11+**
- Node.js **18+**
- [`uv`](https://docs.astral.sh/uv/) 或 `pip`
- 可选：用于生成助手回复的 OpenAI 兼容 LLM 服务

### 1. 配置

```bash
cp .env.example .env
# 默认 SQLite + FTS 配置无需模型凭证即可运行记忆层
```

复制后的模板默认将 PowerContext 数据存入本地 SQLite。需要使用 [OceanBase](https://github.com/oceanbase/oceanbase) 时，把 `POWERCONTEXT_DATABASE_URL` 改为官方 `mysql+aoceanbase` URL。

### 2. 启动后端

```bash
make install-backend # 若 ../powercontext 源码存在，会优先以 editable 方式安装
make backend        # FastAPI 运行在 http://127.0.0.1:8000，API 文档在 /docs
```

### 3. 启动前端

```bash
cd scenarios/smart-ev-cockpit/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

浏览器打开 `http://localhost:5173`。远程开发机上请转发 `5173` 和 `8000` 两个端口（开发服务器会把 `/api` 代理到后端）。

### 4. 导入演示数据

场景 5–9 需要检索历史记忆，请先填充记忆库：在页面顶部数据栏确认记忆数量（默认 1200，可配置），点击**生成**，再点击**导入**。每条导入数据都会先采集为 PowerContext Source，再形成带 citation 的 Memory entry。

之后通过 **下一个 → 发送** 逐幕推进，并打开**证据**面板查看记忆命中、车辆状态 diff、隐私脱敏和审计日志。

## 配置说明

所有配置都在 `.env` 中（参考 [.env.example](.env.example)）：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `POWERCONTEXT_BACKEND` | PowerContext 集成模式 | `builtin` |
| `POWERCONTEXT_SCOPE_ID` | 隔离 Source 与 Memory 的 scope | `smart-ev-cockpit` |
| `POWERCONTEXT_DATABASE_URL` | SQLite 或 OceanBase 异步 SQLAlchemy URL | `sqlite+aiosqlite:///data/powercontext_smart_ev.db` |
| `POWERCONTEXT_OPERATION_TIMEOUT_SECONDS` | Runtime 调用超时 | `30` |
| `LLM_PROVIDER` / `LLM_MODEL` | 可选的助手回复模型 | `openai` / — |
| `LLM_API_KEY`, `OPENAI_LLM_BASE_URL` | OpenAI 兼容服务的凭证与地址 | — |
| `DEMO_PRIVACY_MODE` | 隐私投影严格程度 | `strict` |

## 测试

```bash
make test-backend     # pytest，包含十幕验收测试
make lint-backend     # ruff
make test-frontend    # vitest
```

## 仓库结构

```
awesome-powercontext/
├── docs/                       # 项目文档（中英文）：概览、架构、隐私、演示手册
├── scenarios/
│   └── smart-ev-cockpit/
│       ├── backend/            # 封装 PowerContext Builtin Runtime 的 FastAPI 应用
│       ├── frontend/           # Vite + React 座舱界面
│       ├── data/synthetic/     # 合成场景数据（不含真实 PII）
│       └── docs/               # 场景演示手册
├── Makefile
└── .env.example
```

## 文档

- [概览](docs/zh/overview.md) · [架构](docs/zh/architecture.md) · [隐私](docs/zh/privacy.md) · [Live 证据](docs/zh/live-evidence.md) · [开发](docs/zh/development.md)
- [智能座舱场景说明](docs/zh/scenarios/smart-ev-cockpit.md) · [演示手册](docs/zh/scenarios/smart-ev-cockpit-playbook.md) · [操作指引](docs/zh/scenarios/smart-ev-cockpit-operation-guide.md)
- English docs: [docs/en/](docs/en/)

## 隐私

所有场景数据均为合成数据。仓库中不包含真实汽车品牌、真实用户身份、车辆标识、地址、电话号码或任何凭证。详见[隐私文档](docs/zh/privacy.md)和 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 参与贡献

欢迎贡献新的 PowerContext 场景，见 [CONTRIBUTING.md](CONTRIBUTING.md)。代码、注释、路径、API 字段和提交信息使用英文；公开数据必须保持合成。

## 许可证

Apache License 2.0，与 [PowerContext](https://github.com/oceanbase/powercontext) 保持一致。
