# Pipeline Log（节选）

**起始时间**: 2026-05-07T16:31:12Z
**研究方向**: LLM-as-a-Judge 的偏差、校准与社会选择理论
**目标会场**: EMNLP 2026
**外部模型**: gpt-5.5 (xhigh reasoning) via Codex MCP

> 节选说明：原日志 164 行，此处保留阶段边界、自主决策与耗时；用户给定的方向草稿、
> 各 idea 的机制描述已裁剪。

## [16:35Z] Phase 1 Complete: Literature Survey
- 检索到论文并识别 8 个 gap，写入 `LANDSCAPE.md` / `LANDSCAPE.json`
- **Auto-decision**: 进入 Phase 2，将 8 个 gap 全数传入 critique manifest
- 阶段耗时：约 4 分钟

## [16:55Z] Phase 2 Complete: Idea Generation
- Phase 2a: critique manifest — **16 条批判，覆盖四个维度**（CRITIQUE-01..16）
- Phase 2b: **10 个批判锚定的 idea**，每个带 theorem/conjecture scaffold
- Phase 3-5 过滤：**6 个存活**（Researcher-Fit ≥14/20 + anti-pattern 可接受）
- **Auto-decision**: 为节省时间，先对 top 4 跑 venue simulation
- 阶段耗时：约 20 分钟

## [17:15Z] Phase 3 Complete: Idea Screening
- Module A: 重用 Phase 1 的 lit-survey 数据 + 跨模型验证
- Module B: EMNLP 2026 审稿模拟（3 审稿人 + meta review）
- Module C: 战略契合 5 维
- 阶段耗时：约 20 分钟

## [17:25Z] Phase 4 Complete: Final Discovery Report
- **Auto-decision**: 不调用 `/idea-refine`（本次目标只是"找 idea"）

## [次日 00:35Z] Phase 3 Re-run: 全量 6 个 idea 重新筛选
- 起因：首轮只筛了 top 4，且怀疑首轮查新覆盖不足
- 结果：**两个 idea 的 novelty 被下调（8→4、8→5）**，一个从 CAUTION 变为 ABANDON
- 详见 `SCREENING_RANKED.excerpt.md` 的"关键调整说明"

## [01:30Z] Phase 4-5: idea-refine 并行执行
- 每个 idea 跑完整精炼：Phase 0 (anchor) → 0.5 (skeleton) → 1 (initial) → 2 (review) → 3 (refine) → 4 (re-eval) → 5.5 (expansion)
- 产出 `round-3-expanded.md` 等（**本示例未包含，属裁剪内容**）

## [02:30Z] Phase 6: 更大范围的撞车/抢发检查
## [03:00Z] Phase 7: 知识固化
