# 智能电动车座舱记忆演示 — 完整操作指引

本指引面向演示者（presenter），覆盖从环境检查、数据准备、十幕演示到收尾清理的全过程。演示话术与每一幕的讲解要点见[演示手册](smart-ev-cockpit-playbook.md)，本文重点是"怎么操作"。

---

## 1. 演示架构一览

| 组件 | 默认地址 | 说明 |
|---|---|---|
| 前端 (Vite + React) | `:5173` | 演示界面，`/api` 请求由 Vite 代理转发到后端 |
| 后端 (FastAPI) | `127.0.0.1:8000` | 场景编排 + PowerContext Builtin Runtime（builtin 模式） |
| PowerContext | 随后端加载（pip 包 `powercontext`） | Source capture、Memory revision、FTS 检索和 retire |
| 记忆存储 | SQLite（默认） | 由 `POWERCONTEXT_DATABASE_URL` 配置，也可切换为 OceanBase |
| LLM | `.env` 中可选的 OpenAI 兼容服务 | 生成助手回复；记忆层本身无需模型凭证 |

演示访问地址：本机打开 `http://localhost:5173/`。如需让同网段的其他电脑观看，启动前端时绑定 `--host 0.0.0.0`，观众访问 `http://<演示机IP>:5173/`（记得放行防火墙的 5173 端口）。

---

## 2. 演示前环境检查（约 2 分钟）

在演示机上依次执行。默认 SQLite 模式只需检查前后端；如果配置了可选 LLM 或 OceanBase，再检查对应服务：

```bash
# 加载 .env，供后续检查命令读取连接参数
set -a
source .env
set +a

# ① 后端健康检查，期望返回 {"status":"ok",...}
curl -s http://127.0.0.1:8000/api/health

# ② 前端是否在监听 5173
ss -tlnp | grep 5173

# ③ 可选：LLM 服务连通性，期望 HTTP 200
curl -s -o /dev/null -w "%{http_code}\n" "$OPENAI_LLM_BASE_URL/models" \
  -H "Authorization: Bearer $LLM_API_KEY"

# ④ 当前 PowerContext 存储配置
printf '%s\n' "$POWERCONTEXT_DATABASE_URL"
```

任一项不通时的启动命令（在项目根目录下执行）：

```bash
# 启动后端（前台，Ctrl+C 停止；首次先执行 make install-backend）
make backend

# 或后台常驻，日志写到 logs/backend.log
mkdir -p logs && cd scenarios/smart-ev-cockpit/backend && \
nohup python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 > ../../../logs/backend.log 2>&1 &

# 启动前端（首次先在 frontend 目录执行 npm install；
# 仅本机演示用 --host 127.0.0.1，需远程观看改为 --host 0.0.0.0）
cd scenarios/smart-ev-cockpit/frontend && \
npm run dev -- --host 0.0.0.0 --port 5173
```

> 注意：后端 8000 只需绑定 127.0.0.1，不建议对外开放——前端开发服务器会代理 `/api`。

---

## 3. 演示数据准备（首次或重置后必做）

十幕中的场景 5–9（地点回忆、多媒体偏好、纪念日、驾驶模式、主动关怀）依赖"历史记忆"才能命中检索结果。**记忆库为空时必须先导入合成测试数据**，否则这些幕会检索不到内容。

操作全部在页面**顶部数据栏**完成：

1. 打开演示页面，找到顶部的测试数据面板。
2. 如需使用自定义 PowerContext 用户身份，先在座位身份面板设置驾驶员 / 乘客 / 后排儿童的 `user_id`。后续生成和导入都会把 actor 映射到当前最新的 `user_id`。
3. 确认 **记忆数量** 输入框；不改时默认生成 1200 条，也可以改成 1–10000 内的数量。
4. 点击 **生成**（seed=42，可复现）。每次生成都会创建新的 dataset_id / `.jsonl` 文件名，文件名包含生成时间和短后缀，不会覆盖上一次结果。状态会显示"生成中 → 已生成 N 条"。
5. 点击 **导入**（写入 PowerContext，并发 8 线程）。每条数据会采集为 Source 并形成带 citation 的 Memory entry；状态显示"已导入 X / N 条"。
6. 状态变为"已导入"后即可开始演示。

命令行等价操作（可选，便于提前准备）：

```bash
# 生成
# 省略 count 时默认生成 1200 条；需要更少或更多时设置 count。
curl -s -X POST http://127.0.0.1:8000/api/scenarios/smart-ev-cockpit/test-data/generate \
  -H 'Content-Type: application/json' -d '{"count":1200,"seed":42,"locale":"zh"}'

# 查看状态（拿到 dataset_id，并可轮询导入进度）
curl -s http://127.0.0.1:8000/api/scenarios/smart-ev-cockpit/test-data/status

# 导入（dataset_id 换成上一步返回的值）
curl -s -X POST http://127.0.0.1:8000/api/scenarios/smart-ev-cockpit/test-data/import \
  -H 'Content-Type: application/json' \
  -d '{"dataset_id":"<dataset_id>","apply":true,"max_workers":8}'
```

---

## 4. 界面布局速览

- **顶部数据栏**：测试数据（生成 / 导入 / 删除）、语言切换（EN / 中文，默认中文）、**证据**按钮。
- **座舱舞台（主画面）**：
  - **座位选择器**：主驾 / 前排乘客 / 后排儿童，点击切换当前说话人；齿轮图标可打开身份设置面板。
  - **内饰主题选择器**：仅视觉效果，不影响演示逻辑。
  - **手动控制键**：显示当前"第 N 天 | 场景 N"，含四个按钮——
    - **重置**：回到场景 1，清空当前回应（不删除已存的记忆）；
    - **重播**：重发上一句话；
    - **下一个**：切到下一幕，自动预填该幕的台词和说话人；
    - **导出**：下载完整 trace JSON（`smart-ev-cockpit-trace.json`）。
  - **对话面板**：显示台词输入框和聊天记录，点击发送提交。
- **证据弹窗**（点顶部"证据"打开，面向开发者/评委的深度视图）：
  - 场景时间轴（可直接点选任意一幕）；
  - 记忆流面板（命中的 memory 卡片 + 隐私条）；
  - 车辆状态面板（车控字段 before/after diff）；
  - 推荐面板、记忆图谱；
  - 开发者证据抽屉（原始 SEARCH filters、selected memory IDs、operations）；
  - 生命周期面板（retention score、ADD/UPDATE/DELETE 审计）。

---

## 5. 十幕演示流程

**标准操作节奏**：每一幕都是 —— 点 **下一个**（台词和说话人已自动填好）→ 点 **发送** → 在主画面看助手回应和车控变化 → 需要深讲时点 **证据** 看检索/隐私/审计细节 → 关闭证据弹窗，进入下一幕。

场景 1 是起点（打开页面即处于场景 1），直接发送即可；之后每幕点"下一个"推进。

| 幕 | 天数 | 说话人 | 台词（自动预填） | 看点 |
|---|---|---|---|---|
| 场景 1 建立记忆 | 第 1 天 | 主驾 | 按当前季节生成；夏季示例：我夏天上车一般 23C，座椅加热 0 档。 | 证据面板出现 **ADD** 操作，底层可追溯到 Source citation 与 Memory revision |
| 场景 2 同一句话，不同人 | 第 7 天 | 主驾（**手动再切前排乘客、后排儿童各发一次**） | 按当前季节生成；夏季示例：车里有点热。 | 三人得到不同车控 patch；儿童命中安全策略记忆；SEARCH filters 里带 actor + 座位 |
| 场景 4 车辆能力边界 | 第 21 天 | 主驾 | 这台车支持小憩模式吗？ | 命中 `vehicle_capability` 记忆，助手不编造能力，不执行任何车控 |
| 场景 5 地点回忆 | 第 28 天 | 主驾 | 带我去上周五那家餐厅。 | 返回泛化后的地点记忆；精确地址被隐藏（`visibility=masked`） |
| 场景 6 多媒体偏好 | 第 35 天 | **后排儿童**（自动切换） | 放点适合孩子睡觉的内容。 | 命中媒体偏好 + 安全策略；儿童身份只显示为 `child_rear_left` |
| 场景 7 纪念日推荐 | 第 42 天 | 主驾 | 今晚有什么安排建议？ | 命中 `relationship_event`；推荐卡片出现，但完整纪念日日期被脱敏 |
| 场景 8 驾驶模式建议 | 第 56 天 | 主驾 | 建议一下这段路的驾驶模式。 | 长期驾驶偏好 + 当前车辆状态共同决定建议；通勤路线保持区域级泛化 |
| 场景 9 主动关怀 | 第 70 天 | 主驾 | （台词为触发语，前端自动改调 `POST /events/vehicle` 低电量事件） | SOC/续航从正常变为低电量；助手用个性化语气主动提醒充电（命中 `emotional_preference`） |
| 场景 10 生命周期与隐私 | 第 90 天 | 主驾 | （前端自动改调 `POST /lifecycle/run`，current_day=90） | 首次运行看到 `temporary_context` 被清理，例如 `DELETE: deleted (ok)`；重复运行看到 `REVIEW: unchanged (no_candidates)`，表示没有新的到期短期记忆；每条记录都有审计 trace |

场景 2 的补充操作：发送主驾的"有点冷"之后，**不要点"下一个"**，先在座位选择器点"前排乘客"，在输入框输入"有点冷"发送；再切"后排儿童"重复一次。对比三次的车控差异后，再点"下一个"进入场景 3。

场景 9 和 10 无需记任何 API——前端识别到 act_key 为 Act 9 / Act 10 时会自动调用对应的车辆事件和生命周期接口，操作上仍然是"下一个 → 发送"。

收尾动作：点 **导出** 下载完整 trace JSON，向观众展示全程每一次 PowerContext 操作都可追溯。

**Presenter 铁律**（来自演示手册）：只讲后端真实返回的 memory hits 和 trace evidence；如果 PowerContext 不可用，页面会显示 live-mode 错误——此时停止演示排查问题，不要脱稿编造。

---

## 6. 常见问题排查

| 现象 | 原因与处理 |
|---|---|
| 页面打不开（远程观看） | 防火墙未放行 5173；或前端只绑了 127.0.0.1——用 `--host 0.0.0.0` 重启前端 |
| 页面顶部出现 live-mode 错误条 | 后端挂了或 PowerContext 初始化失败。看 `logs/backend.log`；SQLite 模式检查数据库路径权限，OceanBase 模式检查 URL 和数据库连通性 |
| 场景 5–9 检索不到记忆（memory hits 为空） | 测试数据没导入。按第 3 节生成 + 导入 |
| 发送后长时间转圈 | 若启用了 LLM，先用第 2 节第③项验证；否则检查后端日志中的 PowerContext operation timeout |
| 导入进度卡住 | 看 `test-data/status` 里的 `failed_count` 和 `last_error`；SQLite 锁竞争时降低 `max_workers` 重试 |
| 想彻底重来一遍 | 顶部数据栏点 **删除**（删除已导入的数据集），或命令行 `DELETE /api/scenarios/smart-ev-cockpit/test-data/<dataset_id>`；然后重新生成 + 导入。界面上的"重置"只回到场景 1，**不清数据** |

后端接口自查入口：http://127.0.0.1:8000/docs （FastAPI Swagger，仅本机可访问）。

---

## 7. 演示结束后

- 如需保留现场供复盘：点 **导出** 保存 trace JSON 即可，服务可以继续挂着。
- 如需清理：顶部数据栏点 **删除** 清掉演示数据集；需要停服务时：

```bash
pkill -f 'uvicorn app.main:app'             # 停后端
pkill -f 'vite --host 0.0.0.0 --port 5173'  # 停前端（按实际启动参数调整）
```

（如果记忆存储使用共享 OceanBase 集群，只清数据集即可，**不要**停数据库进程。）
