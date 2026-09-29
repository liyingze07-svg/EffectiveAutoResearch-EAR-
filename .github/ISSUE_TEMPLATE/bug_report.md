---
name: Bug report
about: pipeline 某个阶段行为异常
labels: bug
---

**哪个阶段 / skill**
（如 `/idea-gen` Phase 2a、`tools/arxiv_fetch.py`）

**运行模式**
- [ ] Codex MCP
- [ ] `--gpt-only`（`CODEX_MODE=gpt-api`）
- [ ] Codex CLI 直跑
- 模型：（如 gpt-5.4）

**期望行为 / 实际行为**

**降级记录**
`outputs/PIPELINE_LOG.md` 里有没有 `⚠️` 降级条目？贴出来（外部模型不可用时会自动降级为自评，这会影响分数）。

**复现步骤**

**注意**：请不要粘贴尚未发表的研究内容，举例请用公开已发表的方向。
