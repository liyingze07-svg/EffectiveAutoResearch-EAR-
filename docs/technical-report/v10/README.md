# EAR Technical Report · v10

**Advance research through feedback. Improve strategies through results.**

[English PDF](reports/EAR_Technical_Report_EN.pdf) ·
[中文 PDF](reports/EAR_Technical_Report_CN.pdf) ·
[Aggregate data](data/README.md) · [Evaluation protocol](data/protocol.json)

Yingze Li, Dong Wang, Ben Wu, Xianglong Liu, Hongzhi Wang*<br>
Harbin Institute of Technology · October 2026<br>
\* Corresponding author

This bilingual edition explains EAR's central principle, independent modules,
research revision and strategy evolution. It includes editable LaTeX, nine
figures per edition, aggregate data and reproduction scripts. The English and
Chinese editions use the same results and evaluation definitions.

The data are byte-identical to the [original v6 release](../v6/README.md).
v10 revises the explanation and presentation; it introduces no new evaluation
trials. Historical model-assessment passes, the current engine's terminal
review gate and real conference acceptance remain distinct. Active human-time
savings have not been measured.

## Contents

| Directory | Contents |
| --- | --- |
| [reports](reports/) | Final English and Chinese PDFs |
| [source](source/) | Editable bilingual LaTeX and mechanism diagrams |
| [figures](figures/) | Result plots in PDF, PNG and SVG formats |
| [data](data/) | Aggregate results, claim mapping and protocol |
| [scripts](scripts/) | Statistical recomputation, plotting and PDF builds |

The [SHA-256 manifest](manifest.json) records the versioned files. It detects
accidental changes; it does not authenticate research claims.

## Verify without a model

From the repository root, using Python 3.10 or newer:

```bash
python3 scripts/check_report.py --report-root docs/technical-report/v10
```

This checks the manifest and recomputes the aggregate metrics. The public data
support arithmetic reproduction, not rerunning the private research campaigns.
Individual manuscripts, model reviews and per-case evaluator predictions are
outside this release.

## Rebuild

From this package directory:

```bash
python3 scripts/recompute.py
python3 -m pip install -r requirements.txt
python3 scripts/draw_figures.py --language cn
python3 scripts/draw_figures.py --language en
python3 scripts/build_report_cn.py --output ../../../workspaces/report-v10/CN.pdf
python3 scripts/build_report_en.py --output ../../../workspaces/report-v10/EN.pdf
```

Plotting requires Matplotlib and the fonts specified in the plotting script.
PDF compilation requires XeLaTeX and TeX Live / MacTeX packages including ctex,
fontspec, TikZ, tcolorbox and tocloft. The included vector plots allow compilation
without regenerating figures. Chinese text falls back to Noto / Source Han or
Fandol fonts; English text uses TeX Gyre Pagella with available sans-serif fonts.
System fonts are not distributed.

Without `--output`, the build scripts write to `reports/`. Rebuilding versioned
files changes their hashes; use a copy of this package when modifying sources
or figures. The example above puts compiled PDFs in an ignored local workspace.

中文说明：v10 已包含中英文成稿、可编辑源码、图表与复算脚本。公开汇总数据
与 v6 完全相同，本版没有新增实验。请保留 v6 的原始证据；修改或重新绘图时，
在副本中工作，避免覆盖已发布文件。
