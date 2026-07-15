# 隐私

这个场景使用三层隐私处理。

输入脱敏会在 evidence 组装前移除或标记敏感用户文本。后端暴露 redaction count 和 redacted input，方便评审者检查被移除的内容。

记忆投影决定浏览器能收到什么。敏感内容会被替换为 masked content，删除记录以 tombstone 表示，隐藏字段会被明确列出。

Trace evidence 用于回放，但不暴露原始私密事实。它包含 request context、PowerMem query details、selected memory IDs、reason codes、vehicle diffs 和 write results。

场景数据是合成数据。即便如此，架构仍按真实用户数据处理，以便用于产品评审。
