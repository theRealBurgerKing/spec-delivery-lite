# 变更 Artifact

工作需要持久范围、包含多个任务或将来需要恢复时，使用 Tracked 变更。根据结果生成
简短的 kebab-case 名称，例如 `add-remember-me` 或 `fix-session-expiry`。

在目标仓库创建此目录：

```text
.spec-delivery-lite/changes/<change-name>/
```

复制 `assets/templates/` 中对应的文件并替换所有占位符。默认创建 `change.yaml`、
`brief.md` 和 `tasks.md`；仅在存在实质决策时创建 `design.md`；验证完成时创建
`verification.md`。

`change.yaml` 是生命周期的权威记录，允许的状态如下：

| 状态 | 含义 | 允许的下一状态 |
|---|---|---|
| `planned` | 正在记录范围 | `approved`、`implementing`、`blocked` |
| `approved` | 必须确认的决策已获用户批准 | `implementing`、`blocked` |
| `implementing` | 正在修改代码或配置 | `blocked`、`verified` |
| `blocked` | 工作无法继续；记录 `blocked_reason` | 原工作状态 |
| `verified` | 每项验收条件都已验证或被明确豁免 | 归档 |

High-risk 工作设置 `approval.required: true`。仅在用户确认已记录的决策后设置
`approved`。验收 ID 必须保持稳定：任务和验证行必须引用它们，`change.yaml` 则记录
其 `pending`、`verified` 或 `waived` 状态。豁免必须记录原因并获得用户明确接受。

## Artifact 规则

- 将用户可见的结果写在**验收条件**中，而不是技术任务中。
- 为每项验收条件分配 `AC-##` ID，并写成可复现的场景：前置条件、动作和可观察结果。
- 将实施顺序和命令写在**任务**中，而不是 brief 中。
- 仅在备选方案、选定方法、数据/API 影响或回滚说明实质影响变更时，写入**设计**。
- 修订或实施前从磁盘重新读取 artifact；不要依赖对话记忆。
- 若实施使范围或决策失效，更新受影响的 artifact；变更重大时请求批准。

## 归档

将已完成变更移动到：

```text
.spec-delivery-lite/archive/YYYY-MM-DD-<change-name>/
```

仅从 `verified` 归档。除非用户明确接受缺口且已记录豁免，否则不得在存在未完成任务、
缺少关键验收证据或未解决的高严重性评审问题时归档。
