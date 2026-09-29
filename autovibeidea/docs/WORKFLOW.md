# EAR 工作流详解

## 1. 全局流程图

```
                        [研究方向输入]
                             │
                             ▼
                   ┌─────────────────┐
                   │   Stage 1       │
                   │   /lit-survey   │──→ LANDSCAPE.md + LANDSCAPE.json
                   │   文献调研       │
                   └────────┬────────┘
                            │ Gap Matrix (5-15 gaps, 6 类型)
                            ▼
                      ◆ Checkpoint 1 ◆
                            │
                            ▼
                   ┌─────────────────┐
                   │   Stage 2       │
                   │   /idea-gen     │──→ IDEAS_RAW.md + IDEAS_FILTERED.md
                   │   想点子         │
                   └────────┬────────┘
                            │ 4-6 surviving ideas
                            ▼
                      ◆ Checkpoint 2 ◆
                            │
                            ▼
                   ┌─────────────────┐
                   │   Stage 3       │
                   │   /idea-screen  │──→ SCREENING_REPORT.md + SCREENING_RANKED.md
                   │   多维筛选       │
                   └────────┬────────┘
                            │ Top 1-2 ideas (Composite >= 7.0)
                            ▼
                      ◆ Checkpoint 3 ◆
                            │
                            ▼
                   ┌─────────────────┐
                   │   Stage 4       │
                   │   /idea-refine  │──→ FINAL_PROPOSAL.md + REFINEMENT_REPORT.md
                   │   深度精炼       │
                   └────────┬────────┘
                            │
                            ▼
                      ◆ Checkpoint 4 ◆
                            │
                            ▼
              [IDEA_DISCOVERY_REPORT.md 汇总报告]
```

---

## 2. Stage 1: 文献调研 详解

### 目标
搜索并分析多来源论文，构建领域全景图并识别研究 Gap。

### 内部流程图

```
[研究方向]
     │
     ├──→ Step 0a: Zotero 搜索 (MCP)
     │         │ 收藏夹、标签、批注、BibTeX
     │         ▼
     ├──→ Step 0b: Obsidian 搜索 (MCP)
     │         │ 研究笔记、标签引用、WikiLinks
     │         ▼
     ├──→ Step 0c: 本地 PDF 扫描
     │         │ papers/ 或 literature/ 目录
     │         │ 每篇读前 3 页，上限 20 篇
     │         ▼
     └──→ Step 1: Web 搜索
               │ arXiv API + Semantic Scholar + Google Scholar
               │ 去重 (跳过已有论文)
               ▼
          Step 2: 逐篇分析
               │ 提取: 问题/方法/结果/局限/关联
               │ 分配 Paper ID: P01, P02, ...
               │ 目标: 15-30 篇论文
               ▼
          Step 3: 综合与 Gap 识别
               │
               ├── 3a: 主题综合 (3-7 个主题方向)
               │       每个主题标注: active / mature / emerging
               │
               └── 3b: Gap 矩阵
                       │
                       │   6 种 Gap 类型:
                       │   ┌─────────────────────────────┐
                       │   │ cross-domain transfer       │
                       │   │ untested assumption          │
                       │   │ resolution opportunity       │
                       │   │ scaling frontier              │
                       │   │ missing diagnostic            │
                       │   │ overlooked formulation        │
                       │   └─────────────────────────────┘
                       │   置信度: HIGH / MEDIUM / LOW
                       │   目标: 5-15 个 Gap
                       ▼
          Step 4: 输出
               ├── LANDSCAPE.md  (叙述 + 表格 + Gap 矩阵)
               └── LANDSCAPE.json (结构化, 供下游消费)

          (可选) Step 4c: 轨迹追踪
               ├── Top 3 作者的发表弧线
               └── 共著者集群映射 (2-4 个研究组)
```

### 数据源优先级

| 优先级 | 来源 | 提供内容 |
|--------|------|----------|
| 1 | Zotero (MCP) | 收藏、标签、PDF 高亮、BibTeX |
| 2 | Obsidian (MCP) | 研究笔记、纸间链接 |
| 3 | 本地 PDF | 原始 PDF 内容 (前 3 页) |
| 4 | Web 搜索 | arXiv、Semantic Scholar、Google Scholar |

> 优雅降级: 若 MCP 未配置，自动跳过并使用本地 PDF + Web 搜索。

### 输出文件

- **`outputs/LANDSCAPE.md`** -- 包含 Executive Summary、Paper Table、Thematic Analysis、Gap Matrix、Trajectory Analysis、References
- **`outputs/LANDSCAPE.json`** -- 结构化 JSON，字段: `papers[]`, `themes[]`, `gaps[]`, `trajectory{}`

---

## 3. Stage 2: 想点子 详解

### 目标
基于文献全景生成 8-12 个想法，经多层过滤保留 4-6 个高质量方向。

### 漏斗图 (v2: 两段式生成)

```
         ┌────────────────────────────────────────┐
         │      Phase 1: 全景验证                   │
         │  读取 LANDSCAPE.json (或快速 inline 调研)  │
         └───────────────────┬────────────────────┘
                             ▼
         ┌────────────────────────────────────────┐
         │   Phase 2a: 景观批判分析 ← v2 新增       │
         │  gpt-5.4 · xhigh · 新建 thread          │
         │  系统性批判当前 landscape 的结构性弱点:    │
         │    ① Unverified Assumptions             │
         │    ② Incorrectly Generalized Methods    │
         │    ③ Experimental Design Flaws          │
         │    ④ Cross-Domain Misfits               │
         │  输出: CRITIQUE-01...N 批判清单           │
         │  保存: outputs/CRITICAL_ANALYSIS.md     │
         └───────────────────┬────────────────────┘
                             │ CRITIQUE manifest
                             ▼
         ┌────────────────────────────────────────┐
         │   Phase 2b: 基于批判的 Idea 生成 ← v2   │
         │  gpt-5.4 · codex-reply (同一 thread)    │
         │  每个 idea 必须锚定至少一个 CRITIQUE-ID   │
         │  每个 idea 包含 11 个字段:                 │
         │    Title / Anchored Critique (v2新增)    │
         │    Thesis / Problem / Mechanism          │
         │    Non-obvious                           │
         │    Theorem/Conjecture Scaffold (v2新增)  │
         │    Contribution type / Risk              │
         │    Effort / Closest work                 │
         │  多样性约束: ≥50% idea 锚定不同批判条目    │
         └───────────────────┬────────────────────┘
                             │ 8-12 ideas
              ╔══════════════╧══════════════╗
              ║    Phase 3: 初筛 (三重过滤)   ║
              ╚══════════════╤══════════════╝
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │ 3a 可行性   │ │ 3b 新颖性   │ │ 3c 影响力   │
       │            │ │ 快速检查    │ │ "So What?" │
       │ FEASIBLE / │ │ LIKELY      │ │ HIGH /     │
       │ CAVEATS /  │ │ NOVEL /     │ │ MEDIUM /   │
       │ INFEASIBLE │ │ NEEDS CHECK │ │ LOW        │
       └─────┬──────┘ │ / ALREADY   │ └─────┬──────┘
             │        │ DONE        │       │
             │        └─────┬──────┘       │
             └──────────────┼──────────────┘
                            │ 淘汰: INFEASIBLE / ALREADY DONE / LOW IMPACT
                            │ 剩余: 5-8 ideas
                            ▼
              ┌────────────────────────────┐
              │ Phase 4: 何老师四维度评分     │
              │                            │
              │  Longevity     (1-5)       │
              │  Passion       (1-5)       │
              │  Application   (1-5)       │
              │  Uniqueness    (1-5)       │
              │                            │
              │  阈值: >= 12/20 通过        │
              └─────────────┬──────────────┘
                            │ 4-6 ideas
                            ▼
              ┌────────────────────────────┐
              │ Phase 5: 反模式检查          │
              │                            │
              │  1. Overly trendy (过度跟风) │
              │  2. Overly niche  (过度小众) │
              │  3. A+B stitching (缝合怪)  │
              │  4. Scale-dependent(规模依赖)│
              │                            │
              │  标记警告，不自动淘汰         │
              └─────────────┬──────────────┘
                            │
                            ▼
              ┌────────────────────────────┐
              │ Phase 6: 输出               │
              │  IDEAS_RAW.md (全部 8-12)   │
              │  IDEAS_FILTERED.md (4-6)   │
              └────────────────────────────┘
```

### 输出文件

- **`outputs/IDEAS_RAW.md`** -- 全部生成想法 (含淘汰记录)
- **`outputs/IDEAS_FILTERED.md`** -- 存活想法按 He Score 排名 + 淘汰表 + 风险分布

---

## 4. Stage 3: 多维筛选 详解 (核心创新)

### 目标
通过三模块并行评估，为每个 idea 产出综合评分和行动建议。

### 三模块架构

```
                    ┌──────────────────────┐
                    │   输入: 4-6 个 Ideas  │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
       ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
       │  Module A    │ │  Module B    │ │  Module C    │
       │  新颖性评估   │ │  审稿人模拟   │ │  战略评估     │
       │              │ │              │ │              │
       │  4 阶段流程   │ │  3人审稿     │ │  5 个维度     │
       │  多源搜索     │ │  + Meta      │ │  本地直评    │
       │  交叉验证     │ │  Review      │ │              │
       └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
              │                │                │
              ▼                ▼                ▼
         Novelty 0-10    Venue 0-10      Strategic 0-10
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌────────────────────┐
                    │   Composite Score  │
                    │   综合加权评分       │
                    │                    │
                    │   + Feasibility    │
                    │     0-10           │
                    └────────┬───────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │   Rank + Recommend │
                    │   排名与推荐        │
                    └────────────────────┘
```

> **执行依赖**: Module A 必须先于 Module B 完成 (B 需要 A 的新颖性评分和最近工作)。Module C 与 B 可并行。

---

### Module A: 新颖性评估 (4 阶段)

```
Phase A: 提取核心声明
    │  识别 3-5 个需要具备新颖性的技术声明
    ▼
Phase B: 多源文献搜索
    │  Web搜索 (arXiv/Scholar) + LANDSCAPE.json 交叉引用
    │  每个声明至少 3 种检索策略
    │  年份过滤 2024-2026
    ▼
Phase C: 跨模型验证
    │  gpt-5.4 · xhigh reasoning
    │  对每个声明回答:
    │    1. 完全相同的机制是否已发表?
    │    2. 是否存在密切相关的替代路径?
    │    3. 目标会议审稿人是否认为足够新颖?
    ▼
Phase D: 新颖性报告
    │  Score: 0-10
    │  Recommendation: PROCEED / CAUTION / ABANDON
    │  每个声明: HIGH / MEDIUM / LOW
    └──→ 最近工作对比表
```

### Module B: 审稿人模拟

```
Step 1: 加载会议 Profile
    │  venue-profiles/{VENUE}.md
    │  提取: 校准标准 + 审稿人画像 + 裁决选项
    ▼
Step 2: 构造审稿 Prompt (中文)
    │  注入: Idea 描述 + 新颖性评分 (来自 Module A)
    │  gpt-5.4 · xhigh reasoning
    ▼
Step 3: 三位审稿人独立评审
    │
    │  Reviewer 1 (应用研究者): 效率/可扩展/现实影响
    │  Reviewer 2 (实证主义者): 实验严谨性/Baseline/可复现
    │  Reviewer 3 (理论家):     新颖性/数学深度/洞察
    │
    │  每位输出:
    │    校准层级 (Tier 1/2/3) + 优点 + 弱点 + Verdict + "如何让我 Accept"
    ▼
Step 4: Meta Review
    │  核心争议 (审稿人之间应有分歧)
    │  最终裁决 + 执行 Top 3 风险
    ▼
Step 5: Verdict → 数值映射
    │  Strong Reject=1, Reject=3, Weak Reject=4
    │  Weak Accept=6, Accept=8, Strong Accept=10
    │
    └──→ Venue Score = 三人平均 (保留 1 位小数)
```

### Module C: 战略评估 (5 个维度)

| 维度 | 评分范围 | 核心问题 |
|------|---------|----------|
| **Longevity** 持久性 | 1-10 | 5 年后研究者是否还关心这个问题? |
| **Roadmap Viability** 路线图 | 1-10 | Paper 1 之后，Paper 2 和 3 是什么? |
| **Application Grounding** 应用落地 | 1-10 | 学术界之外谁会关心这个结果? |
| **Execution Uniqueness** 执行独特性 | 1-10 | 为什么是这个团队而非 Google/DeepMind/FAIR? |
| **Iteration Readiness** 迭代速度 | 1-10 | 多快能知道这个 idea 是否可行? |

**Strategic Score** = 5 维平均分 (保留 1 位小数)

---

### 综合评分公式

```
COMPOSITE = 0.25 * Novelty + 0.35 * Venue + 0.20 * Strategic + 0.20 * Feasibility
```

| 权重 | 模块 | 来源 |
|------|------|------|
| 0.25 | Novelty (新颖性) | Module A |
| 0.35 | Venue (会议审稿) | Module B |
| 0.20 | Strategic (战略契合) | Module C |
| 0.20 | Feasibility (可行性) | 继承自 idea-gen 或本地 agent 估算 |

> 权重可通过 `-- weights:` 指令覆盖。

### 决策阈值

```
 COMPOSITE >= 7.0  ──→  PROCEED         进入 /idea-refine 深度精炼
 5.0 <= COMP < 7.0 ──→  PROCEED WITH CAUTION  先修补弱项再精炼
 COMPOSITE < 5.0   ──→  ABANDON         归档，不再投入
```

### 输出文件

- **`outputs/SCREENING_REPORT.md`** -- 每个 idea 三模块完整报告 + Composite 计算
- **`outputs/SCREENING_RANKED.md`** -- 排名表 + 精简版报告 + Next Steps

---

## 5. Stage 4: 深度精炼 详解

### 目标
将粗略 idea 打磨为可投稿的具体提案，通过 Problem Anchor + Skeleton + 迭代审稿实现。

### 迭代精炼循环 (v2: 含理论接地 + Socratic 模式 + Deep Expansion)

```
Phase 0: Problem Anchor (锚定)
    │  冻结不可变的底线问题:
    │    底线问题 / 必须解决的瓶颈 / 非目标 / 约束 / 成功条件
    ▼
Phase 0.5: Skeleton Extraction (骨架提取)
    │  State A: 审稿人当前相信什么?
    │  State B: 审稿人读完后必须相信什么?
    │  Skeleton Path: 3-5 个不可跳过的逻辑步骤
    │  保存至 refine-logs/skeleton.md
    ▼
Phase 1: Build Proposal (构建初始提案)
    │  1.1 扫描基础材料 (本地论文 + Web)
    │  1.2 识别技术 Gap
    │  1.3 选择最锐利路线 (Route A: 最小优雅 vs Route B: 前沿原生)
    │  1.4 具体化方法 (11 个必答项)
    │  1.4.T ← v2 理论接地:
    │      T1 Formalizability Scan — 识别可形式化机制，起草公式草稿
    │      T2 Assumption Inventory — 列出假设并标注 STANDARD/RESTRICTIVE/UNVERIFIED
    │  1.4.TE ← v2 Theory-Experiment Alignment Matrix:
    │      对每条理论 claim 映射标准验证协议 (ML 子领域规律)
    │      ┌───────────────────────────────────────────────────────────┐
    │      │ Convergence bound → 训练曲线 + 学习率敏感性 (≥3 seeds)    │
    │      │ Generalization bound → 数据缩放实验 (≥4 scales)          │
    │      │ Sample complexity → 标签效率实验 (≥5 fractions)          │
    │      │ Approximation ratio → 合成实例与精确解对比 (≥20)         │
    │      │ Computational complexity → wall-clock + FLOP (≥5 sizes)  │
    │      │ Expressivity → 构造证明 + 合成任务实证分离                │
    │      │ ...                                                       │
    │      └───────────────────────────────────────────────────────────┘
    │      NOT FEASIBLE claim → ⚠️ Theory-Experiment Gap (提供三条出路)
    │  1.5 评估草图
    │  1.6 写入 round-0-initial-proposal.md
    ▼
Phase 2 Entry: 模式选择 ← v2 新增
    │
    ├── 默认 (无 -- mode) ──→ 标准 review 循环 (见下)
    ├── -- mode: socratic-auto ──→ Socratic 对话循环 (全自动)
    └── -- mode: socratic-human ──→ Socratic 对话循环 (人工参与)

────────────────────────────────────────────────────────
标准路径 (默认):
────────────────────────────────────────────────────────

┌─→ Phase 2: External Review (外部审稿)
│       │  gpt-5.4 · xhigh reasoning · 7 维度评分
│       │
│       │  7 个评分维度:
│       │  ┌────────────────────────────────────────────┐
│       │  │ Problem Fidelity     问题忠实度     15%    │
│       │  │ Method Specificity   方法具体度     25%    │
│       │  │ Contribution Quality 贡献质量       25%    │
│       │  │ Frontier Leverage    前沿利用度     15%    │
│       │  │ Feasibility          可行性         10%    │
│       │  │ Validation Focus     验证聚焦度      5%    │
│       │  │ Venue Readiness      会议就绪度      5%    │
│       │  └────────────────────────────────────────────┘
│       │  Verdict: READY (>=9) / REVISE / RETHINK
│       ▼
│   Phase 3: Top-2 Diagnosis + Revise (诊断与修订)
│       │  3.1 解析审稿反馈 → 更新 score-history.md
│       │  3.2 Top-2 诊断 (只修最大的 2 个问题)
│       │      ├── 读者会在哪里困惑?
│       │      ├── 敌意审稿人会写什么?
│       │      └── 骨架的哪一步断裂了?
│       │  3.3 Skeleton Gap Check (骨架完整性检查)
│       │  3.4 修订 (附带 Anchor Check + Simplicity Check)
│       ▼
│   Phase 4: Re-evaluation (同一线程复审)
│       │  gpt-5.4 · codex-reply (同线程)
│       │  重评 7 维度 + Drift Warning
│       │
│       ├── Score >= 9 且 READY 且无 Drift? ──Yes──┐
│       │                                          │
│       └── No (且轮次 < 3) ──→ 回到 Phase 3      │
│                                                  │
└── (最多 3 轮迭代)                                 │
                                                   ▼
────────────────────────────────────────────────────────
Socratic 路径 (-- mode: socratic):     ← v2 新增
────────────────────────────────────────────────────────

    Phase 2S: GPT 主动提问 (Turn 0, 新建 thread)
        │  规则: 禁止评分直到宣称完全理解
        │  每轮: 3-5 个具体机制问题 (非模糊批评)
        │    Good: "Step2 的 loss 是 supervised 还是 self-supervised?"
        │    Bad:  "方法不够清晰"
        ▼
    Turn Handler (最多 5 轮):
        │
        ├── 检测"我已充分理解这个方法" ──Yes──→ 最终评分 ──┐
        │                                                  │
        ├── 提取问题 → [socratic-human 模式: PAUSE 等人工]  │
        │             [socratic-auto 模式: 本地 agent 自动回答] │
        │                                                  │
        └── 整合答案 + 扩写提案 → 继续对话                   │
                                                           │
    (到达 MAX_TURNS=5 时强制评分)                            │
                                                           │
    单次评分 (7维度) → 直接进入 Phase 5.5 ◄────────────────┘

────────────────────────────────────────────────────────
两条路径汇合:
────────────────────────────────────────────────────────

Phase 5.5: Deep Expansion Pass ← v2 新增 (两条路径都执行)
    │  扫描当前最优提案中的 [EXPAND] 章节:
    │    ├── 方法组件只有散文，无公式/伪代码 → [EXPAND]
    │    ├── Loss 只提名字未展开 → [EXPAND]
    │    ├── 模块无输入/输出维度 → [EXPAND]
    │    └── 训练 recipe 无具体超参 → [EXPAND]
    │  gpt-5.4 · codex-reply (同线程)
    │  每个 [EXPAND] 节要求:
    │    ① 完整 loss 公式 (所有项定义)
    │    ② 5-15 行伪代码
    │    ③ 模块接口 (输入/输出维度和类型)
    │    ④ 超参范围 + 依据
    │  重跑 Theory-Experiment Alignment 检查 (捕获新增理论 claim)
    │  输出: refine-logs/round-N-expanded.md
    ▼
Phase 5: Final Report (最终输出)
    ├── refine-logs/skeleton.md
    ├── refine-logs/round-N-expanded.md  ← v2 新增 (Deep Expansion 产物)
    ├── refine-logs/REVIEW_SUMMARY.md
    ├── refine-logs/FINAL_PROPOSAL.md    (来自 expanded 版本)
    ├── refine-logs/REFINEMENT_REPORT.md
    └── refine-logs/score-history.md
```

### Skeleton 骨架提取概念

骨架定义了提案的逻辑脊柱——从审稿人的当前认知 (State A) 到目标认知 (State B) 的最短路径。

```
State A                          State B
审稿人当前相信什么              审稿人读完后必须相信什么
(传统智慧/不知道的)              (认知转变/新信念/新工具)
        │                              ▲
        │    Skeleton Path             │
        └──→ Step 1 → Step 2 → ... → Step N
             每一步不可跳过: 跳过则读者无法抵达 State B
```

每轮修订时执行 Skeleton Gap Check: 提案的每个章节必须映射到骨架的某一步。无映射的章节要么多余，要么骨架不完整。

### Top-2 诊断纪律

每轮只修最大的 2 个问题，不试图一次解决所有审稿意见。这防止了提案在多方反馈间震荡，保持修改的聚焦性。

### 四项核心检查 (每轮必做)

1. **Anchor Check** -- 修改是否仍然在解决原始问题?
2. **Simplicity Check** -- 主贡献是否仍然聚焦? 能否删除/合并组件?
3. **Skeleton Gap Check** -- 每个骨架步骤是否有对应章节?
4. **Drift Warning** -- 审稿建议是否导致问题偏移?

---

## 6. 多模型协作

```
    本地 agent (执行层)                         External LLM / gpt-5.4 (评审/生成层)
    ─────────────────                       ──────────────────────────────────────
    文献搜索 / PDF / Zotero / Obsidian       景观批判分析 Phase 2a (xhigh) ← v2
    Gap 识别 & 主题综合                      批判锚定 idea 生成 Phase 2b (xhigh) ← v2
    初筛: 可行性 / 新颖性快检 / 影响力        新颖性交叉验证 (Phase C)
    何老师四维度评分                          审稿人模拟: 3 人 + Meta Review (xhigh)
    反模式检查                               标准迭代审稿: 7 维度评分 (xhigh)
    骨架提取 / Problem Anchor               复审: 同一线程 codex-reply (xhigh)
    理论接地分析 (Phase 1.4.T) ← v2          Socratic 对话 (主动提问模式) ← v2
    Theory-Experiment Matrix ← v2           Deep Expansion (填充公式/伪代码) ← v2
    提案撰写 & 修订
    战略契合度评估 (Module C)
    维护简洁性 / 推回过度复杂化

    ◄──────── Codex MCP (mcp__codex__codex / codex-reply) ────────►
                或 (--gpt-only) tools/gpt_call.sh → OpenAI API ← v2

    设计原则:
    • 本地 agent 负责结构化推理、搜索、过滤、撰写、理论对齐检查
    • External LLM 负责批判性分析、发散性创作、对抗性审稿、Socratic 追问
    • 所有外部 LLM 调用使用 xhigh reasoning effort
    • Phase 2a 的 threadId 贯穿 Phase 2b、review 轮次、Phase 5.5 全流程
    • GPT-only 路径: CODEX_MODE=gpt-api (./run.sh --gpt-only) ← v2
```

---

## 7. 数据流图

```
Stage 1: /lit-survey
    │
    ├──→ outputs/LANDSCAPE.md        (叙述 + 表格 + Gap 矩阵)
    └──→ outputs/LANDSCAPE.json      (结构化数据, 供下游消费)
              │
              │ 读取 gaps[] + papers[]
              ▼
Stage 2: /idea-gen
    │
    ├──→ outputs/CRITICAL_ANALYSIS.md (景观批判清单 CRITIQUE-XX) ← v2
    ├──→ outputs/IDEAS_RAW.md         (全部 8-12 个 idea，含 Anchored Critique + Theorem Scaffold)
    └──→ outputs/IDEAS_FILTERED.md    (4-6 个存活 idea + 淘汰表)
              │
              │ 读取存活 ideas + feasibility
              ▼
Stage 3: /idea-screen
    │
    ├──→ outputs/SCREENING_REPORT.md (三模块完整报告)
    └──→ outputs/SCREENING_RANKED.md (排名表 + 精简报告)
              │
              │ Top 1-2 ideas + 审稿反馈
              ▼
Stage 4: /idea-refine
    │
    ├──→ refine-logs/skeleton.md
    ├──→ refine-logs/round-0-initial-proposal.md  (含 Theoretical Grounding + T-E Matrix) ← v2
    ├──→ refine-logs/round-N-review.md
    ├──→ refine-logs/round-N-refinement.md
    ├──→ refine-logs/round-N-expanded.md          (Deep Expansion Pass 产物) ← v2
    ├──→ refine-logs/socratic-turn-T-*.md         (Socratic 对话模式时) ← v2
    ├──→ refine-logs/REVIEW_SUMMARY.md
    ├──→ refine-logs/FINAL_PROPOSAL.md            (来自 expanded 版本)
    ├──→ refine-logs/REFINEMENT_REPORT.md
    └──→ refine-logs/score-history.md
              │
              ▼
Final: outputs/IDEA_DISCOVERY_REPORT.md (全流程汇总)
```

---

## 8. Checkpoint 机制

Pipeline (`/idea-pipeline`) 在每个 Stage 之间设置检查点，让用户有机会介入或调整。

```
  Stage 1 ──→ Checkpoint 1 ──→ Stage 2 ──→ Checkpoint 2 ──→ Stage 3 ──→ Checkpoint 3 ──→ Stage 4 ──→ Checkpoint 4
               "文献调研完成"                "Idea 生成完成"              "筛选完成"                  "精炼完成"
```

| Checkpoint | 呈现内容 | 用户选项 | AUTO_PROCEED 行为 |
|------------|---------|---------|-------------------|
| **1 (文献后)** | 论文数、Gap 数、Top 3 主题 | 确认 / 调整范围 / 重新搜索 | 基于当前结果自动继续 |
| **2 (生成后)** | 存活 idea 列表 + He Score + Risk | 选择 idea / 换方向 / 重新生成 | 对所有过滤后 idea 进行筛选 |
| **3 (筛选后)** | 排名表 + Composite Score + 审稿共识 | 确认精炼 / 选择特定 idea / 换 venue | 精炼排名前 REFINE_TOP_N 个 |
| **4 (精炼后)** | 最终得分 + Verdict + 方法论文 | 接受 / 继续迭代 / 手动调整 | 输出最终报告 |

### AUTO_PROCEED 机制

- **默认值**: `true`
- 当 `AUTO_PROCEED = true` 时，若用户在 Checkpoint 未作回应，Pipeline 自动选择最优选项继续。
- 通过 `-- auto: false` 可强制在每个 Checkpoint 等待用户确认。

---

## 9. 会议 Profile 系统

### 存放位置
```
venue-profiles/
├── _template.md     模板
├── ICML.md          ICML 配置
├── NeurIPS.md       NeurIPS 配置
└── VLDB.md          VLDB 配置
```

### Profile Schema

```
┌──────────────────────────────────────────────────┐
│               Venue Profile                      │
├──────────────────────────────────────────────────┤
│ Metadata                                         │
│   name:            会议缩写 (ICML)               │
│   full_name:       完整名称                       │
│   type:            ML | systems | NLP | ...      │
│   acceptance_rate: ~25%                          │
│   verdict_options: Strong Reject → Strong Accept │
│   allows_revision: true | false                  │
├──────────────────────────────────────────────────┤
│ Calibration Tiers (校准标准)                      │
│                                                  │
│   Tier 1: 顶级工作                               │
│     characteristics + attitude (严格的肯定)       │
│                                                  │
│   Tier 2: 中上等 (Solid-Incremental)             │
│     characteristics + attitude (怀疑的审视)       │
│                                                  │
│   Tier 3: 平庸/瑕疵                              │
│     characteristics + attitude (严格的底线审查)    │
├──────────────────────────────────────────────────┤
│ Reviewer Profiles (审稿人画像)                    │
│                                                  │
│   Reviewer 1: [角色名]                           │
│     focus / accept_when / reject_when            │
│                                                  │
│   Reviewer 2: [角色名]                           │
│     focus / accept_when / reject_when            │
│                                                  │
│   Reviewer 3: [角色名]                           │
│     focus / accept_when / reject_when            │
├──────────────────────────────────────────────────┤
│ Idea Evaluation Adaptation                       │
│   核心问题: "如果这个 idea 被正确执行，              │
│            产出的论文能发这个会议吗?"               │
└──────────────────────────────────────────────────┘
```

### 在 Module B 中的使用方式

```
/idea-screen "ideas" -- venue: ICML
         │
         ▼
读取 venue-profiles/ICML.md
         │
         ├── 提取 Calibration Tiers → 注入审稿 Prompt
         ├── 提取 Reviewer Profiles → 定义 3 位审稿人角色
         └── 提取 Verdict Options  → 限定评分选项
         │
         ▼
构造中文审稿 Prompt → gpt-5.4 (xhigh)
         │
         ▼
3 位审稿人独立评审 + Meta Review
```

> **Fallback**: 若 Profile 文件不存在，自动使用内置的通用 "Top ML Venue" 配置。
> **`-- venue: all`**: 同时使用所有可用 Profile 进行对比评审。
