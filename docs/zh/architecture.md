# 架构

Smart EV Cockpit Memory 场景由 FastAPI 后端、Vite React 前端和合成场景数据组成。

后端负责：

- 加载合成车辆、对话、导航、多媒体、关系和状态事件。
- 在 FastAPI 进程生命周期内持有真实 PowerContext Builtin Runtime。
- 将每条导入数据先采集为 Source，再通过座舱 candidate pipeline flush 成带 citation 的 Memory revision。
- 使用 PowerContext FTS 检索当前 Memory head，再应用人物、座位、车辆和生命周期过滤。
- 将生命周期更新映射为不可变 revision，将删除映射为保留历史的 retire。
- 将返回的记忆投影后再发送给浏览器。
- 应用车辆状态 patch，并暴露 before/after diff。
- 为每次场景动作追加可回放的 trace evidence。

前端负责：

- 向后端提交 utterance。
- 只渲染后端返回的 memory hits、vehicle diffs 和 trace evidence。
- PowerContext 未连接时展示 live-mode 错误。
- 为 workshop 提供 presenter controls 和 developer evidence panels。

适配器通过独立 event-loop 线程，让现有同步场景服务安全调用 PowerContext 异步 Runtime。只有后端会连接 PowerContext；前端只接收已经投影的数据，不生成 fallback memories。
