---
name: Bug report
about: Unexpected behavior in a pipeline stage
labels: bug
---

**Stage / skill**
(For example, `/idea-gen` Phase 2a or `tools/arxiv_fetch.py`)

**Execution mode**
- [ ] Codex MCP
- [ ] `--gpt-only` (`CODEX_MODE=gpt-api`)
- [ ] Direct Codex CLI run
- Model: (for example, gpt-5.4)

**Expected behavior / actual behavior**

**Degradation record**
Does `outputs/PIPELINE_LOG.md` contain a `⚠️` degradation entry? Paste it here. (When the external model is unavailable, the pipeline automatically degrades to self-review, which affects the scores.)

**Steps to reproduce**

**Note**: Do not paste unpublished research content. Use publicly available, published research directions in examples.
