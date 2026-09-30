# EAR — Effective Auto Research

An automation toolkit for research planning and rebuttal drafting. It contains two subprojects that can be run separately from a complete EAR checkout:

| Subdirectory | What it does |
|---|---|
| **[`autovibeidea/`](autovibeidea/)** | **From research direction to proposal draft.** Literature survey → critical analysis → idea generation → screening → refinement, producing a structured research plan for human evaluation |
| **[`rebuttal/`](rebuttal/)** | **From reviews to response drafts.** Given a paper and its reviews, drafts responses for the selected reviewers and a comment to the Area Chair (AC). Designed for EMNLP / ACL Rolling Review |

They support topic selection and plan development **before submission**, and responding to reviews **after submission**. They do not automate the entire research cycle or guarantee novelty, factual accuracy, or acceptance. Researchers remain responsible for checking sources, running necessary experiments, and approving anything submitted.

Clone this repository once and choose either subproject; root-level scripts provide shared setup and safety checks. Review separation and evidence tracing are design goals, with explicit limitations when model calls fail or the workflow falls back to self-evaluation.

---

## Quick Start

Start with the zero-cost check (Python 3.10+; no API key, Codex, or third-party Python packages):

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR
python3 scripts/doctor.py --offline
python3 scripts/offline_demo.py
```

Expected: `PASS: idea validation/report, five contracts, and synthetic rebuttal dry-run.`
The printed temporary directory contains `SUMMARY.json`, an idea search report and a synthetic
rebuttal campaign with `DRY_RUN.txt`. No model is called and no research/rebuttal quality is evaluated.
Use `--output outputs/first-demo` to keep results at a chosen **new** path; existing directories are refused.

For an OS-isolated offline check on Linux, install `bubblewrap` and run
`bash scripts/isolated_demo.sh`. It mounts this checkout read-only, clears the environment,
hides the host home directory and disables networking. Only the printed output directory is writable
on the host. This is an **offline demo runner**, not a container for live model calls.

### Choose a live pipeline

Both pipelines require Linux / WSL2, Bash, Python 3.10+ and an authenticated Codex CLI.
With Node.js and npm available, install and authenticate the shared driver:

```bash
npm install -g @openai/codex
codex login
```

Choose one path below; both start from the EAR repository root. Live calls use account quota
and may incur charges. The doctor checks local prerequisites, not authentication, model access,
or endpoint availability.

### autovibeidea — Find Ideas

```bash
python3 scripts/doctor.py --component autovibeidea
cd autovibeidea
./run.sh --allow-network --codex-cli --daemon "your research direction" NeurIPS
./run.sh --status                                     # check progress
# ./run.sh --stop                                     # cancel and clean up child processes
```

The recommended `--codex-cli` route requests review in separate Codex sessions using the local login;
it does not imply a different model or provider. Without an explicit review route, the shell workflow
may evaluate in the generating session. Failed review calls can also trigger self-evaluation;
inspect the run logs and degradation markers before interpreting scores.

Expected outputs include `outputs/LANDSCAPE.md` (literature map + gap matrix),
`outputs/SCREENING_RANKED.md` (model-generated ranking), and `refine-logs/FINAL_PROPOSAL.md`
(proposal draft). A successful process exit does not establish research quality.

See [`autovibeidea/README.md`](autovibeidea/README.md) for details.

### rebuttal — Write a Rebuttal

Install the Python dependencies and configure DeepSeek, then prepare a paper/review case.
The [AutoRebuttal quick start](rebuttal/README.md#install-and-run) walks through input preparation,
contract generation, a dry-run, a live run, and locating the response drafts.

The workflow has 18 stage prompts and four review gates. Its cross-family consensus mode uses
Codex and DeepSeek; single-family fallback is labeled and is not equivalent to cross-family approval.

---

## Execution safety and data handling

Live runs send prompts and relevant input/tool content to the configured services and may incur charges.
autovibeidea uses Codex/OpenAI, optionally the OpenAI API; rebuttal uses Codex/OpenAI and DeepSeek
(or explicitly configured provider endpoints). Enabled web search and MCP integrations may contact
additional services. Only supply papers, reviews, code and data you are authorized to send there.

The default agent shell policy is `workspace-write`, unattended approval policy `never`, and no
shell network access. autovibeidea's `--allow-network` also enables live web search. CLI-to-model API
traffic and direct verifier/API calls are **not** disabled by this shell policy. `--unsafe` explicitly
allows unrestricted execution; use it only inside a disposable, externally isolated environment.
Workspace-write is not a confidentiality boundary: it can still read host files allowed by the CLI,
and configured MCP tools have their own permissions. Do not run unfamiliar inputs beside sensitive files.
See [the official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

Local `outputs/`, `refine-logs/`, campaigns, archives, API thread JSON files and CLI session history
can contain submitted material and model responses. API thread files are retained to support resume;
temporary response/event files are cleaned up. New launcher output files use private permissions.
Provider-side retention depends on your account and provider settings; EAR cannot guarantee deletion.
Do not paste credentials or unpublished research in issues or upload raw logs without reviewing them.

Before committing, run `python3 scripts/secret_scan.py --staged` after `git add`. This scans staged
blobs across **both** subprojects; omit `--staged` to inspect tracked and unignored worktree files.
The older `rebuttal/scripts/secret_scan.sh` command delegates to the same scanner. Matches are reported
without their contents. This is heuristic detection, not a guarantee that no secret is present.

---

## Shared Design Principles

- **Separate generation and review where configured.** Separate sessions reduce shared context but do not guarantee independent judgments; cross-family review requires different providers.
- **Require traceable evidence.** Workflows ask claims to point back to literature, code, or experimental records. These checks assist, rather than replace, human verification.
- **Prohibit fabrication in the workflow.** Prompts and checks reject unsupported numbers and citations; model errors can still occur. Missing evidence should be recorded, not invented.
- **Make degradation visible.** Some unavailable dependencies allow a documented fallback. Self-evaluation and single-family review provide weaker assurance; safety denials do not authorize unrestricted execution.

---

## License

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu.
See [LICENSE](LICENSE).
