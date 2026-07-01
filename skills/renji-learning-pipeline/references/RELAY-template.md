# 人纪学习进度 RELAY
# 小凛每次新会话启动 → 读此文件 → 知道学哪段

STATUS: ACTIVE
CURRENT_SEGMENT: 1
TOTAL_SEGMENTS: 17
COURSE: 黄帝内经
PASS_COUNT: 0
FAIL_COUNT: 0
CONSECUTIVE_FAILS: 0
LAST_UPDATE: 2026-06-30T08:30:00

# === 状态码 ===
# ACTIVE   - 学习进行中，supervisor 正常推进
# PAUSED   - 主人手动暂停（改此状态或创建 PAUSE 文件）
# RETRY    - 当前段不通过，需要回炉重学
# DONE     - 全部学完

# === 主人中断方式 ===
# 1. 把 STATUS 改成 PAUSED → supervisor 学完当前段后停止
# 2. 创建 PAUSE 文件（同目录）→ supervisor 检测到立即停止
# 3. Ctrl+C 终止 supervisor 进程

# === 兜底机制 ===
# 单段超时 45min → supervisor 自动 kill
# 连续 2 次 FAIL → 自动 PAUSED 等主人介入
# 每段树文件备份在 checkpoints/
# 每段日志备份在 logs/
