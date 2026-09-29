---
name: lit-survey
description: Search and analyze research papers across multiple sources to build a landscape map with identified gaps. Use when user says "literature survey", "文献调研", "find papers", "landscape map", "related work", "survey", or needs to understand the current state of a research area.
argument-hint: [research-topic]
allowed-tools: Bash(*), Read, Glob, Grep, WebSearch, WebFetch, Write, Agent, mcp__zotero__*, mcp__obsidian-vault__*
---

# Literature Survey — Landscape Mapping & Gap Identification

Research topic: $ARGUMENTS

## Constants

- **PAPER_LIBRARY** — Local directory containing user's paper collection (PDFs). Check these paths in order:
  1. `papers/` in the current project directory
  2. `literature/` in the current project directory
  3. Custom path specified by the user
- **MAX_LOCAL_PAPERS = 20** — Maximum number of local PDFs to scan (read first 3 pages each). If more are found, prioritize by filename relevance to the topic.
- **ARXIV_DOWNLOAD = false** — When `true`, download top 3-5 most relevant arXiv PDFs to PAPER_LIBRARY after search. When `false` (default), only fetch metadata (title, abstract, authors) via arXiv API — no files are downloaded.
- **ARXIV_MAX_DOWNLOAD = 5** — Maximum number of PDFs to download when `ARXIV_DOWNLOAD = true`.

> Overrides:
> - `/lit-survey "topic" -- paper library: ~/my_papers/` — custom local PDF path
> - `/lit-survey "topic" -- sources: zotero, local` — only search Zotero + local PDFs
> - `/lit-survey "topic" -- sources: zotero` — only search Zotero
> - `/lit-survey "topic" -- sources: web` — only search the web (skip all local)
> - `/lit-survey "topic" -- arxiv download: true` — download top relevant arXiv PDFs
> - `/lit-survey "topic" -- arxiv download: true, max download: 10` — download up to 10 PDFs

## Data Sources

This skill checks multiple sources **in priority order**. All are optional — if a source is not configured or not requested, skip it silently.

### Source Selection

Parse `$ARGUMENTS` for a `-- sources:` directive:
- **If `-- sources:` is specified**: Only search the listed sources (comma-separated). Valid values: `zotero`, `obsidian`, `local`, `web`, `all`.
- **If not specified**: Default to `all` — search every available source in priority order.

Examples:
```
/lit-survey "diffusion models"                        → all (default)
/lit-survey "diffusion models" -- sources: all         → all
/lit-survey "diffusion models" -- sources: zotero      → Zotero only
/lit-survey "diffusion models" -- sources: zotero, web → Zotero + web
/lit-survey "diffusion models" -- sources: local       → local PDFs only
/lit-survey "topic" -- sources: obsidian, local, web   → skip Zotero
```

### Source Table

| Priority | Source | ID | How to detect | What it provides |
|----------|--------|----|---------------|-----------------|
| 1 | **Zotero** (via MCP) | `zotero` | Try calling any `mcp__zotero__*` tool — if unavailable, skip | Collections, tags, annotations, PDF highlights, BibTeX, semantic search |
| 2 | **Obsidian** (via MCP) | `obsidian` | Try calling any `mcp__obsidian-vault__*` tool — if unavailable, skip | Research notes, paper summaries, tagged references, wikilinks |
| 3 | **Local PDFs** | `local` | `Glob: papers/**/*.pdf, literature/**/*.pdf` | Raw PDF content (first 3 pages) |
| 4 | **Web search** | `web` | Always available (WebSearch) | arXiv, Semantic Scholar, Google Scholar |

> **Graceful degradation**: If no MCP servers are configured, the skill works perfectly well with local PDFs + web search alone. Zotero and Obsidian are pure additions — their absence never causes a failure.

## Workflow

### Step 0a: Search Zotero Library (if available and requested)

**Skip this step entirely if Zotero MCP is not configured or `zotero` is excluded by `-- sources:`.**

Try calling a Zotero MCP tool (e.g., search). If it succeeds:

1. **Search by topic**: Use the Zotero search tool to find papers matching the research topic.
2. **Read collections**: Check if the user has a relevant collection/folder for this topic.
3. **Extract annotations**: For highly relevant papers, pull PDF highlights and notes — these represent what the user found important.
4. **Export BibTeX**: Get citation data for relevant papers.
5. **Compile results**: For each relevant Zotero entry, extract:
   - Title, authors, year, venue
   - User's annotations/highlights (if any)
   - Tags the user assigned
   - Which collection it belongs to

> Zotero annotations are gold — they show what the user personally highlighted as important, which is far more valuable than generic summaries.

> Zotero/Obsidian tools may have different names depending on how the user configured the MCP server (e.g., `mcp__zotero__search` or `mcp__zotero-mcp__search_items`). Try the most common patterns and adapt.

### Step 0b: Search Obsidian Vault (if available and requested)

**Skip this step entirely if Obsidian MCP is not configured or `obsidian` is excluded by `-- sources:`.**

Try calling an Obsidian MCP tool (e.g., search). If it succeeds:

1. **Search vault**: Search for notes related to the research topic.
2. **Check tags**: Look for notes tagged with relevant topics (e.g., `#diffusion-models`, `#paper-review`).
3. **Read research notes**: For relevant notes, extract the user's own summaries and insights.
4. **Follow links**: If notes link to other relevant notes (wikilinks), follow them for additional context.
5. **Compile results**: For each relevant note:
   - Note title and path
   - User's summary/insights
   - Links to other notes (research graph)
   - Any frontmatter metadata (paper URL, status, rating)

> Obsidian notes represent the user's **processed understanding** — more valuable than raw paper content for understanding their perspective.

### Step 0c: Scan Local Paper Library (if requested)

**Skip if `local` is excluded by `-- sources:`.**

Before searching online, check if the user already has relevant papers locally:

1. **Locate library**: Check PAPER_LIBRARY paths for PDF files.
   ```
   Glob: papers/**/*.pdf, literature/**/*.pdf
   ```

2. **De-duplicate against Zotero**: If Step 0a found papers, skip any local PDFs already covered by Zotero results (match by filename or title).

3. **Filter by relevance**: Match filenames and first-page content against the research topic. Skip clearly unrelated papers.

4. **Summarize relevant papers**: For each relevant local PDF (up to MAX_LOCAL_PAPERS):
   - Read first 3 pages (title, abstract, intro)
   - Extract: title, authors, year, core contribution, relevance to topic
   - Flag papers that are directly related vs tangentially related

5. **Build local knowledge base**: Compile summaries into a "papers you already have" section. This becomes the starting point — external search fills the gaps.

> If no local papers are found, skip to Step 1. If the user has a comprehensive local collection, the external search can be more targeted (focus on what's missing).

### Step 1: Web Search (if requested)

**Skip if `web` is excluded by `-- sources:`.**

- Use WebSearch to find recent papers on the topic.
- Check arXiv, Semantic Scholar, Google Scholar.
- Focus on papers from last 2 years unless studying foundational work.
- **De-duplicate**: Skip papers already found in Zotero, Obsidian, or local library.

**arXiv API search** (always runs within this step, no download by default):

Locate the fetch script and search arXiv directly:
```bash
# Try to find arxiv_fetch.py
SCRIPT=$(find tools/ -name "arxiv_fetch.py" 2>/dev/null | head -1)
# If not found, check common install locations
[ -z "$SCRIPT" ] && SCRIPT=$(command -v arxiv_fetch.py 2>/dev/null)

# Search arXiv API for structured results (title, abstract, authors, categories)
python3 "$SCRIPT" search "QUERY" --max 10
```

If `arxiv_fetch.py` is not found, fall back to WebSearch for arXiv (same results, less structured).

The arXiv API returns structured metadata (title, abstract, full author list, categories, dates) — richer than WebSearch snippets.

> **arXiv 可靠性**：`tools/arxiv_fetch.py` 已对 406/429/5xx 做退避重试，但实测在部分网络环境下
> arXiv 会对**新查询**持续返回 406（节流），数分钟内不恢复。遇到这种情况：**直接改用 WebSearch
> 作为本轮主检索源**，不要反复重试，并把降级记入 `outputs/PIPELINE_LOG.md`。 Merge these results with WebSearch findings and de-duplicate.

**Search failure handling (autonomous mode)**:
- If a single WebSearch query fails: retry once with a different query formulation
- If the retry also fails: log the failure and move to the next query
- If arXiv API (`arxiv_fetch.py`) fails: fall back to WebSearch with "arxiv [topic]" queries
- If ALL web searches fail (e.g., network unavailable):
  1. Build the landscape map using the agent's training knowledge of the research area
  2. Clearly mark the output: "⚠️ OFFLINE MODE: This landscape was built from model training knowledge, not live search. Papers listed are real but may not include the most recent (2025-2026) publications."
  3. Continue pipeline normally — do NOT stop or ask the user
  4. The downstream skills can still use this landscape for idea generation and screening

**Semantic Scholar**: Also search via WebSearch with site:semanticscholar.org or the Semantic Scholar API if available. Semantic Scholar provides citation counts, influential citations, and TLDR summaries.

**Optional PDF download** (only when `ARXIV_DOWNLOAD = true`):

After all sources are searched and papers are ranked by relevance:
```bash
# Download top N most relevant arXiv papers
python3 "$SCRIPT" download ARXIV_ID --dir papers/
```
- Only download papers ranked in the top ARXIV_MAX_DOWNLOAD by relevance.
- Skip papers already in the local library.
- 1-second delay between downloads (rate limiting).
- Verify each PDF > 10 KB.

### Step 2: Analyze Each Paper

For each relevant paper found (from all sources combined), extract:

- **Paper ID**: Assign a short ID (e.g., `P01`, `P02`, ...) for cross-referencing in later steps.
- **Problem**: What gap does it address?
- **Method**: Core technical contribution (1-2 sentences).
- **Results**: Key numbers/claims.
- **Limitations**: Stated or inferred limitations of the approach.
- **Relevance**: How does it relate to the research topic?
- **Source**: Where we found it (Zotero/Obsidian/local/web) — helps the user know what they already have vs what is new.
- **Citation info**: Authors, year, venue, DOI/URL.

Aim for 15-30 papers total across all sources. If fewer than 10 papers are found, broaden the search terms. If more than 40, tighten the relevance filter.

### Step 3: Synthesize & Identify Gaps

#### 3a: Thematic Synthesis

- Group papers by approach/theme. Identify 3-7 major themes.
- For each theme, note:
  - Dominant approach or paradigm
  - Number of papers in the theme
  - Key consensus findings
  - Disagreements or open debates
  - Status: `active` (papers in last 2 years), `mature` (well-established, few new papers), `emerging` (1-2 papers, recent)
- If Obsidian notes exist, incorporate the user's own insights into the synthesis.
- Identify consensus vs disagreements in the field.

#### 3b: Gap Identification Matrix

After the thematic synthesis, systematically identify research gaps. For each gap, classify it by type and assign a confidence level.

**Gap Types** (enum — use exactly these labels):
- `cross-domain transfer` — A technique proven in domain A has not been applied to domain B, where it plausibly could work.
- `untested assumption` — A widely-held assumption in the field lacks direct empirical validation.
- `resolution opportunity` — Two contradictory findings in the literature can be resolved by a new experiment or formulation.
- `scaling frontier` — An approach works at small scale but has not been tested at larger/different scales.
- `missing diagnostic` — The field lacks a standard benchmark, metric, or diagnostic tool for a key question.
- `overlooked formulation` — An alternative mathematical or conceptual formulation has been ignored.

**Confidence Levels**:
- `HIGH` — Multiple papers corroborate the gap's existence; clear evidence of absence.
- `MEDIUM` — 1-2 papers hint at the gap; reasonable inference from the literature.
- `LOW` — Speculative; the gap is inferred from absence of evidence rather than evidence of absence.

Produce the following matrix (included in the final output):

```markdown
## Gap Identification Matrix

| Gap ID | Gap Description | Evidence (papers) | Gap Type | Confidence |
|--------|----------------|-------------------|----------|------------|
| G1     | [Concise description of the gap] | [P01], [P07] | cross-domain transfer | HIGH |
| G2     | [Concise description of the gap] | [P03], [P12], [P15] | untested assumption | MEDIUM |
| G3     | ... | ... | ... | ... |
```

Aim for 5-15 gaps. Prioritize HIGH and MEDIUM confidence gaps. Include LOW confidence gaps only when they are particularly interesting or novel.

### Step 4: Output — Landscape Map

Create the `outputs/` directory if it does not exist:
```bash
mkdir -p outputs
```

#### 4a: `outputs/LANDSCAPE.md`

Write a comprehensive Markdown file with the following structure:

```markdown
# Literature Landscape: [Research Topic]

**Date**: [YYYY-MM-DD]
**Papers analyzed**: [N]
**Sources**: [list of sources used]

## Executive Summary

[2-3 paragraph overview of the field's current state, key trends, and most significant gaps.]

## Paper Table

| ID | Paper | Authors | Year | Venue | Method | Key Result | Relevance | Source |
|----|-------|---------|------|-------|--------|------------|-----------|--------|
| P01 | ... | ... | ... | ... | ... | ... | ... | Zotero |
| P02 | ... | ... | ... | ... | ... | ... | ... | web |

## Thematic Analysis

### Theme 1: [Theme Name]
**Status**: active | mature | emerging
**Dominant approach**: [brief description]
**Papers**: P01, P05, P12

[2-3 paragraph discussion of this theme, key findings, and debates.]

### Theme 2: [Theme Name]
...

## Gap Identification Matrix

| Gap ID | Gap Description | Evidence (papers) | Gap Type | Confidence |
|--------|----------------|-------------------|----------|------------|
| G1     | ... | [P01], [P07] | cross-domain transfer | HIGH |
| G2     | ... | ... | ... | ... |

## Trajectory Analysis

[If trajectory tracing was performed (see Step 4c below), include it here.
Otherwise, note: "Trajectory tracing was not performed. Run with `-- trace: true` to enable."]

## References

[Full citation list in a consistent format. If Zotero BibTeX was exported, include a `references.bib` snippet.]
```

#### 4b: `outputs/LANDSCAPE.json`

Write a machine-readable JSON file for consumption by downstream skills (`/idea-gen`, `/idea-screen`, `/idea-pipeline`):

```json
{
  "topic": "[research topic as provided by user]",
  "date": "[YYYY-MM-DD]",
  "paper_count": 25,
  "sources_used": ["zotero", "local", "web"],
  "papers": [
    {
      "id": "P01",
      "title": "...",
      "authors": ["Author A", "Author B"],
      "year": 2025,
      "venue": "NeurIPS",
      "method": "...",
      "key_result": "...",
      "relevance": "...",
      "source": "zotero",
      "url": "https://...",
      "themes": ["Theme A"]
    }
  ],
  "themes": [
    {
      "name": "Theme A",
      "papers": ["P01", "P05", "P12"],
      "status": "active",
      "dominant_approach": "...",
      "summary": "..."
    }
  ],
  "gaps": [
    {
      "id": "G1",
      "description": "...",
      "type": "cross-domain transfer",
      "evidence_papers": ["P01", "P07"],
      "confidence": "HIGH"
    }
  ],
  "trajectory": {
    "performed": false,
    "top_authors": [],
    "coauthor_clusters": []
  }
}
```

Validate the JSON is well-formed before writing. Use `python3 -c "import json; json.load(open('outputs/LANDSCAPE.json'))"` to verify.

#### 4c: Trajectory Tracing (optional, if time permits)
#### 4b-2: Claim Stance Table 与 Failure Modes（可选扩展字段）

这两组字段供 `/idea-gen` Phase 2a 的**高熵区域**与**失效模式**挖掘使用。若跳过，`idea-gen` 仍按原四维批判运行，不受影响。

在 `outputs/LANDSCAPE.json` 中追加：

```json
"claims": [
  {"id": "C1", "statement": "领域中被反复检验的一条具体主张",
   "observations": [
     {"paper": "P01", "stance": "supports",
      "setting": {"dataset": "GSM8K", "scale": "7B", "metric": "accuracy"}},
     {"paper": "P04", "stance": "refutes",
      "setting": {"dataset": "GSM8K", "scale": "7B", "metric": "accuracy"}}
   ]}
],
"papers": [
  {"id": "P01", "limitations": ["在长上下文（>8k tokens）下性能显著退化"],
   "negative_results": ["多数投票在数学题外无增益"]}
]
```

规则：

1. **`stance` 只能取 `supports` / `refutes` / `conditional`。**
2. **`setting` 必填 `dataset` / `scale` / `metric` 三项**，未知写 `"unknown"`。这三项决定可比性惩罚——缺失会被按"未记录"扣分，因为在不同设定下得到不同结论不构成领域分歧。
3. 只为**至少被 2 篇论文直接检验过**的主张建 claim。单篇主张无法形成分歧。
4. `limitations` / `negative_results` 从论文的 limitations 小节、negative results、附录中"我们观察到在 X 条件下退化"一类表述中抽取，**保留原始条件描述**（规模阈值、数据类型、任务族），不要概括成"性能有限"。

然后执行：

```bash
python3 tools/entropy_map.py outputs/LANDSCAPE.json           # 人读报告
python3 tools/entropy_map.py outputs/LANDSCAPE.json --json > outputs/ENTROPY_MAP.json
```

把报告中的**高熵区域**与**跨论文失效模式**摘要写入 `outputs/LANDSCAPE.md` 的新小节 `## 高熵区域与失效模式`。对被标为**伪冲突嫌疑**（高熵但低可比性）的 claim，必须在该小节注明它们已被排除及原因。


After the main search is complete and the core outputs are written, perform trajectory tracing to identify where the field is heading. This step is optional — skip it if the user signals time pressure or if the paper set is too small (fewer than 10 papers).

**Enable explicitly** with `-- trace: true` in the arguments, or perform automatically if the search yielded 15+ papers and no time constraint is indicated.

1. **Identify top authors**: From the analyzed papers, find the 3 most-cited or most-recurring authors.

2. **Trace publication arcs**: For each top author, use WebSearch to find their publications from the last 3 years. Identify:
   - What topics they are moving toward
   - What topics they are moving away from
   - Any new collaborations or lab changes

3. **Map co-author clusters**: From the paper set, build a rough co-authorship graph:
   - Identify 2-4 distinct research groups (clusters of authors who frequently co-publish)
   - Note if groups are converging on similar approaches or diverging
   - Flag any cross-group collaborations (potential convergence signals)

4. **Add to outputs**: Update `outputs/LANDSCAPE.md` with a "Trajectory Analysis" section and update the `trajectory` field in `outputs/LANDSCAPE.json`:

```json
"trajectory": {
  "performed": true,
  "top_authors": [
    {
      "name": "Author Name",
      "affiliation": "University/Lab",
      "recent_focus": "...",
      "direction": "moving from X toward Y",
      "key_recent_papers": ["title1", "title2"]
    }
  ],
  "coauthor_clusters": [
    {
      "label": "Group A (MIT)",
      "members": ["Author1", "Author2", "Author3"],
      "focus": "...",
      "relationship_to_other_groups": "competing with Group B on approach X"
    }
  ]
}
```

## Key Rules

- **所有输出使用中文。** LANDSCAPE.md 中的 Executive Summary、主题分析、Gap 描述均使用中文撰写。论文标题、作者名、会议名保留英文。LANDSCAPE.json 中的 description 字段也使用中文。
- Always include paper citations (authors, year, venue).
- Distinguish between peer-reviewed papers and preprints (mark preprints explicitly).
- Be honest about limitations of each paper.
- Note if a paper directly competes with or supports the user's likely approach.
- **Never fail because an MCP server is not configured** — always fall back gracefully to the next data source.
- If no papers are found from any source, report that clearly rather than inventing results.
- Paper IDs (P01, P02, ...) and Gap IDs (G1, G2, ...) must be consistent across the Markdown and JSON outputs.
- The JSON output must be valid JSON. Always verify before finishing.
- Write outputs to the `outputs/` directory relative to the current project root.

## Composing with Other Skills

This skill is the starting point for research ideation workflows:

```
/lit-survey "direction"    -> landscape map + gaps
/idea-gen "direction"      -> generates ideas using this landscape
/idea-screen               -> screens ideas against this landscape
/idea-pipeline             -> full workflow starting from this skill
```

The `outputs/LANDSCAPE.json` file is the primary handoff artifact. Downstream skills (`/idea-gen`, `/idea-screen`) read this file to ground their work in the actual state of the literature. When running `/idea-pipeline`, this skill executes first and its outputs feed automatically into the subsequent stages.
