#!/usr/bin/env python3
"""
人纪学习监督脚本 —— learn_supervisor.py

功能：
- 读 RELAY.md → 循环启动 hermes 子进程 → 每段学完自动接力
- 超时自动杀死 (45min/段)
- 连续 2 次失败 → 自动暂停，等主人介入
- 主人中断：改 RELAY STATUS 或创建 PAUSE 文件

用法：
  python learn_supervisor.py
"""

import os, sys, time, signal, subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("~/hermes-data/renji-learning")
RELAY_PATH = BASE_DIR / "RELAY.md"
PAUSE_FILE = BASE_DIR / "PAUSE"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
LOG_DIR = BASE_DIR / "logs"
SEGMENT_DIR = BASE_DIR / "segments"

TIMEOUT_PER_SEGMENT = 2700
SLEEP_BETWEEN = 5
MAX_CONSECUTIVE_FAILS = 2
PEAK_VALLEY_ENABLED = False

def build_hermes_cmd(segment_num: int, course: str):
    instruction = (
        f"加载 renji-learning-pipeline skill。"
        f"然后学习 {course} 第{segment_num}段。"
        f"段文件在 ~/hermes-data/renji-learning/segments/。"
        f"RELAY 在 ~/hermes-data/renji-learning/RELAY.md。"
        f"按 skill 流程执行全部步骤：读段文件→建树→子agent出题→闭卷自测→立刻写Hindsight并上传→更新RELAY。"
        f"注意：如果RELAY的STATUS是RETRY，需要重新学习同一段。"
        f"学完一段后不要继续下一段——退出即可。"
    )
    return (
        ["G:/hermes/venv/Scripts/hermes.exe", "-z", instruction, "--yolo"],
        "G:/hermes"
    )

def read_relay():
    if not RELAY_PATH.exists():
        return {"STATUS": "INIT", "CURRENT_SEGMENT": 1, "FAIL_COUNT": 0}
    state = {}
    with open(RELAY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, _, val = line.partition(':')
                key = key.strip(); val = val.strip()
                if key in ('CURRENT_SEGMENT', 'TOTAL_SEGMENTS', 'PASS_COUNT', 'FAIL_COUNT'):
                    try: state[key] = int(val)
                    except ValueError: state[key] = val
                else: state[key] = val
    return state

def write_relay(state):
    content = f"""# 人纪学习进度 RELAY
# 自动更新于 {datetime.now().isoformat()}

STATUS: {state.get('STATUS', 'ACTIVE')}
CURRENT_SEGMENT: {state.get('CURRENT_SEGMENT', 1)}
TOTAL_SEGMENTS: {state.get('TOTAL_SEGMENTS', 17)}
COURSE: {state.get('COURSE', '黄帝内经')}
PASS_COUNT: {state.get('PASS_COUNT', 0)}
FAIL_COUNT: {state.get('FAIL_COUNT', 0)}
CONSECUTIVE_FAILS: {state.get('CONSECUTIVE_FAILS', 0)}
LAST_UPDATE: {datetime.now().isoformat()}
"""
    with open(RELAY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def check_pause():
    if PAUSE_FILE.exists():
        print(f"[{datetime.now():%H:%M:%S}] ⏸️  检测到 PAUSE 文件，暂停")
        return True
    state = read_relay()
    if state.get('STATUS') == 'PAUSED':
        print(f"[{datetime.now():%H:%M:%S}] ⏸️  RELAY STATUS=PAUSED，暂停")
        return True
    return False

def run_segment(segment_num: int, course: str) -> int:
    cmd, cwd = build_hermes_cmd(segment_num, course)
    print(f"[{datetime.now():%H:%M:%S}] 🚀 启动段 {segment_num}/{read_relay().get('TOTAL_SEGMENTS', 17)}")
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace')
        try:
            stdout, _ = proc.communicate(timeout=TIMEOUT_PER_SEGMENT)
            exit_code = proc.returncode
            log_file = LOG_DIR / f"segment-{segment_num:02d}-{datetime.now():%Y%m%d-%H%M%S}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(stdout or "(no output)")
            if exit_code == 0:
                print(f"[{datetime.now():%H:%M:%S}] ✅ 段 {segment_num} 完成")
            else:
                print(f"[{datetime.now():%H:%M:%S}] ⚠️  段 {segment_num} 异常退出 (exit={exit_code})")
            return 0 if exit_code == 0 else 2
        except subprocess.TimeoutExpired:
            print(f"[{datetime.now():%H:%M:%S}] ⏰ 段 {segment_num} 超时，强制终止")
            proc.kill()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.terminate()
            return 1
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] 💥 段 {segment_num} 启动失败: {e}")
        return 2

def main():
    print("=" * 50)
    print("  人纪学习监督脚本 v1.0")
    print(f"  启动时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 50)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    consecutive_fails = 0
    while True:
        if check_pause():
            print(f"[{datetime.now():%H:%M:%S}] 🛑 已暂停，退出")
            break
        state = read_relay()
        status = state.get('STATUS', 'ACTIVE')
        if status == 'DONE':
            print(f"[{datetime.now():%H:%M:%S}] 🎉 全部学完！")
            break
        if status not in ('ACTIVE', 'RETRY'):
            print(f"[{datetime.now():%H:%M:%S}] ❓ 未知状态: {status}，退出")
            break
        if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
            print(f"[{datetime.now():%H:%M:%S}] 🚨 连续失败 {consecutive_fails} 次，自动暂停")
            state['STATUS'] = 'PAUSED'
            state['CONSECUTIVE_FAILS'] = consecutive_fails
            write_relay(state)
            break
        segment_num = state.get('CURRENT_SEGMENT', 1)
        total = state.get('TOTAL_SEGMENTS', 17)
        course = state.get('COURSE', '黄帝内经')
        seg_files = sorted(SEGMENT_DIR.glob(f"{segment_num:02d}-*"))
        if not seg_files:
            print(f"[{datetime.now():%H:%M:%S}] ❌ 段 {segment_num} 文件不存在")
            break
        print(f"\n{'='*40}")
        print(f"[{datetime.now():%H:%M:%S}] 📖 段 {segment_num}/{total}: {seg_files[0].name}")
        print(f"{'='*40}")
        result = run_segment(segment_num, course)
        if result != 0:
            consecutive_fails += 1
            print(f"[{datetime.now():%H:%M:%S}] 🔴 段 {segment_num} 技术故障 (result={result})，连续失败: {consecutive_fails}")
            continue
        time.sleep(SLEEP_BETWEEN)
        new_state = read_relay()
        new_status = new_state.get('STATUS', '')
        if new_status == 'RETRY':
            consecutive_fails += 1
            print(f"[{datetime.now():%H:%M:%S}] 🔄 段 {segment_num} 不通过，回炉")
            new_state['CONSECUTIVE_FAILS'] = consecutive_fails
            write_relay(new_state)
        elif new_status == 'PAUSED':
            consecutive_fails += 1
            print(f"[{datetime.now():%H:%M:%S}] ⚠️  段 {segment_num} 触发暂停")
            break
        elif new_status == 'DONE':
            print(f"[{datetime.now():%H:%M:%S}] 🎉 课程完成！")
            break
        else:
            consecutive_fails = 0
            print(f"[{datetime.now():%H:%M:%S}] ✅ 段 {segment_num} 通过 → 下一段")
        time.sleep(SLEEP_BETWEEN)
    print(f"\n[{datetime.now():%H:%M:%S}] 监督脚本退出")

def signal_handler(sig, frame):
    print(f"\n[{datetime.now():%H:%M:%S}] ⚡ 收到信号 {sig}，退出")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    main()
