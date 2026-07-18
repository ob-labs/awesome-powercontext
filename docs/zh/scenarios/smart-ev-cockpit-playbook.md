# 智能电动车座舱记忆 Workshop 演示手册

## Act 1: 建立记忆
Presenter action: 点击 Act 1，或发送“我冬天上车一般 26C，座椅加热 2 档。”
PowerMem evidence: 出现 ADD 操作，`memory_kind=cabin_control_preference`。
Vehicle evidence: 本幕不需要车辆状态变化。
Privacy evidence: 原始说法不会作为长期记忆原文保存。
Talk track: PowerMem 保存的是抽取后的偏好记忆，不是聊天原文库。
Developer note: 查看 `actor_id`、`seat_position`、`source_event_ids`。

## Act 2: 同一句话，不同人
Presenter action: 分别用主驾、前排乘客、后排儿童发送“有点冷。”
PowerMem evidence: SEARCH filters 包含 actor 和 seat position。
Vehicle evidence: 主驾、前排乘客、儿童得到不同的安全车控 patch。
Privacy evidence: 儿童声纹会命中 safety policy memory。
Talk track: 同一句话需要结合人、座位和安全边界理解。
Developer note: 对比 evidence drawer 中的 selected memory IDs。

## Act 3: 组合车控例程
Presenter action: 发送“按我上次舒服的设置来。”
PowerMem evidence: SEARCH 返回 `cabin_control_preference` 和 `driving_preference`。
Vehicle evidence: HVAC 和 seat heat 字段出现 before/after diff。
Privacy evidence: 车控历史被总结成例程，不保存原始对话。
Talk track: 高频动作可以沉淀成可复用的程序记忆。
Developer note: 查看 `vehicle_action.patch` 和 selected memory IDs。

## Act 4: 车辆能力边界
Presenter action: 发送“这台车支持小憩模式吗？”
PowerMem evidence: SEARCH 返回 `vehicle_capability` 和 unsupported feature metadata。
Vehicle evidence: 不执行车辆命令。
Privacy evidence: 回复只基于合成车辆档案。
Talk track: 记忆检索可以避免助手编造车辆能力。
Developer note: 查看 `memory_kind=vehicle_capability` filter。

## Act 5: 地点回忆
Presenter action: 发送“带我去上周五那家餐厅。”
PowerMem evidence: SEARCH 返回泛化后的 `location_episode`。
Vehicle evidence: 出现导航推荐，但不展示精确地址。
Privacy evidence: 精确地址和原始地点名称保持隐藏。
Talk track: 有用的地点回忆不需要暴露私人地址。
Developer note: 查看 `visibility=masked` 和 hidden field reason。

## Act 6: 多媒体偏好
Presenter action: 发送“放点适合孩子睡觉的内容。”
PowerMem evidence: SEARCH 返回 `media_preference` 和 `safety_policy`。
Vehicle evidence: 推荐低音量、儿童安全的媒体内容。
Privacy evidence: 儿童身份只表示为 `child_rear_left`。
Talk track: PowerMem 能把乘员上下文和媒体历史结合起来。
Developer note: 对比儿童和主驾的 actor filters。

## Act 7: 纪念日推荐
Presenter action: 发送“今晚有什么安排建议？”
PowerMem evidence: SEARCH 返回 `relationship_event` 和安全地点偏好。
Vehicle evidence: 展示推荐卡片，不直接执行路线。
Privacy evidence: presenter view 中不展示完整纪念日日期。
Talk track: 个性化推荐可以有帮助，同时不暴露敏感事实。
Developer note: 查看 evidence drawer 中的 masked metadata。

## Act 8: 驾驶模式建议
Presenter action: 触发雨天通勤或低电量上下文。
PowerMem evidence: SEARCH 返回 `driving_preference` 和 `emotional_preference`。
Vehicle evidence: 驾驶模式推荐结合 SOC 上下文出现。
Privacy evidence: 通勤路线保持区域级泛化。
Talk track: 车辆状态和长期记忆一起决定场景化建议。
Developer note: 查看 vehicle state diff 和 reason codes。

## Act 9: 主动关怀
Presenter action: 通过 `POST /events/vehicle` 触发低电量。
PowerMem evidence: SEARCH 返回充电提醒表达偏好。
Vehicle evidence: SOC 和 range 字段从正常变为低电量。
Privacy evidence: 情感偏好以摘要形式使用，不展示原始抱怨。
Talk track: 主动关怀需要个性化语气，避免打扰。
Developer note: 查看被选中的 `emotional_preference` memory ID。

## Act 10: 生命周期与隐私
Presenter action: 跳转到 Day 90。
PowerMem evidence: 首次运行时，过期 `temporary_context` 返回 `DELETE: deleted (ok)`；重复运行时返回 `REVIEW: unchanged (no_candidates)`。
Vehicle evidence: 本幕不需要直接车辆命令。
Privacy evidence: archive 和 delete 行为仍可追溯。
Talk track: 生命周期管理让记忆持续有用，而不是堆积过期事实。
Developer note: 查看 retention score、hit count 和 lifecycle status 变化。
