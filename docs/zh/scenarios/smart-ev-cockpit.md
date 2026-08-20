# 智能电动车座舱记忆

Smart EV Cockpit Memory 是一个 workshop 场景，用于展示由真实 PowerContext 操作支撑的车辆助手。

场景覆盖：

- 结合人和座位的记忆检索
- 座舱偏好和驾驶例程回忆
- 不支持车辆能力的边界说明
- 脱敏地点和关系记忆
- 儿童安全媒体和 safety policy memories
- 车辆状态 diff 和主动关怀事件
- 90 天演示中的记忆生命周期状态

前端初始不显示 memory hits。Presenter 提交 utterance 后，后端搜索 PowerContext，执行隐私投影，必要时更新车辆状态，并返回一条包含 developer drawer evidence 的 trace。

workshop act 顺序见 `smart-ev-cockpit-playbook.md`。

进一步阅读：

- `smart-ev-cockpit-ten-scenarios-guide.md`：十个场景的使用方式、PowerContext 能力映射、证据字段和讲解话术。
- `smart-ev-cockpit-operation-guide.md`：环境启动、测试数据导入、界面操作和排障。
- `smart-ev-cockpit-playbook.md`：每幕的简短 presenter action 和 talk track。
