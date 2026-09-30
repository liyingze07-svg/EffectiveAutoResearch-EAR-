The repository's `SKILL.md` files were originally written for an agent environment supporting the Skill / Agent tools. When the runtime environment is Codex CLI, follow these compatibility rules:

1. There is no `Skill` tool.
When instructed to "invoke `/lit-survey`," "invoke `/idea-gen`," "invoke `/idea-screen`," or "invoke `/idea-refine`," do not stop and do not emit the instruction as ordinary text.
Read the corresponding `skills/<name>/SKILL.md` directly, then continue executing its equivalent steps in the current Codex session.

2. There is no `Agent` tool.
When subagents or parallel work are required, complete the work sequentially in the current session and record the degradation in `outputs/PIPELINE_LOG.md`.

3. There are no `mcp__codex__codex` / `mcp__codex__codex-reply` tools.
These calls mean that "an independent external review / verification / continuation is required."
In Codex-only mode, the current Codex session performs this step directly by default while maintaining continuity of context.
If `CODEX_MODE=gpt-api`, `tools/gpt_call.sh` is available, and an API key is available, you may use it to simulate an additional thread; otherwise, continue in the current session and do not stop because MCP is missing.

If `CODEX_MODE=codex-cli`, use `bash tools/codex_call.sh --thread <file> --output <file> --prompt "..."` instead.
It uses the local `codex exec` to provide equivalent new/continued-thread semantics and requires no API key.
MCP availability depends on the host agent and installed CLI capabilities; the shell entry points do not require MCP.

4. A background `codex exec` may lack native `WebSearch / WebFetch`.
If native web search is unavailable, use shell equivalents for online retrieval, such as:
- `python3 tools/arxiv_fetch.py search "query" --max 10`
- Fetch public webpages or APIs with `curl` / `wget`.
- When necessary, visit arXiv, Semantic Scholar, conference information pages, and project homepages.
Do not stop because the native WebSearch tool is missing; prioritize preserving the pipeline artifacts and chain of evidence.

5. Prioritize automation.
The entire pipeline must not wait for user input. At any checkpoint, write the decision to `outputs/PIPELINE_LOG.md` and continue.
Respect the launcher's execution policy: shell networking and live search are disabled unless the user
selected `--allow-network`; sandbox bypass requires an explicit `--unsafe`. A denied action is not
permission to change sandbox settings or relaunch unrestricted. Record blocked retrieval and degraded
evidence coverage; do not describe cached or unavailable retrieval as a fresh search.

6. Preserve the established artifact paths.
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

7. All reports and logs must be written in English; technical terms may remain in their original English form.
