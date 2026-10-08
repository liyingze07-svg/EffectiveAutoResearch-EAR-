# EAR project page and research workspace

```bash
python3 -m ear demo studio --no-open
```

English is the default at `http://127.0.0.1:8765/`; `?lang=zh` provides the Chinese counterpart. Export a self-contained HTML with `--export /path/to/new-demo.html`. Serving and exporting use only Python's standard library.

The static hero shows all three EAR workflows and their inputs and outputs inside one dashed system boundary. Downloadable SVG architecture diagrams separate the research worker, supervisor, fixed review, revision and strategy evolution. EAR Studio provides three tabs, each with one input/process/output canvas: tree search and a proposal, proof and a paper, reviewer concerns and evidence-linked replies.

The module illustrations use authored proposals, proofs and responses. The mathematical example has two error schedules for a known quadratic optimization result; error controls change the computed numerical evidence and parameter-matched exports. It does not claim a model run, verified novelty or acceptance. The original historical idea case and executable synthetic engine examples remain separate. See [the guide](../../docs/demo-studio.md) for provenance and evaluation scope.

## Rebuild the authored assets

```bash
python3 examples/studio/build_architecture.py
python3 examples/studio/build_reference.py
```

The figure builder requires only Python's standard library. The reference builder requires ReportLab and writes six parameter-matched English PDF manuscripts to `output/pdf/` and their portable payloads to `reference.json`. It does not call a model. Serving never requires PDF-authoring dependencies.

Inspect every generated PDF page after changing the builder. Restart the local preview to load changed figures or reference data. HTML/CSS changes appear after reloading the page. Chinese UI summaries accompany the English source manuscripts.
