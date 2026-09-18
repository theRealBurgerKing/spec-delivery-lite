---
name: spec-delivery-lite
description: 用于规划、实施、调试、评审与验收软件变更。逐条需求分级，在项目内用文件状态机记录开发和验收进度，并按风险决定落档深度。
---

# 轻量规格交付

将变更的可恢复状态保存在目标项目的 `.spec-delivery-lite/`，以需求、任务和验收条件的稳定 ID 连接范围、实现与证据。不要依赖 OpenSpec 或 Superpowers 的 CLI。

## 路由变更

先检查项目和已有 `.spec-delivery-lite/changes/`。恢复变更时，先读取 `change.yaml` 及现有的 `brief.md`、`tasks.md`、`design.md`、`verification.md`，用 `python3 <skill目录>/scripts/workflow.py status <变更目录>` 核对已完成和待完成内容；不凭对话记忆重新开始。多个未归档变更都可能匹配时，询问用户。

将复合请求拆成能单独判断完成与否的需求 `R-##`，**逐条**按下表判级并在 `change.yaml` 写明原因。整个变更所需文件取各需求等级的并集；高风险要求只应用于触发它的需求及共享决策。新事实提高风险时升级该需求并补齐文件，不静默降低等级。

| 等级 | 适用条件 | 落档策略 |
|---|---|---|
| `direct` | 单一、范围窄、可回滚，且不影响用户可见行为、公开契约、数据、安全、权限或架构 | `change.yaml` 记录需求、状态与验收证据；不强制其他文件。 |
| `tracked` | 多步骤、bug 修复、用户可见行为变化或值得留存的行为 | 另建 `brief.md`、`tasks.md`；验收前写 `verification.md`。 |
| `high` | 数据迁移/删除、安全、权限、隐私、兼容性取舍、生产/外部写入、不可逆或高成本决策 | 在 tracked 文件外增加 `design.md`，实施相关需求前记录用户对未决决策的批准。 |

每个需求至少关联一个可观察的 `AC-##`。`change.yaml` 是需求等级、需求阶段、任务完成状态、验收结果和批准信息的唯一状态源；`brief.md` 解释范围，`tasks.md` 解释实施步骤，`verification.md` 记录独立核验过程，不能用后两者的文字替代状态转换。文件格式、状态规则和归档路径见 [artifacts.md](references/artifacts.md)。若旧变更仍为 `format_version: 1`，先读取原文件并人工拆分需求；不得自动将多个需求合成一个 `R-01`。

## 开发与验收

开发阶段为 `planned → implementing → ready_for_acceptance`。开发者只能交付待验收，不能把测试通过直接写成 `accepted`。验收阶段由验收者从原定 `AC-##` 出发，执行独立的只读核验，记录新鲜证据后依次进入 `accepting → accepted`；失败用 `changes_requested → implementing` 退回。若没有独立验收者，同一人必须另开验收轮次并记录自验限制。验收前不要按实现结果改写验收条件；若需求确实变更，先修订需求并留下原因。详见 [verification.md](references/verification.md)。

使用 `python3 <本Skill目录>/scripts/workflow.py` 的 `transition`、`task`、`acceptance`、`validate`、`status`、`archive` 命令更新与校验文件状态。阻塞时记录原因和 `blocked_from`，恢复时只回到原阶段。所有需求 `accepted`、任务完成且验收证据齐备后才能归档。脚本依赖 PyYAML；缺少依赖时可安装它，再执行状态转换。

## 按需读取

| 事件 | 读取文件 |
|---|---|
| 创建、恢复或归档变更 | [artifacts.md](references/artifacts.md) |
| 有 `high` 需求 | [brainstorming.md](references/brainstorming.md) |
| 报错、测试失败或行为异常 | [debugging.md](references/debugging.md) |
| 收到代码评审意见 | [code-review.md](references/code-review.md) |
| 准备验收、提交或宣称完成 | [verification.md](references/verification.md) |
| 考虑多 Agent 协作 | [parallel-work.md](references/parallel-work.md) |

## 执行约束

- 实施前读取当前 artifact；变更使事实或决策失效时先更新相应记录。
- 将任务写成可验证的切片，引用 `R-##` 和 `AC-##`。行为变更增加或更新聚焦测试；bug 修复优先先用测试复现。
- 任务完成后用 `task` 命令记录；任何必要检查失败都不能交付待验收。
- 评审意见须根据代码、测试和已确认需求核实，不直接作为改动指令。
- 只有证据支持的范围才能宣称完成；不能把开发自测、代码评审和需求验收混为一谈。
