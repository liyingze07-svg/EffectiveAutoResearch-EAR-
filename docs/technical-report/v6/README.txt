EAR — Effective Auto Research
Public technical report package · October 2026 · v6

Authors
Yingze Li, Dong Wang, Ben Wu, Xianglong Liu, Hongzhi Wang*
Harbin Institute of Technology
* Corresponding author

Read the reports
reports/EAR_Technical_Report_EN.pdf — English technical report
reports/EAR_Technical_Report_CN.pdf — 中文技术报告

EAR organizes idea discovery, autonomous mathematical research, and rebuttal
around one objective: reduce active human effort while meeting research quality
and machine-budget requirements. The reports connect this objective to critical
search, continuous research, harness evolution, and evidence-based responses.

Both language editions have 17 pages and share their structure, numerical results,
and evaluation definitions. Mathematical revision and strategy comparisons use
aggregate historical records. Idea and rebuttal workflows include anonymized
process observations and reported feedback-evaluator measurements.

This edition displays G0 initialization plus three evolution generations, G1-G3.
It is a retrospective reporting window, with all 64 episodes inside that window
included in the totals. The G3 selected strategy passes 3/4 episodes (75%),
compared with 2/4 (50%) for its baseline; the entire G3 population passes 9/20
(45%). A pass is the historical model-assessment label defined below.

Package contents
source/en/ and source/cn/   Editable LaTeX sources for each language
source/shared/             Shared visual style, vector diagrams and references
figures/en/ and figures/cn/ Reusable figures in each language
data/                     Aggregate tables, process summaries and protocol
scripts/                  Statistical recomputation, plotting and PDF builds

Rebuild
From this directory, use Python 3 and install requirements.txt. PDF compilation
requires XeLaTeX with ctex, TikZ, tcolorbox, TeX Gyre Pagella, TeX Gyre Heros,
DejaVu Sans Mono, Noto Serif CJK SC and Noto Sans CJK SC. A standard TeX Live
installation with its Chinese-language and extra LaTeX packages supplies the
TeX dependencies.

  python3 scripts/recompute.py
  python3 scripts/draw_figures.py
  python3 scripts/build_reports.py

To compile one language, pass en or cn to build_reports.py. Temporary TeX files
are kept outside this package and removed after compilation.

Evaluation definitions
data/protocol.json defines cohorts, scoring rounds, version selection and cost
units. The historical mathematical pass is an automated assessment under the
recorded three-session rule. Research invocations, reviewer invocations and
reconstructed refinement attempts are reported in their original units.
Active human time is the system's primary objective and a separate measurement
axis. The accompanying tables support recomputation of the reported aggregate
statistics; source manuscripts and individual review text are not distributed.

中文说明
本包提供相同结构、图表和结果的中英文技术报告。报告以人时为首要资源，
介绍批判性点子搜索、数学研究内循环与策略演化外循环，以及基于证据的
Rebuttal 优化。公开附件保留成组统计、匿名过程记录、评价协议和复算脚本。
本版统计截至 G3：G0 初始化与 G1–G3 三代演化，范围内 64 次尝试均计入。
G3 所选策略通过率 75%（3/4），基线 50%（2/4），整个种群为 45%（9/20）。
运行上述三个命令即可复算结果、重绘图形并编译两份 PDF。

Project
https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-
