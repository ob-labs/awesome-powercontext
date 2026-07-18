# Smart EV Cockpit 十个场景使用与 PowerMem 能力说明

本文面向演示者、评审和开发协作者，说明智能电动车座舱 demo 的十个场景怎么使用、每个场景在证明 PowerMem 的什么能力，以及在界面和证据面板里应该看什么。

相关文档：

- 快速话术：`docs/zh/scenarios/smart-ev-cockpit-playbook.md`
- 完整操作：`docs/zh/scenarios/smart-ev-cockpit-operation-guide.md`
- 场景代码：`scenarios/smart-ev-cockpit/backend/app/services/acts/`

---

## 1. Demo 要证明什么

这个 demo 不是展示一个普通车载聊天机器人，而是展示一个由 PowerMem 支撑的“可记忆、可治理、可证明”的座舱助手。

它覆盖 10 类能力：

| 场景 | 用户体验 | PowerMem 能力 |
|---|---|---|
| 1 建立偏好 | 用户说出长期座舱偏好 | 结构化记忆写入 `ADD` |
| 2 同句不同人 | 同一句“有点冷/热”因乘员不同而动作不同 | actor + seat scoped retrieval |
| 3 组合例程 | 一句话恢复空调、座椅、驾驶模式 | 多记忆检索与组合决策 |
| 4 能力边界 | 问车辆是否支持某功能，不支持就拒绝执行 | 结构化 metadata + filter + policy guard |
| 5 地点回忆 | 记得上周五餐厅，但只给区域级目的地 | 隐私投影与脱敏召回 |
| 6 儿童媒体 | 给儿童播放安全低音量内容 | 偏好记忆 + safety policy |
| 7 关系推荐 | 结合纪念日给建议，但不暴露日期 | 敏感关系记忆治理 |
| 8 驾驶模式 | 结合驾驶偏好和车辆状态给建议 | 长期偏好 + live vehicle context |
| 9 主动关怀 | 低电量事件主动提醒充电 | 车辆事件触发 proactive recall |
| 10 生命周期 | 第 90 天衰减、归档或删除短期记忆 | lifecycle status / retention governance |

一句话总结：

> PowerMem 在这里承担“长期记忆基础设施”的角色：把对话、车辆状态、偏好、地点、关系、策略和生命周期都变成可检索、可过滤、可审计的 memory evidence。

---

## 2. 演示前准备

### 2.1 启动服务

从项目根目录启动：

```bash
# 后端
make backend

# 前端
cd scenarios/smart-ev-cockpit/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

访问：

```text
http://localhost:5173/
```

### 2.2 导入测试数据

场景 5 到场景 9 依赖历史记忆。如果 PowerMem 里没有数据，需要先在页面顶部数据栏点击：

```text
数据生成 -> 数据导入
```

默认生成 1200 条合成记忆，覆盖地点、关系、媒体、驾驶、充电、情感偏好等类型。

命令行等价：

```bash
curl -s -X POST http://127.0.0.1:8000/api/scenarios/smart-ev-cockpit/test-data/generate \
  -H 'Content-Type: application/json' \
  -d '{"count":1200,"seed":42,"locale":"zh"}'

curl -s http://127.0.0.1:8000/api/scenarios/smart-ev-cockpit/test-data/status

curl -s -X POST http://127.0.0.1:8000/api/scenarios/smart-ev-cockpit/test-data/import \
  -H 'Content-Type: application/json' \
  -d '{"dataset_id":"<dataset_id>","apply":true,"max_workers":8}'
```

### 2.3 标准演示节奏

每个场景按同一节奏演示：

1. 点击右侧车机或手动控制区的“下一个”进入场景。
2. 输入框会自动预填当前场景台词。
3. 点击“发送”。
4. 在主画面看助手回复、车机变化、车辆状态变化。
5. 点击顶部“证据”查看 PowerMem operations、memory hits、selected memory IDs、reason codes 和 vehicle diff。
6. 关闭证据弹窗，进入下一幕。

注意：场景 9 和场景 10 表面上也使用“发送”，但前端会自动改调特殊接口：

- 场景 9：`POST /api/scenarios/smart-ev-cockpit/events/vehicle`
- 场景 10：`POST /api/scenarios/smart-ev-cockpit/lifecycle/run`

---

## 3. PowerMem 在这个 demo 里的实现方式

### 3.1 记忆结构

座舱 demo 把每条记忆抽象成：

```text
MemoryRecord
  memory_id
  content
  metadata
```

关键 metadata 字段包括：

| 字段 | 用途 |
|---|---|
| `scenario_id` | 固定为 `smart_ev_cockpit`，隔离场景数据 |
| `vehicle_id` | 固定为 `demo_vehicle_001`，隔离车辆 |
| `actor_id` | 主驾、前排乘客、后排儿童 |
| `seat_position` | `front_left` / `front_right` / `rear_left` |
| `memory_kind` | 记忆类型，例如 `cabin_control_preference`、`location_episode` |
| `memory_dimension` | 记忆维度，例如 procedural / capability / safety |
| `privacy_level` / `visibility` | 展示和脱敏策略 |
| `source_event_ids` | 记忆来源事件 |
| `confidence` | 排序和选择参考 |
| `retention_score` | 生命周期治理参考 |
| `lifecycle_status` | `active` / `decayed` / `archived` / `deleted` |

主要记忆类型：

```text
person_profile
relationship_event
vehicle_capability
cabin_control_preference
media_preference
location_episode
driving_preference
charging_preference
emotional_preference
temporary_context
safety_policy
```

### 3.2 PowerMem 调用

后端通过 `MemoryService` 包一层 PowerMem SDK：

```python
memory.add(content, user_id=user_id, metadata=metadata, infer=False)
memory.search(query=query, user_id=user_id, filters=filters, limit=limit)
memory.update(memory_id=..., content=..., metadata=...)
memory.delete(memory_id)
memory.get_all(filters=..., user_id=..., limit=...)
```

在证据面板里，你主要看：

| 证据字段 | 说明 |
|---|---|
| `operations` | PowerMem 做了 ADD / SEARCH / UPDATE / DELETE / VEHICLE_PATCH |
| `query` | 本次检索的语义查询 |
| `filters` | 结构化过滤条件 |
| `memory_hits` | 命中的记忆 |
| `selected_memory_ids` | 最终被采用的记忆 ID |
| `reason_codes` | 决策原因 |
| `vehicle_state_diff` | 对车辆状态的字段级变化 |
| `privacy_report` | 隐私处理结果 |
| `lifecycle` / `audit` | 生命周期治理审计 |

### 3.3 PowerMem 和应用层的边界

PowerMem 负责：

- 存储长期记忆；
- 用语义 query + metadata filters 检索；
- 返回 memory hits 和分数；
- 支持 update / delete / get_all 等生命周期操作；
- 让每次操作可以被 evidence trace 记录。

应用层负责：

- 根据场景构造 query 和 filters；
- 根据命中结果做业务决策；
- 做隐私投影；
- 生成车辆状态 patch；
- 决定哪些 memory ID 被采用；
- 把 reason code 和 trace 返回前端。

所以不要把它讲成“大模型自己记住了”。更准确的说法是：

> PowerMem 提供可检索、可过滤、可治理的长期记忆层；座舱应用基于这些 memory evidence 做可解释决策。

---

## 4. 十个场景完整说明

### 场景 1：建立偏好

**演示目标**

证明 PowerMem 可以把用户自然语言中的偏好抽取成结构化长期记忆，而不是把聊天原文当数据库保存。

**怎么使用**

- 页面初始就是场景 1。
- 说话人：主驾。
- 输入示例：`我冬天上车一般 26C，座椅加热 2 档。`
- 点击“发送”。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 1"
```

**PowerMem 做了什么**

后端解析温度、座椅加热档位和季节，然后调用 PowerMem `ADD`：

```text
memory_kind = cabin_control_preference
memory_dimension = ["procedural", "environmental"]
actor_id = driver_primary
seat_position = front_left
season = winter
target_temp_c = 26
seat_heat_level = 2
```

**展示的 PowerMem 能力**

- 从自然语言提取结构化记忆；
- 以 metadata 形式保存可过滤字段；
- 绑定 `actor_id`、`seat_position`、`session_id`；
- 保留 `source_event_ids`，方便追溯来源；
- 可以立即把新记忆用于车辆动作。

**证据面板看什么**

- `operations[0].type = ADD`
- 新增 memory ID；
- `memory_kind=cabin_control_preference`
- `vehicle_state_diff` 中 HVAC 和 seat heat 的 before/after；
- `reason_codes` 包含 `cabin_preference_saved`。

**讲解话术**

> 这一幕证明 PowerMem 保存的是“可复用偏好”，不是原始聊天记录。用户说一句自然语言，系统写入的是带 actor、seat、season、temperature、seat heat 等 metadata 的长期记忆。

---

### 场景 2：同一句话，不同人

**演示目标**

证明 PowerMem 的记忆检索不是全局混用，而是能按人、座位和安全策略隔离。

**怎么使用**

- 进入场景 2。
- 默认说话人：主驾。
- 输入示例：`有点冷。`
- 发送后，可以手动切换到前排乘客、后排儿童，再分别发送同一句话。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 2"
```

**PowerMem 做了什么**

构造检索：

```text
query = cold cabin preferences and safety policy for <actor_id> <seat_position>
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  actor_id = 当前说话人
  seat_position = 当前座位
  memory_kind in ["cabin_control_preference", "safety_policy"]
```

然后应用 `RecommendationService.decide_cold_cabin_action()`：

- 优先找当前 actor + seat 的 `cabin_control_preference`；
- 如果命中 `safety_policy`，会移除不允许执行的控制项；
- 对儿童或敏感策略，只应用安全范围内的 patch。

**展示的 PowerMem 能力**

- actor-scoped memory retrieval；
- seat-scoped memory retrieval；
- 同一句话根据乘员上下文得到不同动作；
- 安全策略作为记忆参与决策；
- selected memory IDs 证明采用了哪些记忆。

**证据面板看什么**

- SEARCH filters 是否包含当前 `actor_id` 和 `seat_position`；
- `memory_kind in ["cabin_control_preference", "safety_policy"]`；
- 主驾、前排乘客、儿童三次的 `selected_memory_ids` 不同；
- `vehicle_state_diff` 中不同座位的 HVAC / seat heat patch；
- `reason_codes` 可能包含 `cabin_preference_applied`、`heat_sensitivity_applied`、`safety_policy_applied`。

**讲解话术**

> 这一幕的关键是“同一句话，不同人”。PowerMem 不是简单取最近的偏好，而是用 actor_id 和 seat_position 限定检索范围，再让安全策略决定哪些动作可以执行。

---

### 场景 3：组合车控例程

**演示目标**

证明 PowerMem 可以把多条长期记忆组合成一个可执行例程，而不是只返回一条记忆。

**怎么使用**

- 进入场景 3。
- 说话人：主驾。
- 输入示例：`按我上次舒服的设置来。`
- 点击“发送”。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 3"
```

**PowerMem 做了什么**

构造检索：

```text
query = previous cabin and driving routine for <actor_id> <seat_position>
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  actor_id = 当前说话人
  seat_position = 当前座位
  memory_kind in ["cabin_control_preference", "driving_preference"]
```

后端从命中结果里分别取：

- `cabin_control_preference`：温度、座椅加热；
- `driving_preference`：驾驶模式。

再组合成一个 `vehicle_patch`。

**展示的 PowerMem 能力**

- 多 memory kind 联合检索；
- 把偏好记忆组合成动作；
- 支持 partial routine：只命中部分记忆时也能应用可用部分；
- selected memory IDs 显示每个动作来自哪条记忆。

**证据面板看什么**

- `memory_kind in ["cabin_control_preference", "driving_preference"]`；
- `selected_memory_ids` 是否包含座舱偏好和驾驶偏好；
- `vehicle_state_diff` 是否包含 HVAC、seat heat、drive mode；
- `reason_codes` 是 `complete_routine` 或 `partial_routine`。

**讲解话术**

> 这一幕证明 PowerMem 的输出不是“搜到一条文本”。应用可以把多条记忆变成一个完整例程：空调、座椅和驾驶模式都来自可追溯的 memory evidence。

---

### 场景 4：车辆能力边界

**演示目标**

证明 PowerMem 可以参与能力事实核验，避免助手编造车辆能力或执行不支持的车控。

**怎么使用**

- 进入场景 4。
- 说话人：主驾。
- 输入示例：`这台车支持小憩模式吗？`
- 点击“发送”。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 4"
```

**PowerMem 做了什么**

构造检索：

```text
query = vehicle capability rest_mode for <actor_id>
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  memory_kind = vehicle_capability
```

同时读取车辆档案：

```text
unsupported_features contains "rest_mode"
```

如果车辆档案显示 `rest_mode` 不支持，助手回答不支持，并且不生成车控 patch。

**展示的 PowerMem 能力**

这一幕可以直接讲：

> 在 PowerMem 里，这个能力边界主要靠结构化记忆 metadata + 检索 filter + 应用层策略判断实现。

具体来说：

- `vehicle_capability` 记忆说明能力信息的来源；
- metadata 里有 `capability_feature=rest_mode`、`capability_source_field=un_support_funcs`；
- filter 限定只查当前车辆的能力类记忆；
- 应用层把 PowerMem 记忆和车辆档案 `unsupported_features` 一起判断；
- 不支持时返回 `unsupported_vehicle_feature`，不执行任何车辆命令。

**证据面板看什么**

- SEARCH filters：`memory_kind=vehicle_capability`；
- 命中的 memory 是否包含 `capability_feature=rest_mode`；
- `data_source` 是车辆档案来源，例如 `synthetic_fallback` 或 `masked_vehicle_csv`；
- `reason_codes` 包含 `unsupported_vehicle_feature`；
- 没有 `vehicle_state_diff`，因为没有执行车控。

**讲解话术**

> 很多车载助手的问题是“问什么都敢答”。这一幕证明 PowerMem 可以让助手基于车辆能力记忆和车辆档案回答，不知道或不支持就拒绝，不把幻想变成车控动作。

---

### 场景 5：地点回忆

**演示目标**

证明 PowerMem 可以召回地点类记忆，但通过隐私投影只返回区域级信息，不暴露精确地址。

**怎么使用**

- 进入场景 5。
- 说话人：主驾。
- 输入示例：`带我去上周五那家餐厅。`
- 点击“发送”。
- 可选：再输入 `确认导航`，触发地图模式。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 5"
```

**PowerMem 做了什么**

构造检索：

```text
query = region-level location recall for <actor_id> <seat_position>
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  actor_id = 当前说话人
  seat_position = 当前座位
  memory_kind = location_episode
```

后端把 presenter view 的 location memory 改成：

```text
visibility = masked
privacy_level = masked
is_sensitive = true
```

只把 `region` 这样的区域级字段用于推荐。

**展示的 PowerMem 能力**

- 地点 episodic memory recall；
- 通过 metadata filter 只查当前用户/座位的地点；
- 隐私投影：精确地址不展示；
- 推荐需要确认，不直接导航；
- 用户确认后才生成 navigation patch。

**证据面板看什么**

- `memory_kind=location_episode`；
- `visibility=masked`；
- `privacy_level=masked`；
- `reason_codes` 包含 `location_exact_fields_masked`；
- 首次推荐的 `action_policy=confirm`；
- 确认后 `vehicle_state_diff` 或 patch 包含 navigation map mode。

**讲解话术**

> PowerMem 可以记得“上周五那家餐厅”这种上下文，但前端展示的是隐私投影后的结果。用户得到可用的导航建议，评审看得到 evidence，但精确地址不会暴露。

---

### 场景 6：儿童媒体

**演示目标**

证明 PowerMem 可以把儿童媒体偏好和安全策略一起检索，用策略约束个性化结果。

**怎么使用**

- 进入场景 6。
- 前端会自动切到后排儿童。
- 输入示例：`放点适合孩子睡觉的内容。`
- 点击“发送”。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 6"
```

**PowerMem 做了什么**

构造检索：

```text
query = child-safe sleep media for child_rear_left rear_left
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  actor_id = child_rear_left
  seat_position = rear_left
  memory_kind in ["media_preference", "safety_policy"]
```

后端取：

- `media_preference`：内容类别、历史音量；
- `safety_policy`：最大允许音量 `max_media_volume`。

最终推荐音量是：

```text
min(media_preference.media_volume, safety_policy.max_media_volume)
```

**展示的 PowerMem 能力**

- 偏好记忆与策略记忆联合检索；
- 儿童身份和座位强约束；
- safety policy 可以覆盖个性化偏好；
- 推荐结果是 suggest，不是直接强制播放。

**证据面板看什么**

- SEARCH filters 固定到 `child_rear_left` + `rear_left`；
- 命中 `media_preference` 和 `safety_policy`；
- `selected_memory_ids` 包含两类记忆；
- `reason_codes` 包含 `child_safe_media_suggestion` 和 `safety_volume_cap_applied`；
- recommendation metadata 里有 `content_category` 和最终 `volume`。

**讲解话术**

> 个性化不是越个人越好，儿童场景必须先过安全策略。PowerMem 让 preference 和 policy 都是记忆，决策时可以明确看到是哪条偏好和哪条策略共同影响结果。

---

### 场景 7：纪念日推荐

**演示目标**

证明 PowerMem 可以使用关系类敏感记忆做温和推荐，同时隐藏敏感日期和精确地点。

**怎么使用**

- 进入场景 7。
- 说话人：主驾。
- 输入示例：`今晚有什么安排建议？`
- 点击“发送”。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 7"
```

**PowerMem 做了什么**

构造检索：

```text
query = relationship suggestions for <actor_id> with region-safe context
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  actor_id = 当前说话人
  seat_position = 当前座位
  memory_kind in ["relationship_event", "location_episode"]
```

后端把关系和地点记忆都投影成 masked：

```text
visibility = masked
privacy_level = masked
is_sensitive = true
```

返回推荐时用安全摘要：

```text
可以考虑今晚安排一次安静的晚餐。
```

完整纪念日日期只显示为：

```text
anniversary date masked
```

**展示的 PowerMem 能力**

- relationship event memory；
- 敏感关系字段脱敏；
- relationship memory + location memory 联合推荐；
- 不自动导航，只给 suggest；
- 推荐可以有温度，但证据保持可审计。

**证据面板看什么**

- `memory_kind in ["relationship_event", "location_episode"]`；
- `selected_memory_ids` 是否包含 relationship 和 location；
- `reason_codes` 包含 `relationship_suggestion`、`anniversary_date_masked`；
- recommendation 的 `action_policy=suggest`；
- metadata 里 `date=anniversary date masked`。

**讲解话术**

> 这一幕不是为了展示“记得越多越好”，而是展示敏感记忆如何被治理。PowerMem 可以让关系事件参与推荐，但日期和地点都经过投影，应用只拿到安全摘要。

---

### 场景 8：驾驶模式建议

**演示目标**

证明 PowerMem 可以结合长期驾驶偏好和实时车辆状态，生成可解释的驾驶模式建议。

**怎么使用**

- 进入场景 8。
- 说话人：主驾。
- 输入示例：`建议这次出行的驾驶模式。`
- 点击“发送”。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/utter
act_key = "Act 8"
```

**PowerMem 做了什么**

构造检索：

```text
query = safe driving preference for <actor_id>
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  actor_id = 当前说话人
  seat_position = 当前座位
  memory_kind in ["driving_preference", "emotional_preference"]
```

同时读取车辆 telemetry：

```text
soc
outside_temp_c
range_km
```

决策逻辑：

- 如果 SOC < 20，优先建议 eco；
- 如果极冷天气且原偏好为 sport，降为 comfort；
- 否则使用 `driving_preference.drive_mode`。

**展示的 PowerMem 能力**

- 长期驾驶偏好检索；
- live vehicle context 参与决策；
- 推荐可解释：偏好、SOC、外温都在证据里；
- 不直接执行驾驶模式，只作为 suggest。

**证据面板看什么**

- `memory_kind in ["driving_preference", "emotional_preference"]`；
- `data_source` 来自 telemetry 来源；
- recommendation metadata 里有 `drive_mode`、`soc`、`outside_temp_c`；
- `reason_codes` 可能包含 `driving_preference`、`low_soc`、`cold_weather_caution`。

**讲解话术**

> 驾驶模式不是纯偏好问题，也不是纯车态问题。PowerMem 提供长期偏好，车辆 telemetry 提供实时约束，最终建议能解释为什么这么选。

---

### 场景 9：主动关怀

**演示目标**

证明 PowerMem 不只响应用户提问，也能被车辆事件触发，做主动、个性化、可确认的提醒。

**怎么使用**

- 进入场景 9。
- 页面输入框会显示低电量触发语。
- 点击“发送”。
- 前端会自动调用车辆事件接口，传入：

```text
soc = 9
range_km = 42
```

- 如果助手要求确认导航，可以再输入 `确认导航`。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/events/vehicle
```

**PowerMem 做了什么**

构造检索：

```text
query = proactive low energy support for <actor_id>
filters:
  scenario_id = smart_ev_cockpit
  vehicle_id = demo_vehicle_001
  actor_id = 当前说话人
  seat_position = 当前座位
  memory_kind in ["charging_preference", "driving_preference", "emotional_preference"]
```

后端取：

- `charging_preference`：充电站选择策略，例如最近可用；
- `emotional_preference`：提醒语气，例如 calm / reassuring / direct；
- 车辆事件：SOC 和剩余续航。

如果 SOC < 10：

- `reason_codes=["critical_soc"]`；
- recommendation `action_policy=confirm`；
- 用户确认后生成 navigation patch。

**展示的 PowerMem 能力**

- vehicle-event-triggered recall；
- 主动关怀不是定时提醒，而是状态 + 记忆触发；
- 充电偏好决定推荐策略；
- 情感偏好决定提醒语气；
- 高风险动作需要 confirmation；
- 低电量事件和记忆采用都有 trace。

**证据面板看什么**

- 接口是 `/events/vehicle`，不是普通 `/utter`；
- `vehicle_patch` 包含 `soc=9`、`range_km=42`；
- 命中 `charging_preference`、`emotional_preference`；
- `selected_memory_ids` 包含充电偏好和情感偏好；
- `reason_codes` 包含 `critical_soc`；
- recommendation `type=charging_safety`、`action_policy=confirm`；
- 确认导航后出现 `charging_navigation_confirmed` 和 navigation patch。

**讲解话术**

> 这一幕证明 PowerMem 可以支撑 proactive experience。触发点不是用户问了什么，而是车辆低电量事件；但提醒方式和充电建议仍然来自用户长期记忆，并且高风险动作需要确认。

---

### 场景 10：生命周期与隐私

**演示目标**

证明 PowerMem 不是无限堆积记忆，而是能按 retention 和 lifecycle 规则衰减、归档、删除，并保留审计证据。

**怎么使用**

- 进入场景 10。
- 点击“发送”。
- 前端会自动调用生命周期接口，传入：

```text
current_day = 90
```

首次演示时，默认 seed 会提供一条已经超过有效期的 `temporary_context`，因此生命周期面板应该看到至少一条 `DELETE: deleted (ok)` 记录。  
如果同一份 PowerMem 数据已经跑过一次生命周期清理，再次点击时不会重复删除，面板会显示 `REVIEW: unchanged (no_candidates)`，表示第 90 天复核完成，但当前没有新的短期记忆需要处理。

**接口**

```text
POST /api/scenarios/smart-ev-cockpit/lifecycle/run
```

**PowerMem 做了什么**

先读取相关记忆：

```text
memory_kind in ["driving_preference", "emotional_preference", "temporary_context"]
```

然后 `LifecycleService` 根据当前天数和 metadata 生成计划：

- `temporary_context` 到期后衰减或删除；
- 低 retention score 的短期事实退出 active 层；
- 长期偏好保持 active 或 reinforced；
- 每个 UPDATE / DELETE 都写入 audit。

**展示的 PowerMem 能力**

- lifecycle governance；
- retention score；
- lifecycle status；
- archive / delete / decay；
- 审计 trace；
- 长期偏好和短期上下文区别处理。

**证据面板看什么**

- `plan`：将要执行的生命周期操作；
- `completed_operations`：实际完成的 UPDATE / DELETE；
- `audit`：每条变更的 trace_id；
- 重复运行时的 `REVIEW / no_candidates`：说明没有新的到期短期记忆；
- `memory_hits`：被纳入回顾的记忆；
- `before_status` / `after_status`；
- `lifecycle_status` 是否变化。

**讲解话术**

> 真正可用的长期记忆系统必须会遗忘。PowerMem 不是把所有上下文永久堆起来，而是让临时事实按时间衰减或删除，让长期偏好保留，并且所有生命周期变更都可审计。

---

## 5. 每个场景的能力映射速查表

| 场景 | PowerMem operation | 主要 memory kind | 核心 filters / metadata | 关键 reason codes |
|---|---|---|---|---|
| Act 1 | `ADD` | `cabin_control_preference` | `actor_id`、`seat_position`、`season`、`target_temp_c`、`seat_heat_level` | `cabin_preference_saved` |
| Act 2 | `SEARCH` | `cabin_control_preference`、`safety_policy` | `actor_id`、`seat_position`、`memory_kind in [...]` | `cabin_preference_applied`、`safety_policy_applied` |
| Act 3 | `SEARCH` | `cabin_control_preference`、`driving_preference` | `actor_id`、`seat_position`、routine query | `complete_routine`、`partial_routine` |
| Act 4 | `SEARCH` | `vehicle_capability` | `vehicle_id`、`capability_feature=rest_mode`、`unsupported_features` | `unsupported_vehicle_feature`、`vehicle_feature_supported` |
| Act 5 | `SEARCH` | `location_episode` | `visibility=masked`、`region`、`area_scope=region` | `region_navigation_confirmation`、`location_exact_fields_masked` |
| Act 6 | `SEARCH` | `media_preference`、`safety_policy` | `child_rear_left`、`rear_left`、`max_media_volume` | `child_safe_media_suggestion`、`safety_volume_cap_applied` |
| Act 7 | `SEARCH` | `relationship_event`、`location_episode` | `privacy_level=masked`、`anniversary date masked` | `relationship_suggestion`、`anniversary_date_masked` |
| Act 8 | `SEARCH` | `driving_preference`、`emotional_preference` | `drive_mode`、`soc`、`outside_temp_c` | `driving_preference`、`low_soc`、`cold_weather_caution` |
| Act 9 | `SEARCH` | `charging_preference`、`emotional_preference`、`driving_preference` | `soc`、`range_km`、`charging_strategy`、`emotional_tone` | `critical_soc`、`low_soc`、`charging_navigation_confirmed` |
| Act 10 | `get_all` + `UPDATE` / `DELETE` | `temporary_context`、`driving_preference`、`emotional_preference` | `retention_score`、`lifecycle_status`、`current_day=90` | lifecycle audit entries |

---

## 6. 演示时怎么讲 PowerMem，而不是讲“AI 聊天”

推荐讲法：

```text
这套座舱 demo 不是让大模型凭上下文猜，而是让 PowerMem 作为长期记忆层：
1. 写入结构化记忆；
2. 按 user、actor、seat、vehicle、memory_kind 做过滤检索；
3. 把命中的记忆交给应用层做安全和隐私策略判断；
4. 每次动作都返回 selected memory IDs、reason codes 和 vehicle diff；
5. 最后还能对短期记忆做生命周期治理。
```

不推荐讲法：

```text
大模型记住了用户喜欢什么。
```

更准确的说法：

```text
PowerMem 存储和检索可治理的长期记忆，应用层基于这些 memory evidence 做可解释决策。
```

---

## 7. 失败场景如何解释

| 现象 | 说明 | 应对 |
|---|---|---|
| memory hits 为空 | 当前 PowerMem 没有对应记忆，或测试数据没导入 | 导入测试数据，或先跑 Act 1 写入偏好 |
| 前端显示 live-mode 错误 | PowerMem 或后端不可用 | 看后端日志，不要继续演示编造结果 |
| Act 4 没有 selected memory ID | 车辆档案已经证明不支持，但命中记忆本身不一定标记 unsupported | 讲“车辆档案 + capability memory + policy guard”共同决策 |
| Act 5 不显示精确地址 | 这是预期行为 | 说明 privacy projection 生效 |
| Act 9 没有自动导航 | 这是预期行为 | 低电量导航属于高风险动作，需要用户确认 |
| Act 10 没有删除所有记忆 | 这是预期行为 | 长期偏好不应被删除，短期上下文才会衰减/归档/删除 |

---

## 8. 建议演示顺序和时间分配

如果只有 5 分钟：

1. Act 1：写入偏好，证明 ADD。
2. Act 2：同句不同人，证明 actor/seat scoped retrieval。
3. Act 4：能力边界，证明防幻觉和 policy guard。
4. Act 5：地点回忆，证明隐私投影。
5. Act 9：低电量主动关怀，证明 event-triggered proactive memory。
6. Act 10：生命周期，证明长期记忆治理。

如果有 15 分钟：

按 1 到 10 全部演示，并在每幕打开一次证据面板，重点展示 filters、selected memory IDs、reason codes 和 vehicle diff。

---

## 9. 一页式总结

| PowerMem 能力 | 在哪个场景证明 |
|---|---|
| 结构化长期记忆写入 | Act 1 |
| user / actor / seat 维度隔离 | Act 2 |
| 多记忆组合决策 | Act 3 |
| 能力边界和防幻觉 | Act 4 |
| 隐私投影和敏感字段脱敏 | Act 5、Act 7 |
| safety policy memory | Act 2、Act 6、Act 9 |
| 车辆状态参与记忆决策 | Act 8、Act 9 |
| 主动事件触发 | Act 9 |
| selected memory evidence | Act 2 到 Act 9 |
| lifecycle governance | Act 10 |

最终要让观众记住：

> PowerMem 让智能座舱从“会回答”升级到“会记住、会区分、会治理、会证明”。
