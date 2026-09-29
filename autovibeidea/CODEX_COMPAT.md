本仓库的 `SKILL.md` 最初为 Claude Code 工作流编写。当前运行环境改为 Codex CLI 时，请按下面的兼容规则执行：

1. 没有 `Skill` 工具。
遇到“调用 `/lit-survey`”“调用 `/idea-gen`”“调用 `/idea-screen`”“调用 `/idea-refine`”时，不要停下来，也不要把它当成普通文本输出。
请直接读取对应的 `skills/<name>/SKILL.md`，然后在当前 Codex 会话中继续执行其等价步骤。

2. 没有 `Agent` 工具。
需要子代理或并行时，在当前会话中串行完成，并把降级记录到 `outputs/PIPELINE_LOG.md`。

3. 没有 `mcp__codex__codex` / `mcp__codex__codex-reply` 工具。
这些调用表示“需要一次独立的外部审阅/复核/续写”。
在 Codex-only 模式下，默认由当前 Codex 会话直接承担这一步，并保持前后文连续。
如果环境变量 `CODEX_MODE=gpt-api` 且 `tools/gpt_call.sh` 可用、API key 可用，你可以选择用它模拟额外 thread；否则继续当前会话，不要因为缺少 MCP 而中止。

若 `CODEX_MODE=codex-cli`，改用 `bash tools/codex_call.sh --thread <file> --output <file> --prompt "..."`。
它用本机 `codex exec` 提供等价的新建/续写线程语义，无需 API key。
**注意 codex CLI ≥0.158.0 已移除 `mcp-server` 子命令**，因此 `mcp__codex__*` 工具在新版环境下必然不可用，这是预期情况，不是故障。

4. 后台 `codex exec` 可能没有原生 `WebSearch / WebFetch`。
如果原生网页搜索不可用，请用 shell 等价完成联网检索，例如：
- `python3 tools/arxiv_fetch.py search "query" --max 10`
- `curl` / `wget` 抓取公开网页或 API
- 必要时访问 arXiv、Semantic Scholar、会议信息页、项目主页
不要因为缺少原生 WebSearch 工具而中止；优先保住 pipeline 的产物和证据链。

5. 自动化优先。
整个 pipeline 不要等待用户输入；遇到需要 checkpoint 的地方，把决策写入 `outputs/PIPELINE_LOG.md`，然后继续。

6. 保持既定产物路径。
- `outputs/LANDSCAPE.md`
- `outputs/LANDSCAPE.json`
- `outputs/CRITICAL_ANALYSIS.md`
- `outputs/IDEAS_RAW.md`
- `outputs/IDEAS_FILTERED.md`
- `outputs/SCREENING_REPORT.md`
- `outputs/SCREENING_RANKED.md`
- `outputs/IDEA_DISCOVERY_REPORT.md`
- `outputs/PIPELINE_STATE.json`
- `refine-logs/*`

7. 所有报告与日志使用中文，技术术语可保留英文。
