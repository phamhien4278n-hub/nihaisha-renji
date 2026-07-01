---
name: renji-learning-pipeline
description: 人纪课程自动化学习流水线。Phase 1 纵向——每段独立学习（读原文→建树→子agent出题→闭卷自测→Hindsight→RELAY）；Phase 2 横向——逐症状打通五门课（搜索引+Hindsight→制鉴别诊断表→checkpoint→Hindsight→RELAY）。与 learn_supervisor.py / lateral_supervisor.py 配合，实现上下文零腐烂的自动接力。已覆盖黄帝内经、神农本草经、伤寒论、金匮要略四门课 + 30 症状横向打通。\ntriggers:\n  - 学习黄帝内经\n  - 学习伤寒论\n  - 学习金匮要略\n  - 学习神农本草经\n  - 人纪学习\n  - renji 学习\n  - 横向打通\n  - 症状鉴别\n  - 症状横向
---

# renji-learning-pipeline

人纪课程自动化学习流水线。每段独立学习——读原文→建树→子agent出题→闭卷自测→立刻上传Hindsight→更新RELAY→退出。与 supervisor 脚本配合，实现上下文零腐烂的自动接力学习。

## 核心原则

1. **一段一上下文**：每段学完立即退出，下段新会话白板启动
2. **子agent出题，自己诚实作答**：不需要子agent评分——诚实闭卷自测即通过
3. **学完立刻上传 Hindsight**：不等全段结束，防止中途出错白干
4. **本地 checkpoint + 云端 Hindsight 双保险**：树文件存本地，知识条目存云端

## 学习流水线（每段执行）

### Step 0: 启动
1. 读 `~/hermes-data/renji-learning/RELAY.md`
2. 获取 `CURRENT_SEGMENT` 和 `STATUS`
3. 若 STATUS 不是 ACTIVE 或 RETRY → 退出
4. 加载对应段文件：`~/hermes-data/renji-learning/segments/XX-*.txt`

### Step 1: 读原文 + 建树（~15min）
1. **逐字读原文**，不跳、不扫
2. 建结构化知识树——**格式取决于课程类型**：
   
   **内经/伤寒/金匮（理论型）**：
   ```
   ### 段X：[篇章名]
   #### 核心概念 / 病机推理链 / 关键治则 / 新学到的东西
   ```
   
   **神农本草经（药理+临床型）**：
   ```
   ### 段X：药物清单
   #### 本段药物速查表
   | 药名 | 性味 | 主治 | 倪师关键用法 |
   |------|------|------|-------------|
   #### 倪师案例（本段涉及的倪案）
   - [案例名]: [病人故事+用药思路+教训]
   #### 倪师辨证思路（本段涉及的倪辨/倪诀/倪联/倪问）
   - [思路类型]: [倪师原话或转述]
   #### 跨课连接
   - 本段药物出现在哪些伤寒/金匮方中
   ```
   
3. 写入 `~/hermes-data/renji-learning/checkpoints/tree-segment-XX.md`
4. **神农本草经特有**：对照 nishizhu 文件——`~/hermes-data/backups/renji-2026-06-09/skills/learning/knowledge-schema-learning/references/nishizhu/shennong-bencao/nishizhu_bencao.json`
   - 找本段涉及的药物在 nishizhu 中是否有**倪案/倪辨/倪诀/倪联/倪问**
   - 有 → 逐条读入树中（**这是主人强调的核心——倪师治病思路和案例比药理本身更重要**）

### Step 2: 子agent出题（delegate_task）
context = 当前段的知识节点（药物性味+倪案+倪师思路）
goal = 生成5道应用题。**神农本草经模式**：题目必须包含至少2道案例分析题（给出一个病人症状，要求选择药物/鉴别药物/给出用药思路）。

### Step 3: 闭卷自测（简化——诚实作答即通过）
1. 不看原文、不看树、不看 Hindsight——纯闭卷
2. 逐题作答
3. **不需要子agent评分**——诚实回答，明显答不上来的（完全空白/答非所问）标记为不通过
4. 全部答出 → 通过

### Step 4: 写 Hindsight + 立刻上传（防止中途出错丢失）
1. **先在脑中 Erase 原文**（执行反注意力陷阱五问）
2. 凭记忆写 Hindsight：学到了什么、跨课连接、薄弱点
3. **立刻用 `hindsight_retain` 上传**到云端，标签：`renji,huangdi-neijing,segment-XX`
4. 同时确保 checkpoint 树文件已写入本地
5. 本地 + 云端双保险——即使 supervisor 崩了，记忆不丢

### Step 5: 更新 RELAY + 退出
- 自测通过 → `STATUS: ACTIVE`, `CURRENT_SEGMENT += 1`, `PASS_COUNT += 1`
- 自测不通过 → `STATUS: RETRY`（段号不变，FAIL_COUNT += 1）
- 连续 2 次 FAIL → `STATUS: PAUSED`（等主人介入）
- 学完最后一段 → `STATUS: DONE`

**重要：退出前必须执行 `session_search` 确保本段学习成果可追溯。**

## 兜底与安全

| 机制 | 实现 |
|------|------|
| 单段超时 | supervisor 的 `timeout` 参数（45分钟） |
| 连续失败暂停 | FAIL_COUNT ≥ 2 → STATUS: PAUSED |
| 主人中断 | 改 RELAY STATUS 或创建 PAUSE 文件 |
| 回滚 | checkpoints/ 保留每段的树文件 |
| 上下文腐烂 | 每段独立会话，学完退出，永不积累 |
| 记忆丢失 | 每段学完立刻上传 Hindsight + 本地 checkpoint 双保险 |

### 调试陷阱

**致命 Bug：子进程退出码不能替代 RELAY 状态检查**

当 hermes 子进程异常退出（exit code != 0）时，RELAY 不会被更新。如果 supervisor 只读 RELAY 判断状态，会看到 STATUS 仍是 ACTIVE → 误判为"段通过"→ 进入无限崩溃循环。

正确做法：先检查 `run_segment()` 返回值——`result != 0` 直接标记技术故障并 retry，**不要读 RELAY**。RELAY 只在子进程正常退出（exit code 0）后才可信。

**hermes.exe 调用注意事项**

Windows 上 `subprocess.Popen` 调用 hermes 时，不能用 `bash -l -c 'cd ~/hermes && hermes ...'`（Python 子进程无法访问 MSYS 的 `/g` 挂载点）。直接用 `hermes.exe` 二进制 + `cwd` 参数：`Popen(['~/hermes/venv/Scripts/hermes.exe', '-z', instruction, '--yolo'], cwd='G:/hermes')`。**不要走 bash 中转。**

### 陷阱3：Supervisor 静默崩溃（2026-07-01 金匮实战）

**症状**：RELAY 长时间不变（如一直显示 31/38），checkpoints 目录有更高的段文件（如 segment-33），但 supervisor 进程已消失（`ps aux | grep learn_supervisor` 无结果）。

**原因**：supervisor 的 Python 进程本身崩了——可能是子进程异常退出后 supervisor 的异常处理没有覆盖某种边缘情况，导致整个 supervisor 退出而非进入 retry 逻辑。

**修复步骤**：
1. 检查 checkpoint 目录最高段号：`ls ~/hermes-data/renji-learning/checkpoints/ | sort -V | tail -5`
2. 手动修正 RELAY.md：将 CURRENT_SEGMENT 设为最高 checkpoint 段号+1，PASS_COUNT 同步
3. 清缓存 + 重启：`rm -rf ~/hermes-data/renji-learning/__pycache__/ && python learn_supervisor.py`
4. 用 `terminal(background=true, notify_on_complete=true)` 启动

**预防**：supervisor 代码需增加全局 try/except 包裹主循环，确保任何未捕获异常不会导致静默退出。

### 陷阱4：Hermes 去重保护拦截 RELAY 读取（2026-07-01 金匮实战）

**症状**：多次 `read_file(RELAY.md)` 后返回 `"BLOCKED: You have read this exact file region 4 times in a row. The content has NOT changed."`，无法确认最新状态。

**原因**：Hermes 内置去重保护——同一个文件同一区域连续读 4 次未变化会自动拦截。这是正常的防 token 浪费机制，不是 bug。

**处理**：被拦截说明文件确实没变化。如果怀疑 supervisor 挂了（几分钟过去了应该有变化但没有），不要反复读 RELAY，改用以下方式诊断：
- `ps aux | grep learn_supervisor` 检查进程是否存活
- `ls -lt ~/hermes-data/renji-learning/checkpoints/ | head -5` 看最新 checkpoint 时间戳

### 陷阱5：Supervisor 重启后段重复执行（2026-07-01 金匮实战）

**症状**：supervisor 重启后，同一段被执行了两次（如段32跑了两次）。

**原因**：第一个 supervisor 崩溃时，某段的 checkpoint 已写入但 RELAY 未更新为 PASS → 重启后 RELAY 仍指向该段 → hermes 子进程重新学习 → 生成第二个同段 checkpoint。checkpoint 目录出现两个不同命名的同段文件。

**影响**：学习质量不受影响（每段独立上下文，重复学习只是多耗一次 API token），但 Hindsight 可能存两条相似记忆。

**处理**：不需要特殊修复——重复段不影响最终完整性。关注点应该是 supervisor 的稳定性，不是去除重复。如果 token 预算敏感，可以在全部完成后手动清理重复的 Hindsight 记忆。

- **Supervisor 脚本**：`learn_supervisor.py` 位于 `~/hermes-data/renji-learning/`
- **RELAY**：`~/hermes-data/renji-learning/RELAY.md`
- **段文件**：
  - 黄帝内经等：`~/hermes-data/renji-learning/segments/`
  - 神农本草经：`~/hermes-data/renji-learning/segments-bencao/`（supervisor 根据 RELAY COURSE 自动选择）
- **nishizhu 注释**（神农本草经专用）：
  - **段文件位置（supervisor 根据 RELAY COURSE 自动选择）**：
    - 黄帝内经：`~/hermes-data/renji-learning/segments/`
    - 神农本草经：`~/hermes-data/renji-learning/segments-bencao/`
    - 伤寒论：`~/hermes-data/renji-learning/segments-shanghan/`
    - 金匮要略：`~/hermes-data/renji-learning/segments-jingui/`
  - **nishizhu 注释**：
    - 神农本草经：`~/hermes-data/backups/renji-2026-06-09/.../nishizhu/shennong-bencao/nishizhu_bencao.json`（112条：27倪案+13倪辨+30倪诀+30倪联+12倪问）
    - 伤寒论：`~/hermes-data/backups/renji-2026-06-09/.../nishizhu/shanghan-lun/nishizhu_shanghan.json`（34KB）
    - 金匮要略：暂无 nishizhu 文件
  - **课程规模参考**（便于预估时间）：
    | 课程 | 行数 | 段数 | 实测耗时 |
    |------|------|------|---------|
    | 黄帝内经 | 954 | 17 | 58min |
    | 神农本草经 | 1483 | 25 | 2h30min |
    | 伤寒论 | 1025 | 17 | 1h15min |
    | 金匮要略 | 2286 | 38 | ~3-4h* |
- **Supervisor 架构** → `references/supervisor-architecture.md`
- **神农本草经数据指南** → `references/shennong-bencao-data.md`
- **Supervisor 脚本**：`~/hermes-data/renji-learning/learn_supervisor.py`（实际运行位置；skill 目录 `scripts/` 下有一份副本作参考）——管理 hermes 子进程循环，实现自动接力
- **段文件拆分**：首次使用时需将课程原文拆分为段文件（按 segmentation.md 方案）

## Supervisor 陷阱（关键！）

### 陷阱1：不能通过 bash -l -c 调 hermes
**症状**：`/bin/bash: hermes: command not found` 或 `cd: ~/hermes: No such file or directory`
**原因**：Python subprocess 不继承 MSYS 驱动挂载。`bash -l` 里的 `cd ~/hermes` 找不到路径，`hermes` 是 bash 函数不是二进制。
**正确做法**：
```python
# ✅ 直接调 hermes.exe + cwd 参数
cmd = ["~/hermes/venv/Scripts/hermes.exe", "-z", instruction, "--yolo"]
subprocess.Popen(cmd, cwd="~/hermes", ...)

# ❌ 不要走 bash -l -c
subprocess.Popen(["bash", "-l", "-c", "cd ~/hermes && hermes -z ..."])
```

### 陷阱2：子进程崩溃 ≠ 段通过
**症状**：hermes 崩溃 (exit code != 0) → RELAY 未被更新 → supervisor 读回 STATUS 仍是 ACTIVE → 错误认为"段通过" → 无限循环
**正确做法**：先检查 `run_segment()` 返回值，result != 0 是技术故障，不应读 RELAY：
```python
result = run_segment(segment_num, course)
if result != 0:
    # 技术故障，RELAY 未更新，不能盲信
    consecutive_fails += 1
    continue
# 只有 result == 0 时才读 RELAY
new_state = read_relay()
```

### 陷阱3：__pycache__ 缓存旧代码
修改 supervisor 后必须清 `__pycache__/`，否则 Python 可能加载缓存的 .pyc 旧版本。

### 陷阱4：Supervisor 静默崩溃 + RELAY/checkpoint 不匹配（2026-07-01 金匮实测）
**症状**：
- 询问进度时 RELAY 连续多次读取不变（如始终显示 CURRENT_SEGMENT: 32, PASS_COUNT: 31）
- `ps aux | grep learn_supervisor` 返回空——supervisor 进程已消失
- 但 `checkpoints/` 目录下存在比 RELAY 记录更高段号的知识树文件

**原因**：supervisor 子进程（hermes）可能在完成某段后、更新 RELAY 前异常退出（exit code != 0），supervisor 自身也未正确处理此情况而崩溃。checkpoint 是在 Step 1 写入的（早于 RELAY 更新），所以 checkpoint 比 RELAY 领先。

**恢复步骤**：
1. `ps aux | grep learn_supervisor` — 确认进程已死
2. `ls ~/hermes-data/renji-learning/checkpoints/ | grep jingui` — 找最高段号的 checkpoint
3. 手动修正 RELAY：`CURRENT_SEGMENT = 最高checkpoint段号 + 1`，`PASS_COUNT = 最高checkpoint段号`
4. `rm -rf ~/hermes-data/renji-learning/__pycache__/`
5. 重新启动 supervisor

**预防**：supervisor 应在每个子进程结束后立即检查 checkpoints/ 目录与 RELAY 的一致性，若发现 checkpoint 领先 RELAY 则自动修正（而非盲信 RELAY）。此功能尚未实现，当前需人工介入。

## 启动方式

```bash
# 1. 初始化 RELAY（仅首次）
echo "STATUS: ACTIVE
CURRENT_SEGMENT: 1
TOTAL_SEGMENTS: 17
COURSE: 黄帝内经
PASS_COUNT: 0
FAIL_COUNT: 0" > ~/hermes-data/renji-learning/RELAY.md

# 2. 清缓存 + 启动
rm -rf ~/hermes-data/renji-learning/__pycache__/
~/hermes/venv/Scripts/python.exe ~/hermes-data/renji-learning/learn_supervisor.py
```
- Supervisor 脚本：实际运行位置为 `~/hermes-data/renji-learning/learn_supervisor.py`。skill 目录 `scripts/` 下的副本仅作参考——启动时必须用 renji-learning 根目录下的版本（RELAY 和 checkpoints 均与该脚本同目录）

## Phase 2：横向打通——以症状为纲（2026-07-01 凌晨完成，30/30 ✅）

**背景**：第一遍纵向按课程学完五门（针灸✅ 内经✅ 神农✅ 伤寒✅ 金匮✅），但倪师讲课的精髓之一是"以症为纲"——如"头痛一共有几种情况：第一种……第二种……"——这种横向诊断思维在纵向学习中分散在不同课程段落里，未系统整理。

**目标**：制作"倪师症状鉴别诊断总表"——每个症状下汇总五门课中的全部分型、辨证要点、方剂、针灸、出处、C1/C2标注。

**最终结果**：30/30 全部完成，0 失败，总耗时约 1h46min（23:43→01:29）。

| 步骤 | 内容 | 状态 | 产出 |
|------|------|------|------|
| 1. 原文提取 | `scan_symptoms.py` 扫描所有 segments + checkpoints | ✅ 完成 | `symptom-classification-index.md`（562段匹配，1.4MB） |
| 2. 症状聚类 | 从 562 段中按关键词频率聚类 30 症状 → 分 4 批 | ✅ 完成 | `lateral_symptoms.json`（30症状 × 4批次） |
| 3. 横向打通 | `lateral_supervisor.py` 逐症状启动 hermes 子进程 | ✅ 30/30 完成 | 30 个 checkpoints/lateral-*.md（6-16KB）+ Hindsight |

**minor incident**：汗证子进程 exit 0 但实际只输出「数」字就秒退，checkpoint 未生成。supervisor 被 exit code 欺骗（见 Bug 7）。已在同会话手动补写 checkpoint，30/30 完整。

### 横向打通架构

与纵向学习的 `learn_supervisor.py` 同模式，但子进程任务不同：

| 维度 | 纵向学习 | 横向打通 |
|------|---------|---------|
| Supervisor | `learn_supervisor.py` | `lateral_supervisor.py` |
| RELAY | `RELAY.md`（段号驱动） | `RELAY-LATERAL.md`（批次+症状索引驱动） |
| 子进程任务 | 读段文件→建树→自测 | 搜索引+Hindsight→五门课打通→制表 |
| Checkpoint | `tree-segment-XX.md` | `lateral-{symptom}.md` |
| 每单元耗时 | ~10-15min | ~10-15min |

**30 个症状分 4 批**（从 562 段匹配中按关键词频率聚类）：

| 批次 | 症状数 | 症状 |
|------|--------|------|
| 第1批 | 8 | 呕吐、咳嗽、小便、口渴、便秘、汗证、水肿、下利 |
| 第2批 | 8 | 腹痛、妇人、痹证、发热、头痛、出血、情志、黄疸 |
| 第3批 | 8 | 胸痹心痛、失眠、恶寒、痉病、疟疾、虚劳、眩晕、外科 |
| 第4批 | 6 | 饮食、奔豚、积聚、咽喉、百合、心悸 |

**子进程 Hermes 指令模板**：每个症状独立会话，指令包含：
1. 从 `symptom-classification-index.md` 搜索该症状相关段落（search_files）
2. 从 Hindsight 搜索相关记忆（hindsight_recall）
3. 横向打通五门课：伤寒（六经辨证）→ 金匮（杂病辨证）→ 内经（病机理论）→ 针灸（治法穴位）→ 神农（相关药物）
4. 输出鉴别诊断表（分型/病机/辨证要点/方剂/针灸/关键药物/出处标注C1或C2）
5. 写 checkpoint + hindsight_retain + 更新 RELAY-LATERAL

**硬截止**：`lateral_supervisor.py` 内置截止时间 `datetime(2026, 7, 1, 7, 0, 0)`，到期自动暂停（⚠️ 不能用 `hour >= 7`——23 点会误触发，见 supervisor-architecture.md Bug 4）。

**启动**：
```bash
# Step 1: 生成症状聚类（已完成，不需要重跑）
# Step 2: 初始化横向打通 RELAY
echo "STATUS: ACTIVE
BATCH: 0
SYMPTOM_INDEX: 0
TOTAL_SYMPTOMS: 30
PASS_COUNT: 0
FAIL_COUNT: 0" > ~/hermes-data/renji-learning/RELAY-LATERAL.md

# Step 3: 启动 supervisor（后台）
~/hermes/venv/Scripts/python.exe ~/hermes-data/renji-learning/lateral_supervisor.py
```

**进度恢复**：supervisor 自动从 RELAY-LATERAL.md 的 BATCH + SYMPTOM_INDEX 恢复，重启即续跑。

## 参考文献

- `references/clinical-reasoning-order.md` — **临床回答顺序铁律**：先内经→再顺序→再针方，不跳步骤
- `scripts/learn_supervisor.py` — 学习监督脚本（循环启动 hermes 子进程 + 兜底机制）
- `scripts/scan_symptoms.py` — 症状分型原文提取脚本（Phase 2 第一步：扫描所有 segments + checkpoints 输出症状分型原文索引）
- `scripts/lateral_supervisor.py` — 横向打通监督脚本（逐症状启动 hermes 子进程，五门课横向打通制表）
- `references/hermes-subprocess-pitfalls.md` — hermes 子进程调试踩坑（cwd + MSYS 挂载 + bash 函数陷阱）
- `references/tcm-product-compliance.md` — **AI中医产品监管合规与商业化参考**：三分法监管框架、核心红线、GitHub六种变现路径、安全定位
