# EAR Technical Report

**Version 6 · October 2026 · English and Chinese editions**

EAR organizes idea discovery, autonomous mathematical research, and rebuttal around one objective: reduce active human time while meeting research quality and machine-budget requirements. The report explains the mechanisms, connects each claim to its evidence, and presents the evaluation results.

| Edition | Report |
| --- | --- |
| English · 17 pages | [Read the English PDF](v6/reports/EAR_Technical_Report_EN.pdf) |
| 中文 · 17 页 | [阅读中文技术报告](v6/reports/EAR_Technical_Report_CN.pdf) |

**[Download the complete bilingual package (ZIP)](EAR_Technical_Report_v6_Bilingual_Public.zip?raw=true)**

Authors: Yingze Li, Dong Wang, Ben Wu, Xianglong Liu, Hongzhi Wang*

Harbin Institute of Technology

\* Corresponding author

## Report and supporting materials

Both editions share the same structure, results and evaluation definitions. The public package includes anonymized process examples and aggregate evaluation data.

| Directory | Contents |
| --- | --- |
| [reports](v6/reports/) | English and Chinese PDFs |
| [source](v6/source/) | Editable LaTeX sources and shared visual template |
| [figures](v6/figures/) | Figures in PDF, PNG and SVG formats |
| [data](v6/data/) | Aggregate results, claim mapping and evaluation protocol |
| [scripts](v6/scripts/) | Statistical recomputation, figure generation and PDF builds |

The mathematical strategy comparison covers G0 initialization and three evolution generations, G1–G3. Pass rates use the model-assessment protocol defined in [protocol.json](v6/data/protocol.json). Active human time is the primary optimization objective; direct human-time savings have not yet been measured.

## Rebuild

From the repository root:

```bash
cd docs/technical-report/v6
python3 -m pip install -r requirements.txt
python3 scripts/recompute.py
python3 scripts/draw_figures.py
python3 scripts/build_reports.py
```

PDF compilation requires XeLaTeX and the fonts and TeX packages listed in the [package README](v6/README.txt).

中文说明：两份报告采用相同的结构、图表与结果，以减少科研过程中的人时投入为核心，介绍批判性点子搜索、数学研究内外循环及 Rebuttal 优化。压缩包包含中英文 PDF、可编辑源码、图表、公开汇总数据和复算脚本。
