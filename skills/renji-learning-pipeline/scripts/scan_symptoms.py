#!/usr/bin/env python3
"""症状分型原文索引——扫描所有 segments + checkpoints，提取倪师症状分型总结段落。
用途：Phase 2 横向整理的第一步——先知道倪师一共讲了哪些症状分型，再做完整诊断表。
输出：symptom-classification-index.md"""
import re
from pathlib import Path

base = Path("~/hermes-data/renji-learning")
segment_dirs = [
    base / "segments",
    base / "segments-jingui",
    base / "segments-shanghan",
    base / "segments-bencao",
]
checkpoint_dir = base / "checkpoints"

# 症状关键词
symptoms = [
    "头痛","心痛","胸痛","腹痛","胁痛","腰痛","骨节痛","身痛",
    "下利","腹泻","泄泻","痢疾",
    "呕吐","呕","吐","哕","嗳气","呃逆",
    "咳嗽","咳","喘","短气",
    "水肿","水气","水病","腹水","浮肿","肿胀",
    "黄疸",
    "出血","吐血","衄血","咳血","便血","尿血","崩漏",
    "小便不利","小便难","淋","癃闭",
    "口渴","消渴",
    "汗","汗出","自汗","盗汗","无汗",
    "发热","恶寒","往来寒热","潮热",
    "失眠","不寐","不得眠",
    "月经","经期","带下","崩漏","妊娠","产后",
    "腹胀","腹满","痞","心下痞",
    "便秘","大便难",
    "眩晕","眩","悸","惊悸",
    "厥","逆","四逆","手足冷",
    "痹","历节","风湿","湿痹",
    "痉","瘛疭","抽搐",
    "疟","虫","蛔虫",
    "狐惑","百合",
    "肺痿","肺痈",
    "胸痹",
    "寒疝",
    "痰饮","饮","水饮",
    "瘀血","血症","血痹",
    "疮痈","肠痈","浸淫",
    "虚劳","奔豚","转筋",
    "阴狐","疝气",
    "积聚","癥瘕",
    "中风","偏枯",
]

patterns = [
    re.compile(r'第[一二三四五].{0,3}种.{0,15}(' + '|'.join(symptoms) + r')'),
    re.compile(r'(' + '|'.join(symptoms) + r').{0,30}(?:有|分|一共|总共|大致|归纳|概括).{0,10}[种类型个]'),
    re.compile(r'(?:分为|分成|分.{0,2}类).{0,10}(' + '|'.join(symptoms) + r')'),
    re.compile(r'#+\s*(.+?分类.+)|#+\s*(.+?分型.+)'),
    re.compile(r'(?:几个|几种|几类).{0,20}(' + '|'.join(symptoms) + r')'),
]

def find_classification_context(lines, line_idx, window=8):
    start = max(0, line_idx - window)
    end = min(len(lines), line_idx + window + 1)
    return '\n'.join(lines[start:end])

results = []

for seg_dir in segment_dirs:
    if not seg_dir.exists():
        continue
    for f in sorted(seg_dir.glob('*.txt')):
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                for pat in patterns:
                    m = pat.search(line)
                    if m:
                        ctx = find_classification_context(lines, i)
                        results.append({
                            'file': f.name, 'dir': seg_dir.name,
                            'line': i+1, 'match': m.group()[:200],
                            'context': ctx[:800]
                        })
                        break
        except:
            pass

if checkpoint_dir.exists():
    for f in sorted(checkpoint_dir.glob('*.md')):
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                for pat in patterns:
                    m = pat.search(line)
                    if m:
                        ctx = find_classification_context(lines, i)
                        results.append({
                            'file': f.name, 'dir': 'checkpoints',
                            'line': i+1, 'match': m.group()[:200],
                            'context': ctx[:800]
                        })
                        break
                if re.match(r'^#+\s*(.+?(?:分类|分型|几种|种情况).+)', line):
                    ctx = find_classification_context(lines, i, 15)
                    results.append({
                        'file': f.name, 'dir': 'checkpoints',
                        'line': i+1, 'match': line.strip()[:200],
                        'context': ctx[:800]
                    })
        except:
            pass

seen = set()
unique = []
for r in results:
    key = (r['file'], r['line'] // 3)
    if key not in seen:
        seen.add(key)
        unique.append(r)

out = Path("~/hermes-data/renji-learning/symptom-classification-index.md")
lines_out = ["# 倪海厦人纪——症状分型总结原文索引\n"]
lines_out.append(f"> 自动提取时间：{__import__('datetime').datetime.now()}")
lines_out.append(f"> 匹配段落数：{len(unique)}\n---\n")

for r in sorted(unique, key=lambda x: (x['dir'], x['file'], x['line'])):
    lines_out.append(f"## [{r['dir']}] {r['file']} (行{r['line']})\n")
    lines_out.append(f"**匹配**：{r['match']}\n```")
    lines_out.append(r['context'])
    lines_out.append("```\n---\n")

out.write_text('\n'.join(lines_out), encoding='utf-8')
print(f"✅ 完成！匹配段落数：{len(unique)}")
print(f"输出：{out}")
