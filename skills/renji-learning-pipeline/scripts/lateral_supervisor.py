#!/usr/bin/env python3
"""
横向打通监督脚本 —— lateral_supervisor.py v1.1

与 learn_supervisor.py 同架构，但用于 Phase 2 横向打通。
逐症状启动 hermes 子进程，每个症状独立上下文，五门课横向打通制表。

关键文件：
- RELAY: ~/hermes-data/renji-learning/RELAY-LATERAL.md（0-indexed BATCH/SYMPTOM_INDEX）
- 症状列表: ~/hermes-data/renji-learning/lateral_symptoms.json
- 索引文件: ~/hermes-data/renji-learning/symptom-classification-index.md
- Checkpoints: ~/hermes-data/renji-learning/checkpoints/lateral-*.md

硬截止：datetime(2026, 7, 1, 7, 0, 0)，到期自动暂停。
注意：不能用 hour >= 7——23 点会误触发（Bug 4）。

用法：python lateral_supervisor.py
"""

import os, sys, time, json, signal, subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# 配置
# ============================================================
BASE_DIR = Path("~/hermes-data/renji-learning")
RELAY_PATH = BASE_DIR / "RELAY-LATERAL.md"
PAUSE_FILE = BASE_DIR / "PAUSE-LATERAL"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
LOG_DIR = BASE_DIR / "logs"
INDEX_PATH = BASE_DIR / "symptom-classification-index.md"
SYMPTOM_LIST_PATH = BASE_DIR / "lateral_symptoms.json"

TIMEOUT_PER_SYMPTOM = 2700  # 45 分钟
SLEEP_BETWEEN = 5
MAX_CONSECUTIVE_FAILS = 2
HARD_DEADLINE = datetime(2026, 7, 1, 7, 0, 0)  # ⚠️ 必须用完整 datetime，不能用 hour >= 7

HERMES_EXE = "G:/hermes/venv/Scripts/hermes.exe"
HERMES_CWD = "G:/hermes"

# ============================================================
# RELAY 管理（0-indexed 存储）
# ============================================================

def read_relay() -> dict:
    if not RELAY_PATH.exists():
        return {"STATUS": "INIT", "BATCH": 0, "SYMPTOM_INDEX": 0, "FAIL_COUNT": 0}
    state = {}
    with open(RELAY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, _, val = line.partition(':')
                key = key.strip()
                val = val.strip()
                for int_key in ('BATCH', 'SYMPTOM_INDEX', 'TOTAL_SYMPTOMS', 'PASS_COUNT', 'FAIL_COUNT'):
                    if key == int_key:
                        try:
                            state[key] = int(val)
                        except ValueError:
                            state[key] = val
                        break
                else:
                    state[key] = val
    return state

def write_relay(state: dict):
    content = f"""# 横向打通进度 RELAY
# 自动更新于 {datetime.now().isoformat()}

STATUS: {state.get('STATUS', 'ACTIVE')}
BATCH: {state.get('BATCH', 0)}
SYMPTOM_INDEX: {state.get('SYMPTOM_INDEX', 0)}
TOTAL_SYMPTOMS: {state.get('TOTAL_SYMPTOMS', 30)}
PASS_COUNT: {state.get('PASS_COUNT', 0)}
FAIL_COUNT: {state.get('FAIL_COUNT', 0)}
CURRENT_SYMPTOM: {state.get('CURRENT_SYMPTOM', '')}
LAST_UPDATE: {datetime.now().isoformat()}
"""
    with open(RELAY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def save_state(batch_idx, symptom_idx, pass_count, fail_count, total_symptoms, status, current_symptom=''):
    """统一写入 RELAY（0-indexed）"""
    state = {
        'STATUS': status, 'BATCH': batch_idx, 'SYMPTOM_INDEX': symptom_idx,
        'TOTAL_SYMPTOMS': total_symptoms, 'PASS_COUNT': pass_count,
        'FAIL_COUNT': fail_count, 'CURRENT_SYMPTOM': current_symptom
    }
    write_relay(state)

# ============================================================
# 检测
# ============================================================

def check_deadline() -> bool:
    now = datetime.now()
    if now >= HARD_DEADLINE:
        print(f"[{now:%H:%M:%S}] ⏰ 已过硬截止 {HARD_DEADLINE:%Y-%m-%d %H:%M}，暂停")
        return True
    return False

def check_pause() -> bool:
    if PAUSE_FILE.exists():
        print(f"[{datetime.now():%H:%M:%S}] ⏸️  检测到 PAUSE-LATERAL 文件，暂停")
        return True
    state = read_relay()
    if state.get('STATUS') == 'PAUSED':
        print(f"[{datetime.now():%H:%M:%S}] ⏸️  RELAY STATUS=PAUSED，暂停")
        return True
    return False

# ============================================================
# Hermes 子进程
# ============================================================

def build_lateral_instruction(symptom_name: str) -> str:
    return (
        f"加载 renji-learning-pipeline skill 和 medical-memory-palace skill。"
        f"然后执行横向打通任务。"
        f"\n\n## 任务：横向打通症状「{symptom_name}」\n\n"
        f"步骤：\n"
        f"1. 搜索 ~/hermes-data/renji-learning/symptom-classification-index.md，"
        f"找「{symptom_name}」相关段落（用 search_files 搜 content 模式）\n"
        f"2. 从 Hindsight 中搜索「{symptom_name}」补充倪师相关记忆（用 hindsight_recall）\n"
        f"3. 横向打通五门课——该症状在每门课中的辨证分型、病机、方剂、针灸\n"
        f"   - 伤寒论：六经辨证\n"
        f"   - 金匮要略：杂病辨证\n"
        f"   - 黄帝内经：病机理论根源\n"
        f"   - 针灸大成：针灸治法+穴位\n"
        f"   - 神农本草经：相关药物\n"
        f"4. 输出鉴别诊断表\n\n"
        f"## 鉴别诊断表格式：\n"
        f"| 分型 | 病机(内经) | 辨证要点 | 方剂(伤寒/金匮) | 针灸 | 关键药物 | 出处(C1/C2) |\n"
        f"|------|-----------|---------|----------------|------|---------|------------|\n\n"
        f"5. 写 checkpoint：~/hermes-data/renji-learning/checkpoints/lateral-{symptom_name}.md\n"
        f"6. 存 Hindsight：hindsight_retain 带标签 renji,lateral,{symptom_name}\n"
        f"7. 更新 RELAY：写 ~/hermes-data/renji-learning/RELAY-LATERAL.md\n"
        f"   格式：STATUS=PASS，CURRENT_SYMPTOM={symptom_name}，PASS_COUNT += 1\n\n"
        f"完成后退出，不要继续下一个症状——supervisor 会自动接力。"
    )

def run_symptom(symptom_name: str, batch_num: int, symptom_idx: int, total: int) -> int:
    instruction = build_lateral_instruction(symptom_name)
    cmd = [HERMES_EXE, "-z", instruction, "--yolo"]
    
    print(f"[{datetime.now():%H:%M:%S}] 🚀 批次{batch_num+1} 症状 {symptom_idx}/{total}: {symptom_name}")
    
    try:
        proc = subprocess.Popen(
            cmd, cwd=HERMES_CWD,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace'
        )
        try:
            stdout, _ = proc.communicate(timeout=TIMEOUT_PER_SYMPTOM)
            exit_code = proc.returncode
            
            safe_name = symptom_name.replace('/', '_').replace('\\', '_')
            log_file = LOG_DIR / f"lateral-b{batch_num+1}-{safe_name}-{datetime.now():%Y%m%d-%H%M%S}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(stdout or "(no output)")
            
            if exit_code == 0:
                print(f"[{datetime.now():%H:%M:%S}] ✅ {symptom_name} 完成 (exit={exit_code})")
            else:
                print(f"[{datetime.now():%H:%M:%S}] ⚠️  {symptom_name} 异常退出 (exit={exit_code})")
            
            return 0 if exit_code == 0 else 2
            
        except subprocess.TimeoutExpired:
            print(f"[{datetime.now():%H:%M:%S}] ⏰ {symptom_name} 超时，强制终止")
            proc.kill()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.terminate()
            return 1
            
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] 💥 {symptom_name} 启动失败: {e}")
        return 2

# ============================================================
# 主循环
# ============================================================

def main():
    print("=" * 55)
    print("  人纪横向打通监督脚本 v1.1")
    print(f"  启动时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  症状超时: {TIMEOUT_PER_SYMPTOM}s | 硬截止: {HARD_DEADLINE:%m-%d %H:%M}")
    print("=" * 55)
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(SYMPTOM_LIST_PATH, 'r', encoding='utf-8') as f:
        symptom_data = json.load(f)
    batches = symptom_data['batches']
    
    state = read_relay()
    
    batch_idx = state.get('BATCH', 0)
    symptom_idx = state.get('SYMPTOM_INDEX', 0)
    pass_count = state.get('PASS_COUNT', 0)
    fail_count = state.get('FAIL_COUNT', 0)
    consecutive_fails = 0
    
    # 自动恢复 PAUSED
    if state.get('STATUS') == 'PAUSED' and batch_idx < len(batches):
        print(f"📌 恢复进度：批次 {batch_idx+1}/{len(batches)}，症状 {symptom_idx+1}")
        state['STATUS'] = 'ACTIVE'
        write_relay(state)
    
    total_symptoms = sum(len(b) for b in batches)
    
    while batch_idx < len(batches):
        batch = batches[batch_idx]
        
        while symptom_idx < len(batch):
            if check_deadline():
                save_state(batch_idx, symptom_idx, pass_count, fail_count, total_symptoms, 'PAUSED')
                print(f"\n[{datetime.now():%H:%M:%S}] 🛑 已暂停（截止）")
                print(f"   进度: 批次{batch_idx+1}/{len(batches)}, PASS={pass_count}, FAIL={fail_count}")
                return
            if check_pause():
                save_state(batch_idx, symptom_idx, pass_count, fail_count, total_symptoms, 'PAUSED')
                print(f"\n[{datetime.now():%H:%M:%S}] 🛑 已暂停（PAUSE 文件）")
                return
            if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                save_state(batch_idx, symptom_idx, pass_count, fail_count, total_symptoms, 'PAUSED')
                print(f"\n[{datetime.now():%H:%M:%S}] 🚨 连续失败 {consecutive_fails} 次，自动暂停")
                return
            
            symptom = batch[symptom_idx]
            current_num = sum(len(batches[i]) for i in range(batch_idx)) + symptom_idx + 1
            
            save_state(batch_idx, symptom_idx, pass_count, fail_count, total_symptoms, 'ACTIVE', symptom)
            
            print(f"\n{'='*45}")
            print(f"[{datetime.now():%H:%M:%S}] 📖 第{current_num}/{total_symptoms}个症状: {symptom}")
            print(f"{'='*45}")
            
            result = run_symptom(symptom, batch_idx, current_num, total_symptoms)
            
            if result != 0:
                consecutive_fails += 1
                fail_count += 1
                print(f"[{datetime.now():%H:%M:%S}] 🔴 {symptom} 故障 (result={result})，连续失败: {consecutive_fails}")
                time.sleep(SLEEP_BETWEEN * 2)
                continue
            
            time.sleep(SLEEP_BETWEEN)
            new_state = read_relay()
            
            if new_state.get('STATUS') == 'RETRY':
                consecutive_fails += 1
                fail_count += 1
                print(f"[{datetime.now():%H:%M:%S}] 🔄 {symptom} 不通过，重试")
            else:
                consecutive_fails = 0
                pass_count += 1
                symptom_idx += 1
                print(f"[{datetime.now():%H:%M:%S}] ✅ {symptom} 通过 → {current_num}/{total_symptoms}")
            
            time.sleep(SLEEP_BETWEEN)
        
        batch_idx += 1
        symptom_idx = 0
        if batch_idx < len(batches):
            print(f"\n[{'='*45}]")
            print(f"[{datetime.now():%H:%M:%S}] 🎯 批次 {batch_idx} 完成！共{len(batches[batch_idx-1])}个症状")
            print(f"[{'='*45}]")
            save_state(batch_idx, 0, pass_count, fail_count, total_symptoms, 'ACTIVE')
            time.sleep(SLEEP_BETWEEN)
    
    save_state(batch_idx, 0, pass_count, fail_count, total_symptoms, 'DONE')
    print(f"\n[{'='*45}]")
    print(f"[{datetime.now():%H:%M:%S}] 🎉 横向打通全部完成！PASS={pass_count} FAIL={fail_count}")
    print(f"[{'='*45}]")


signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

if __name__ == '__main__':
    main()
