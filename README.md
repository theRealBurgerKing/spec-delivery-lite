# spec-delivery-lite

面向中小项目的软件变更 Skill。它将复合请求拆为可单独验收的需求，**逐条判级**，再按等级决定保留哪些文件。项目工作区的 `.spec-delivery-lite/` 记录当前进度；开发交付后必须经过单独验收，才能宣称完成或归档。

需求等级由 Agent 根据项目事实判断，`workflow.py` 校验等级记录、文件和状态转换；脚本不会替 Agent 理解自然语言需求。

## 分级与落档

| 等级 | 典型条件 | 所需文件 |
|---|---|---|
| `direct` | 单一、范围窄、可回滚，且不改变用户可见行为、公开契约、数据、安全、权限或架构 | `change.yaml` |
| `tracked` | 多步骤、bug 修复或用户可见行为变化 | `change.yaml`、`brief.md`、`tasks.md`；验收通过前补 `verification.md` |
| `high` | 数据迁移/删除、安全、权限、隐私、兼容性取舍、生产/外部写入、不可逆或高成本决策 | tracked 文件，加 `design.md` 与该需求的批准记录 |

复合请求中的每条需求使用稳定的 `R-##`，每项任务和验收条件使用 `T-##`、`AC-##`。每条需求在 `change.yaml` 记录等级、判级原因、当前阶段和关联 AC。混合等级的变更共用一个目录，文件要求取各等级的并集；高风险批准只针对相关需求和共享决策。

```text
目标项目/
└── .spec-delivery-lite/
    ├── changes/
    │   └── <change-name>/
    │       ├── change.yaml        # 唯一状态源：需求、任务、验收和批准
    │       ├── brief.md           # tracked/high：范围与背景
    │       ├── tasks.md           # tracked/high：实施步骤
    │       ├── design.md          # high：方案、取舍和回滚
    │       └── verification.md    # tracked/high 验收时：核验过程
    └── archive/
        └── YYYY-MM-DD-<change-name>/
```

`change.yaml` 是状态唯一来源。其他文件提供上下文或证据，不另存一套完成状态。项目是否将 `.spec-delivery-lite/` 纳入 Git，由项目自行决定。

## 安装与准备

把本仓库安装到 Codex Skills 目录。以下命令假定安装路径为 `$HOME/.codex/skills/spec-delivery-lite`，并且当前目录是**目标项目根目录**；安装在其他位置时修改 `SKILL_DIR`。在同一个 shell 中依次运行后面的命令。状态脚本需要 Python 3 和 PyYAML。

```bash
SKILL_DIR="$HOME/.codex/skills/spec-delivery-lite"
python3 -m pip install -r "$SKILL_DIR/requirements.txt"
```

## 从模板创建变更

以 tracked 需求为例，在目标项目根目录创建目录并复制所需模板：

```bash
CHANGE_DIR=".spec-delivery-lite/changes/add-remember-theme"
mkdir -p "$CHANGE_DIR"
cp "$SKILL_DIR/assets/templates/change.yaml" "$CHANGE_DIR/"
cp "$SKILL_DIR/assets/templates/brief.md" "$CHANGE_DIR/"
cp "$SKILL_DIR/assets/templates/tasks.md" "$CHANGE_DIR/"
```

编辑三个文件，替换全部 `<...>` 占位符。在 `change.yaml` 中逐条写入真实的 `R-##`、等级与理由、`T-##` 和可观察的 `AC-##`；再校验并查看当前进度：

```bash
python3 "$SKILL_DIR/scripts/workflow.py" validate "$CHANGE_DIR"
python3 "$SKILL_DIR/scripts/workflow.py" status "$CHANGE_DIR"
```

direct 需求只需复制 `change.yaml`，把对应需求的 `level` 改为 `direct`，将 `tasks` 设为 `[]`；其验收证据直接写入状态文件。high 需求还需复制并填写 `design.md`，在开始实施前，将用户对未决决策的批准记录到对应需求的 `approval.confirmed_by` 和 `approval.confirmed_at`。旧版 `format_version: 1` 不会自动迁移；先阅读原记录并人工拆分需求。

## 开发、验收与归档

每条需求按 `planned → implementing → ready_for_acceptance → accepting → accepted` 前进。开发者只能交付待验收；验收者重新按原定 AC 检查实际行为，并在 `verification.md` 中记录核验过程。下例在上一步的 tracked 目录中继续：

```bash
python3 "$SKILL_DIR/scripts/workflow.py" transition "$CHANGE_DIR" R-01 implementing --actor developer
python3 "$SKILL_DIR/scripts/workflow.py" task "$CHANGE_DIR" T-01 done
python3 "$SKILL_DIR/scripts/workflow.py" transition "$CHANGE_DIR" R-01 ready_for_acceptance

cp "$SKILL_DIR/assets/templates/verification.md" "$CHANGE_DIR/"
# 填写 AC-01 的实际检查、证据、环境和结果，再运行：
python3 "$SKILL_DIR/scripts/workflow.py" transition "$CHANGE_DIR" R-01 accepting --actor reviewer
python3 "$SKILL_DIR/scripts/workflow.py" acceptance "$CHANGE_DIR" AC-01 passed --evidence "测试日志或可复现场景"
python3 "$SKILL_DIR/scripts/workflow.py" transition "$CHANGE_DIR" R-01 accepted
python3 "$SKILL_DIR/scripts/workflow.py" archive "$CHANGE_DIR"
```

验收失败时，先用 `acceptance ... failed --evidence "实际失败结果"` 记录，再用 `transition ... changes_requested --reason "退回原因"` 退回开发；修复后转回 `implementing`，重新核验受影响的 AC。阻塞可用 `transition ... blocked --reason "原因"` 记录，解除时只能回到 `blocked_from`。同一人自验时，进入 `accepting` 须用 `--reason` 记录独立性限制；豁免 AC 必须提供原因和明确同意豁免的用户。

脚本仅在**所有需求 accepted、所有任务 done、验收证据齐备**后归档。它检查记录与状态门槛；测试是否真实证明行为，仍由验收者判断。

## 项目文件

- [SKILL.md](SKILL.md)：技能入口与判级规则。
- [references/artifacts.md](references/artifacts.md)：文件策略与状态机。
- [references/verification.md](references/verification.md)：开发与验收分离。
- [assets/templates/change.yaml](assets/templates/change.yaml)：状态文件模板。
- [scripts/workflow.py](scripts/workflow.py)：状态校验、更新、查询和归档。
- [方案设计.md](方案设计.md)：最初设计及取舍；v2 行为以当前技能与模板为准。
