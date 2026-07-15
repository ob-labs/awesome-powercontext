# 概览

awesome-powermem 是一个用场景展示 PowerMem 能力的参考项目。它展示应用如何在真实产品流程中检索、写入、投影和审计记忆。

第一个场景是 Smart EV Cockpit Memory。它模拟一个隐私安全的智能电动车座舱助手，用真实 PowerMem 操作为车控、推荐、多媒体和记忆生命周期提供个性化能力。

这个演示有三个目标：

- 展示记忆检索如何结合人物、座位、车辆和生命周期 metadata。
- 通过脱敏和前端投影，避免在 presenter view 暴露敏感事实。
- 暴露 trace evidence，让每次助手动作都可以回放和检查。

前端不会生成假的记忆命中。PowerMem 不可用时，后端返回 live-mode 错误，界面直接展示该错误。
