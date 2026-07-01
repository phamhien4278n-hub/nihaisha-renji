# 倪海厦人纪 · AI 深度学习系统

# nihaisha-renji · AI Deep Learning System for Traditional Chinese Medicine

> 🎓 逐段读原文 → 建记忆树 → 挂宫殿房间 → 闭卷自测 → 100% 掌握
> 🎓 Read → Build Memory Tree → Mount in Memory Palace → Closed-book Self-test → 100% Mastery

---

## 📌 这是什么？ / What is this?

**倪海厦《人纪》系列课程（针灸·黄帝内经·神农本草经·伤寒论·金匮要略）的完整 AI 学习框架。**

**A complete AI learning framework for nihaisha's Renji (Human Epoch) lecture series — covering Acupuncture, Huangdi Neijing, Shennong's Herbal Classic, Shanghan Lun, and Jingui Yaolue.**

所有知识提炼自倪海厦人纪课程字幕原文——不是通用大模型的知识，不是二手解读，是**逐字逐句从倪师原话中提取、建树、验证**的结果。

All knowledge is extracted directly from nihaisha's original lecture transcripts — not from general-purpose LLM knowledge, not from second-hand interpretations, but **word-by-word extraction, tree construction, and verification from Master Ni's original words**.

### 📦 这不是空方法 / Not Just Methods — Actual Knowledge Inside

**本仓库包含了五门课完整学习产物**——不是只给一个"学习框架"让你自己去学，而是把我们已经学完、验证通过的**知识树、治则索引、临床珍珠、症状横向对照表**全部开源。

**This repo ships the complete learning artifacts of all 5 courses** — not just a "learning framework" for you to fill yourself. The verified **memory trees, treatment index, clinical pearls, and symptom cross-reference tables** are all included.

| 知识资产 / Knowledge Assets | 内容量 / Volume | 说明 / Description |
|---------------------------|:---:|------|
| 五门课 checkpoint | 97 段 | 每段原始知识树——针灸22段·内经17段·本草25段·伤寒17段·金匮38段 |
| accumulated-tree.md | 6 层 24 房间 | 所有知识树汇总——按宫殿房间组织，完整可查 |
| therapeutic-index.md | 30+ 症状 × 21 维治则 | 每个症状的全部治法体系逐格标注 |
| clinical-pearls.md | 50+ 条 | 倪师"统治一切XX病"核心治法汇总 |
| symptom-classifications.md | 30 症状分型 | 太阳病·痹·痿·咳·黄疸·便秘·下利等完整分型 |
| western-lab-tcm-mapping.md | 全套映射表 | 血脂/肝功/血糖/血常规→中医病机逐项翻译 |
| 实战案例 / Cases | 5+ 个 | 反酸烧心·水肿眩晕·化验单辨证·凌晨勃醒等完整推理链路 |

---

## 🔥 核心特色 / Core Features

| 特色 / Feature | 说明 / Description |
|---------------|-------------------|
| **逐段读原文** / Segment-by-segment Reading | 五门课共 97 个学习段，每段 5-10KB 原文精读 |
| **建记忆树** / Memory Tree Construction | 每个知识点挂载到 6 层宫殿对应房间，结构化存储 |
| **挂宫殿房间** / Memory Palace Mounting | 基于罗马房间法——每层 4 个方位房间，知识点有"空间地址" |
| **闭卷自测** / Closed-book Self-testing | 每段学完立即自测，不过关不前进，0% 欺骗率 |
| **三遍学习法** / Three-pass Learning | 两纵一横：第一遍建树 → 第二遍重建补漏 → 第三遍纵向重建+横向症状打通 |
| **21 维治则体系** / 21-Dimension Treatment Framework | 从十问辨证到补泻手法，逐层检查不遗漏 |
| **症状横向索引** / Cross-reference Symptom Index | 30+ 症状在五门课中的全部治法一键检索 |
| **临床珍珠** / Clinical Pearls | 倪师"统治一切XX病"级别的核心治法汇总 |

---

## 🏛 记忆宫殿架构 / Memory Palace Architecture

```
         ┌──────────┐
         │  5F 综合层 │ ← 跨系统整合
         ├──────────┤
         │  4F 专科   │ ← 妇科·儿科·外科
         ├──────────┤
         │  3F 内科   │ ← 五脏六腑疾病库
         ├──────────┤
         │  2F 治疗   │ ← 方剂·药物·针灸
         ├──────────┤
         │  1F 诊断   │ ← 辨证·脉诊·望诊
         ├──────────┤
         │ B1 基础   │ ← 经络·穴位·药性
         └──────────┘
```

每层 4 个房间（北/东/南/西），知识点按空间定位——回想时"走到那个房间，看墙上挂的知识树"。

---

## 📚 三遍学习法 / Three-Pass Learning Method

### 第一遍：纵向建树 / Pass 1 — Vertical Tree Building
逐段读原文 → 建记忆树 → 挂宫殿房间 → 写云端记忆 → 闭卷自测 → 开卷批改 → 100% 通过才前进

### 第二遍：纵向重建 / Pass 2 — Vertical Reconstruction
**与第一遍完全相同**——重新读原文、重新建树、重新自测。禁止凭记忆快速复诵。独立的一轮学习发现第一遍遗漏的细节。

### 第三遍：纵向重建 + 横向打通 / Pass 3 — Reconstruction + Cross-linking
逐段重建 → 标注遗漏 → 横向关联（每段知识点与其他段/其他经络的交叉引用）→ 闭卷自测（含跨科题目）→ 全部完成后建立"症状→治法"横向索引

> ⚠️ 为什么需要横向打通？纵向按经络存储（"梅花灸在任脉中脘"），但临床问题是按症状检索的（"反酸怎么治？"）。存储维度 ≠ 检索维度。第三遍末尾的横向症状索引解决的就是这个问题。

---

## 🗂 仓库结构 / Repo Structure

```
nihaisha-renji/
├── README.md                         ← 你在这里
│
├── skills/                           ← 学习方法论（Hermes Agent 技能包）
│   ├── renji-knowledge-base/         ← 21维治则体系·症状索引·化验单映射
│   │   ├── SKILL.md                  ← 主技能：临床回答守则·内经先行铁律
│   │   └── references/
│   │       ├── symptom-classifications.md    ← 30 症状分型完整清单
│   │       ├── western-lab-tcm-mapping.md    ← 化验单→中医病机映射表
│   │       ├── clinical-pearls.md            ← 50+ 条倪师核心治法


│   │       ├── hemorrhoid-differentiation.md       ← 痔疮寒热虚实鉴别
│   │       ├── reflux-differential-journey.md      ← 反酸鉴别诊断全程
│   │       └── hemiplegia-formula-system.md        ← 半身不遂方剂体系
│   │
│   ├── medical-memory-palace/        ← 三遍学习法·记忆宫殿·自测系统
│   │   ├── SKILL.md                  ← 主技能：逐段读→建树→挂宫殿→自测
│   │   └── references/
│   │       ├── accumulated-tree.md   ← ★ 所有知识树汇总——6层24房间
│   │       ├── therapeutic-index.md  ← ★ 30症状×21治则完整索引
│   │       └── review-schedule.md    ← 间隔复习调度表
│   │
│   └── renji-learning-pipeline/      ← 自动化学习流水线
│       ├── SKILL.md                  ← 零上下文腐烂全自动接力
│       └── references/
│           └── supervisor-architecture.md  ← Supervisor 设计文档
│
├── checkpoints/                      ← ★ 五门课每段知识树产物
│   ├── zhenjiu/                      ← 针灸大成 22 段
│   ├── neijing/                      ← 黄帝内经 17 段
│   ├── shennong/                     ← 神农本草经 25 段
│   ├── shanghan/                     ← 伤寒论 17 段
│   └── jingui/                       ← 金匮要略 38 段
│
└── cases/                            ← 实战案例（独立可读）
    ├── reflux-burning-full-analysis.md    ← 反酸烧心·内经→经方→针灸全链路
    ├── edema-dizziness-three-layer.md     ← 水肿眩晕·中焦积水三层治疗

```

---

## ⚠️ 声明 / Disclaimer

- 本系统为 **AI 学习工具**，非临床诊断系统。不可替代医师诊断。
- 所有内容源自倪海厦人纪课程字幕原文，版权归倪师及其版权方所有。本仓库仅提供学习框架和方法论，不包含课程视频/音频/完整字幕。
- AI 输出仅供学习参考，临床应用需在执业医师指导下进行。

- This system is an **AI learning tool**, NOT a clinical diagnosis system. It cannot replace physician diagnosis.
- All content is derived from nihaisha's Renji lecture transcripts. Copyright belongs to Master Ni and the copyright holders. This repository provides only the learning framework and methodology, not the course videos/audio/full transcripts.
- AI output is for learning reference only. Clinical application requires supervision by licensed practitioners.

---

## 🛠 如何使用 / How to Use

本仓库为 **Hermes Agent** 技能包。安装 Hermes Agent 后，将 `skills/` 目录复制到 `~/.hermes/skills/` 下即可加载。

This repository is a **Hermes Agent skill pack**. After installing Hermes Agent, copy the `skills/` directory to `~/.hermes/skills/` to load.

---

## 🔮 后续计划 / Coming Soon

本仓库目前开源了**学习框架 + 知识树 + 实战案例**。更多高级内容将在后续版本中发布：

This repo currently open-sources the **learning framework + knowledge trees + clinical cases**. More advanced content is coming in future releases:

| 计划发布 / Planned | 内容 / Content | 状态 / Status |
|-------------------|---------------|:--:|
| **知识图谱数据包** / Knowledge Graph Dataset | 737 个结构化节点 · 五门课实体+关系网络 · 跨科关联图谱 | 🚧 整理中 / Preparing |
| **临床推理引擎** / Clinical Reasoning Engine | 21 维治则自动遍历 · 症状→治法智能路由 · 化验单→中医辨证自动映射 | 🚧 开发中 / In Development |
| **Docker 一键部署包** / Docker One-Click Deployment | PostgreSQL + pgvector + 知识图谱数据 · 本地语义检索 · 零门槛使用 | 🚧 构建中 / Building |
| **云端 API 服务** / Cloud API Service | 知识图谱实时查询 · 持续更新 · 按月订阅 | 📋 规划中 / Planned |

> ⚠️ 知识图谱与记忆系统为独立产品，不包含在本仓库中。Watch 本仓库获取发布通知。
> ⚠️ The knowledge graph and memory system are separate products, not included in this repo. Watch this repo for release announcements.

---

> *"因为谎言导致让别人失望，最终你将不再被信任。"*  
> *"Once you lose trust through lies, you are no longer trustworthy."*  
> —— Hermes Agent 小凛 · Xiaolin
