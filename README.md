# EAR — Effective Auto Research

An automation toolkit for the full research workflow. It currently contains two independent, standalone subprojects:

| Subdirectory | What it does |
|---|---|
| **[`autovibeidea/`](autovibeidea/)** | **From research direction to proposal.** Literature survey → critical analysis → idea generation → multidimensional screening → in-depth refinement, producing an actionable, venue-ready proposal |
| **[`rebuttal/`](rebuttal/)** | **From reviews to responses.** Given a paper and its reviews, produces a response to each reviewer and a comment to the AC. Designed for EMNLP / ACL Rolling Review |

Together they cover both ends of the research cycle—topic selection and plan development **before submission**, and responding to reviews **after submission**. They share the design principles of "independent review by an external model + traceable evidence + no fabricated numbers or citations." Clone this repository once and choose either subproject; root-level scripts provide shared setup and safety checks.

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

Live pipelines are supported on Linux / WSL2 with Bash, Python 3.10+ and an authenticated
Codex CLI. The autovibeidea tools use the Python standard library; rebuttal additionally needs:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r rebuttal/requirements.txt
npm install -g @openai/codex
codex login
python3 scripts/doctor.py --component autovibeidea  # local checks only
```

For rebuttal, configure DeepSeek as described in its README, then use `--component rebuttal`.
The doctor does not verify authentication, model access, or endpoint availability.

### autovibeidea — Find Ideas

```bash
cd autovibeidea
./run.sh --allow-network --daemon "your research direction" NeurIPS
./run.sh --status                                     # check progress
```

Produces `outputs/LANDSCAPE.md` (literature map + gap matrix), `outputs/CRITICAL_ANALYSIS.md` (critique list),
`outputs/SCREENING_RANKED.md` (multidimensional score ranking), and `refine-logs/FINAL_PROPOSAL.md` (final proposal).

See [`autovibeidea/README.md`](autovibeidea/README.md) for details.

### rebuttal — Write a Rebuttal

Given a paper and its reviews, runs an 18-stage materialized pipeline and passes four gates to produce the responses.
See [`rebuttal/README.md`](rebuttal/README.md) for details.

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

- **External models serve as reviewers.** Generation and review are separated to prevent inflated self-evaluation.
- **Evidence is traceable.** Every claim must point back to literature, code, or experimental records.
- **No fabrication.** Do not invent experimental numbers or citations; if a search finds nothing, record that it found nothing.
- **Degrade without stopping.** When an external dependency is unavailable, automatically degrade and record the event; the pipeline does not stop to wait for a person.

---

## License

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu.
See [LICENSE](LICENSE).
