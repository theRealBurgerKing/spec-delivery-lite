# 变更文件与状态

在目标项目创建 `.spec-delivery-lite/changes/<change-name>/`，名称采用简短 kebab-case。每个变更先复制 `assets/templates/change.yaml` 并替换占位符；每条可独立验收的需求获得稳定 `R-##`，每个任务和验收条件分别获得 `T-##`、`AC-##`。一个复合请求可以有不同等级的需求，不把整包请求只记为一个风险值。

## 分级与落档

逐条需求记录 `level` 与 `level_reasons`。`direct` 只需 `change.yaml`；只要存在 `tracked` 或 `high` 需求，就增加 `brief.md` 和 `tasks.md`，验收通过前增加 `verification.md`；只要存在开始实施的 `high` 需求，就增加 `design.md` 并在该需求的 `approval` 字段中记录已获批准的决策。混合等级取文件要求的并集。影响共享数据或接口的决策应覆盖所有受影响需求，不能把一个高风险需求拆成多个 direct 来规避设计。

`change.yaml` 是机器可检查的唯一状态源：

- `requirements`：需求标题、等级与原因、阶段、开发者、验收者、批准、关联 AC。
- `tasks`：任务 ID、关联需求和 `pending/done`。`tasks.md` 只解释步骤，不能另存冲突的完成状态。
- `acceptance`：AC 的可观察标准、所属需求、`pending/passed/failed/waived` 与证据。`brief.md` 可展开背景，不重定义标准。
- `history`：脚本追加转换和验证事件；恢复工作时结合当前状态读取，不以历史事件覆盖当前状态。

## 每条需求的状态机

```text
planned → implementing → ready_for_acceptance → accepting → accepted
                  ↑                                ↓
                  └──────── changes_requested ─────┘
```

任一未完成状态可转入 `blocked`，记录 `blocked_from` 与原因；解除阻塞只能回到原状态。`accepted` 不回退；验收后发现新问题时创建新变更，或明确修订并重新验收。实施 `high` 需求前检查 `design.md` 和用户批准记录。交付 `ready_for_acceptance` 前检查关联任务全为 `done`；进入 `accepted` 前检查所有关联 AC 为 `passed/waived`、验收者与证据齐备，并且 tracked/high 变更有 `verification.md`。自验需记录限制，豁免需记录原因和明确接受豁免的用户。

使用 `python3 <skill目录>/scripts/workflow.py <命令> <变更目录> ...`。常用命令：

```text
status <path>
validate <path>
transition <path> R-01 implementing --actor <开发者>
task <path> T-01 done
transition <path> R-01 ready_for_acceptance
transition <path> R-01 accepting --actor <验收者>
acceptance <path> AC-01 passed --evidence <证据引用>
transition <path> R-01 accepted
archive <path>
```

验收失败时先以 `acceptance ... failed --evidence ...` 记录事实，再 `transition ... changes_requested --reason ...`；修复时转回 `implementing`。阻塞使用 `transition ... blocked --reason ...`，恢复时转到 `blocked_from`。同一人自验时，进入 `accepting` 须用 `--reason` 记录无法独立验收的限制。`waived` 须同时提供 `--reason` 和 `--waiver-approved-by`。

## 归档

脚本只允许在全部需求 `accepted`、任务 `done` 后，将目录移至 `.spec-delivery-lite/archive/YYYY-MM-DD-<change-name>/`。未经验证的缺口不得通过伪造通过证据消除；确需豁免时，先取得用户明确接受并记录原因。旧版 `format_version: 1` 不由脚本自动迁移，保留原内容并人工拆分需求后再使用新状态机。
