# 架构

Smart EV Cockpit Memory 场景由 FastAPI 后端、Vite React 前端和合成场景数据组成。

后端负责：

- 加载合成车辆、对话、导航、多媒体、关系和状态事件。
- 封装真实 PowerMem SDK 边界。
- 根据 actor 和 seat context 构造 search query。
- 将返回的记忆投影后再发送给浏览器。
- 应用车辆状态 patch，并暴露 before/after diff。
- 为每次场景动作追加可回放的 trace evidence。

前端负责：

- 向后端提交 utterance。
- 只渲染后端返回的 memory hits、vehicle diffs 和 trace evidence。
- PowerMem 未连接时展示 live-mode 错误。
- 为 workshop 提供 presenter controls 和 developer evidence panels。

只有后端会连接 PowerMem。前端只接收已经投影的数据，不生成 fallback memories。
