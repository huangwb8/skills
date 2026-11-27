---
entry_conditions: [bensz.revision.working]
invariants: []
transitions: []
---

# 当前冻结产物可交付

本状态只说明某份冻结交付物通过了当前 required 审查及绑定 Gate。进入证据包括源 run/visit/attempt、全部 Verifier 结果、Gate event、证据索引哈希及已落盘的 transition。控制入口会复核回执、快照和文件字节。

本阶段没有 helper 或额外机器 invariant，不能把阶段存在当作稿件仍未变化的证明。取回已批准产物时仍须重验哈希；改变后不能重用旧资格。

终态没有离开边，不代表宿主已经发送、写入正式文件或作者已经认可。需要继续编辑时按新任务建立新运行；同一任务内不得擅自更换已锁定任务根。入口外的宿主操作不在 BSK 强制范围内。
