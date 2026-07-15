# 真实链路证据

Smart EV Cockpit Memory 场景只运行真实 PowerMem 模式。PowerMem 未连接时，场景动作会失败，前端显示 live mode 错误，不会生成假的记忆命中。

每次交互都可以展开查看：

- 请求 ID、接口、时间戳和延迟
- 隐私脱敏数量和脱敏后的输入
- PowerMem search query、filters、limit 和耗时
- memory ID、score、metadata 和脱敏内容
- 被采用的 memory ID 和 reason code
- 车辆命令 payload 和 before/after 状态变化
- ADD、UPDATE、ARCHIVE、DELETE 的 PowerMem 写入结果

Presenter Mode 和 Developer Evidence Mode 使用同一份后端响应。前端不生成假的 memory hits。
