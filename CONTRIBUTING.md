# Contributing to EAR

Useful contributions make a research workflow easier to run, inspect or evaluate. A small reproducible failure or a clearly documented real case can be as valuable as a new feature.

## Report a problem

Open an [issue](https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-/issues) with the workflow, repository revision, Python/CLI versions, exact command, expected result and observed result. Include a minimal input and the relevant redacted error when possible. Keep credentials, private manuscripts, reviewer identities and account session records out of the issue.

For model-dependent behavior, record the provider/model, review route and any fallback markers. Distinguish an infrastructure failure, a failed model review and a content-quality concern.

## Make a focused change

Use a complete checkout. The shared launcher lives in `ear/`; research implementations remain in `autovibeidea/`, `autonomousmath/` and `rebuttal/`. Match the scope of the change to the affected module and keep existing entry points working.

Run the basic checks from the repository root:

```bash
python3 -m ear doctor --offline
python3 -m ear demo report
python3 -m ear demo check
python3 scripts/secret_scan.py
python3 scripts/public_source_audit.py
```

For AutonomousMath behavior changes, also run:

```bash
python3 -m unittest discover -s autonomousmath/tests -v
```

Use the affected module's documented checks for other code changes. Documentation-only changes need valid links, accurate commands and consistent claims; they do not require paid research episodes. Before committing staged files, run `python3 scripts/secret_scan.py --staged`.

Maintainers can enable the prepared [offline CI template](docs/ci/README.md) to
run the same checks on Python 3.10 and 3.12. It is not active until installed under
`.github/workflows/`.

## Contribute a result or demo

Include the task, input provenance, configuration, version, comparison conditions, outputs and failure coverage. Mark synthetic fixtures and constructed cases explicitly. A model score or model-assessor pass is distinct from expert validation, a formal proof or conference acceptance.

For report changes, preserve the evidence chain: data → recomputation → figure → prose. Do not silently replace the released v6 data with new trials. Add a new version or clearly scoped supplement and document the changed population or protocol. Active human time, elapsed time, invocation counts, tokens and money are different measurements.

Store runtime work under ignored `workspaces/` or outside the checkout. Share only artifacts you are authorized to release. Submit a focused pull request explaining the behavior change, how it was checked and any remaining limitations.
