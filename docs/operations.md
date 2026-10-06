# Operations, review records and data handling

Run commands from the EAR repository root unless a workflow guide says otherwise. For first use, see [Getting started](getting-started.md).

## Review mechanisms and process records

### Separate sessions and different model families are distinct configurations

AutoVibeIdea's `--codex-cli` route uses the local login to request review in separate Codex sessions. Separate sessions can reduce shared context between generation and review, but they do not imply different models or providers, nor fully independent judgments.

AutoRebuttal's cross-family consensus mode combines Codex and DeepSeek. The distinction is not merely between sessions: different model families participate in review.

### Review fallbacks are marked

In AutoVibeIdea's shell workflow, evaluation may take place in the same session that generates ideas when no review route is explicitly selected. Failed review calls may also trigger a fallback to self-evaluation.

Run logs and degradation markers distinguish these cases. When reading rankings or review outcomes, consult these records to understand which review path was actually used, rather than relying only on a final score or pass status.

### Connect key claims to evidence

EAR's workflows require key claims to be linked to literature, code, or experimental records. Literature analysis, research proposals, and rebuttals should be organized around the available materials.

Prompts and checks instruct models to reject unsupported numbers and citations. Missing evidence should be recorded explicitly rather than filled in with invented content. Evidence tracing and missing-evidence markers preserve the basis of the text, helping readers trace drafts back to their sources.

### Degradation does not expand execution permissions

When some dependencies are unavailable, the workflow can use a documented fallback. Self-evaluation and single-family review provide weaker assurance and should remain distinguishable from the intended review configuration.

A safety denial from a model or tool does not automatically trigger unrestricted execution and is not a reason to expand permissions.

---

## Advanced Execution and Configuration

### Isolated offline checks on Linux

To run the offline demo with operating-system-level isolation, install `bubblewrap`, then run this from the EAR repository root:

```bash
bash scripts/isolated_demo.sh
```

The script mounts the checkout read-only, clears the environment, hides the host home directory, and disables networking. Only the printed output directory is writable on the host.

This is an **offline demo runner** for isolated workflow checks, not a container environment for live model calls.

<a id="execution-safety-and-data-handling"></a>

### Model services and network access

Live runs send prompts and relevant input and tool content to the configured services.

| Workflow | Services used |
| --- | --- |
| AutoVibeIdea | Codex / OpenAI, with the OpenAI API as an optional route |
| AutonomousMath | Codex / OpenAI or Claude / Anthropic; terminal-review route is configurable |
| AutoRebuttal | Codex / OpenAI and DeepSeek, or explicitly configured endpoints |
| Enabled web search and MCP integrations | May contact additional external services |

The default agent shell policy for AutoVibeIdea and AutoRebuttal is:

| Setting | Default behavior |
| --- | --- |
| Sandbox mode | `workspace-write` |
| Unattended approval policy | `never` |
| Shell network access | Disabled |

AutoVibeIdea's `--allow-network` also enables live web search. Shell network restrictions do not block CLI-to-model API traffic or direct verifier/API calls.

AutonomousMath's Codex research worker defaults to `workspace-write` with shell
network access enabled for literature and novelty checks; its JSON configuration
can set `network_access=false`. Terminal Codex reviews use fresh read-only sessions.
Claude execution uses its CLI tool permissions; see the AutonomousMath guide.

`workspace-write` limits writes, but it is not a confidentiality boundary: the CLI may still read host files that its permissions allow, and MCP tools have their own permissions.

`--unsafe` allows unrestricted execution and should be used only in a disposable, externally isolated environment.

[Read the official configuration reference →](https://learn.chatgpt.com/docs/config-file/config-reference)

### Local outputs and session records

`outputs/`, `refine-logs/`, rebuttal campaign directories, archives, API conversation JSON files, and CLI session history may contain input materials and model responses.

API conversation files are retained to support resuming a conversation; temporary response and event files are cleaned up. New output files created by the launchers use private permissions. Provider-side retention depends on the account and service provider settings.

### Pre-commit checks

EAR provides a shared secret scanner covering all subprojects.

After `git add` and before committing, run this from the repository root:

```bash
python3 scripts/secret_scan.py --staged
```

This scans the contents of Git's staged files. Omit `--staged` to inspect tracked and unignored worktree files:

```bash
python3 scripts/secret_scan.py
```

The older `rebuttal/scripts/secret_scan.sh` command delegates to the same scanner. Reports do not display matched contents. Detection uses heuristics and is not equivalent to a complete security audit.

---


## Where outputs live

| Entry | Output location |
| --- | --- |
| Direct AutoVibeIdea launcher | `autovibeidea/outputs/`, `autovibeidea/refine-logs/` |
| EAR idea launcher with `--workspace` | The selected workspace contains its own idea runner and output directories. |
| AutonomousMath | The explicit `--workspace` holds state, episode artifacts and reviews. |
| Direct AutoRebuttal launcher | `rebuttal/campaigns/<case>/` and `rebuttal/papers/<case>/` |
| EAR rebuttal initialization | The selected workspace contains the case inputs, contracts and campaign artifacts. |

Use `workspaces/` (ignored by this checkout) or a path outside the repository for live runs. Follow the [workspace commands](getting-started.md#workspaces-and-run-control) to inspect or stop work.
