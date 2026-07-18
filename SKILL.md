---
name: spec-delivery-lite
description: 用于规划、实施、调试、评审、验证或安全并行化软件变更。在 .spec-delivery-lite 中管理变更生命周期，保持范围和验收条件明确，并执行风险驱动的设计与基于证据的验证。
---

# 轻量规格交付

将本 Skill 作为软件变更的唯一入口。把变更的持久状态保存在目标项目的
`.spec-delivery-lite/` 目录中；不要依赖 OpenSpec、superpowers 或其 CLI。

## 路由请求

检查仓库及已有的 `.spec-delivery-lite/changes/` 条目。恢复变更前，先读取
`change.yaml`、`brief.md`、`tasks.md` 和已有的 `design.md`、`verification.md`。
不要猜测当前变更；存在多个匹配的未归档变更时，询问用户。

按下表分类请求：

| 分类 | 条件 | 行动 |
|---|---|---|
| Direct | 单一、范围窄、可回滚，且不影响用户可见行为、公开契约、数据、安全、权限或架构的改动 | 直接实施；宣称结果前读取 `references/verification.md`。 |
| Tracked | 有多个实施步骤、属于 bug 修复、改变用户可见行为，或行为值得留存 | 读取 `references/artifacts.md`；创建或更新变更。 |
| High-risk | 符合下方任一强制升级条件，或成功标准不明确 / 存在明显不同的方案 | 实施前读取 `references/brainstorming.md`。 |

出现数据迁移或删除、安全、权限、隐私、存在兼容性取舍的公开 API/配置格式/跨模块
契约变更、生产或外部写入、不可逆或高成本决策时，归为 High-risk。将分类和所有触发
原因记入 `change.yaml`。High-risk 工作必须先记录用户批准，才能执行不可逆操作或实施
未决决策。

## 仅在需要时加载细节

只在对应事件发生时读取下列文件：

| 事件 | 读取文件 |
|---|---|
| 创建、修订、恢复或归档变更 | `references/artifacts.md` |
| 归类为 High-risk | `references/brainstorming.md` |
| 报错、测试失败或行为不符合预期 | `references/debugging.md` |
| 收到代码评审意见 | `references/code-review.md` |
| 声称完成、提交、交接或归档 | `references/verification.md` |
| 考虑多 Agent 协作 | `references/parallel-work.md` |

## 执行 Tracked 变更

1. 由模板创建 `change.yaml`、`brief.md` 和 `tasks.md`。设置 `status: planned`，并为每项验收条件分配 `AC-##` 标识；写明目标、范围、非目标、验收条件和影响面。
2. 仅在存在实质技术决策时创建 `design.md`。实施未决的 High-risk 决策前取得用户批准；然后设置 `status: approved`。
3. 将每项任务写成可测试的垂直切片，引用一个或多个 `AC-##` 标识，并给出验证命令或手动场景。编辑代码前设置 `status: implementing`。
4. 实施前读取所有当前 artifact。将改动控制在范围内；新发现使既有事实失效时，先更新 artifact。
5. 一次实施一项任务。可自动化的行为变更应新增或更新聚焦测试；修复 bug 时优先先以测试复现。
6. 仅在任务指定的验证成功后标记任务完成。
7. 完成前使用 `references/verification.md` 创建或更新 `verification.md`。仅当所有验收条件都有新鲜证据或已获用户明确豁免时设置 `status: verified`。仅从 `verified` 归档；无法继续时设置 `blocked` 并写明原因。

## 全局约束

- 不要仅为流程而给琐碎、孤立的工作创建 change artifact。
- 不要静默扩大范围或重写已批准的决策。
- 不要叠加猜测性修复。发生错误或验证失败后，切换到调试 reference。
- 不要未经代码、测试和已批准变更核实，就把评审意见当作指令。
- 不要只因任务可拆分就派发 Agent；先检查并行工作 reference。
- 没有支持该精确结论的新鲜证据时，不要说工作已完成、已修复、已通过或已就绪。
