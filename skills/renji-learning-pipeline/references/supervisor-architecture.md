# Supervisor 架构

学习监督脚本 (`scripts/learn_supervisor.py`)，运行于 `~/hermes-data/renji-learning/`。

## 核心循环

```
while RELAY.STATUS in (ACTIVE, RETRY):
    读 RELAY → 选段目录 → 启动 hermes -z --yolo 子进程
    → 等完成/超时 → 读 RELAY 新状态 → PASS/RETRY/PAUSE
```

## 多课程支持

通过 RELAY.md 的 `COURSE` 字段自动选择段目录：

| COURSE 含 | 段目录 |
|-----------|--------|
| 神农/本草 | segments-bencao/ |
| 伤寒 | segments-shanghan/ |
| 金匮 | segments-jingui/ |
| 其他 | segments/ |

## 兜底机制

| 机制 | 实现 |
|------|------|
| 单段超时 | 2700s (45min)，Popen.communicate(timeout=) |
| 连续失败暂停 | consecutive_fails ≥ 2 → STATUS: PAUSED |
| 主人中断 | 改 RELAY STATUS 为 PAUSED 或创建 PAUSE 文件 |
| 子进程崩溃检测 | result != 0 → 技术故障 → retry，不读 RELAY |
| 峰谷控制 | PEAK_VALLEY_ENABLED flag，当前关闭 |

## 致命 Bug 备忘

### Bug 1: bash -l -c 不可用
**症状**：exit code 127 / "command not found" / "cd: /g/hermes: No such file"
**原因**：Python subprocess 不继承 MSYS 挂载
**修复**：直接调 hermes.exe + cwd='G:/hermes'

### Bug 2: 子进程崩溃 ≠ 段通过
**症状**：hermes 崩溃 (exit != 0) → RELAY 未更新 → supervisor 读回 STATUS=ACTIVE → 误判"通过"
**修复**：先检查 run_segment() 返回值，result != 0 时直接 continue，不读 RELAY

### Bug 3: __pycache__ 缓存旧代码
修改 supervisor 后必须 `rm -rf __pycache__/`

## RELAY.md 协议

```
STATUS: ACTIVE|RETRY|PAUSED|DONE
CURRENT_SEGMENT: N
TOTAL_SEGMENTS: N
COURSE: 课程名
PASS_COUNT: N
FAIL_COUNT: N
```

## Hermes 子进程调用

```python
cmd = ["G:/hermes/venv/Scripts/hermes.exe", "-z", instruction, "--yolo"]
proc = subprocess.Popen(cmd, cwd="G:/hermes", ...)
```

## 横向打通 Supervisor 特有陷阱

### Bug 4: 截止时间不能用 hour >= N（2026-06-30 横向打通）

**症状**：supervisor 启动秒退，日志「已过 7:00 硬截止」，但当前 23:43。`HARD_DEADLINE_HOUR=7`，`datetime.now().hour` 取到 23 ≥ 7 → 误触发。

**修复**：用完整 `datetime` 对象比较：
```python
# ❌ 23 点会误触发
HARD_DEADLINE_HOUR = 7
if datetime.now().hour >= HARD_DEADLINE_HOUR: ...

# ✅ 精确日期时间
HARD_DEADLINE = datetime(2026, 7, 1, 7, 0, 0)
if datetime.now() >= HARD_DEADLINE: ...
```

### Bug 5: RELAY 索引 0-indexed vs 1-indexed 混用（2026-06-30 横向打通）

**症状**：重启后跳过第一批次。RELAY 存 `BATCH=1`（写入时 +1），读回当 0-indexed（`batches[1]`=第二批）。

**修复**：RELAY 存 0-indexed，显示时 +1：
```python
state = {'BATCH': batch_idx, ...}   # 存储 0-indexed
print(f"批次 {batch_idx+1}")         # 仅显示 +1
```

### Bug 7: Hermes 子进程 exit 0 ≠ 工作完成（2026-07-01 横向打通）

**症状**：汗证子进程只输出一个「数」字就 exit 0，supervisor 误判「通过」。checkpoint 和 Hindsight 都没产出。其余 29 个症状正常。

**原因**：hermes 子进程在某些边缘情况下（指令解析失败/API 返回异常/上下文太短）会秒退但仍返回 exit 0。

**修复**：supervisor 在子进程 exit 0 后，加一步**产出验证**：
```python
if result == 0:
    # 验证 checkpoint 确实生成
    expected = CHECKPOINT_DIR / f"lateral-{symptom_name}.md"
    if not expected.exists():
        print(f"[WARN] {symptom} exit 0 但无 checkpoint，标记 RETRY")
        result = 2  # 当作技术故障重试
```
或者更轻量：检查 checkpoint 文件修改时间是否在子进程启动之后。

**教训**：不能只信 exit code。对写文件类的子进程，必须验证产出文件存在。
