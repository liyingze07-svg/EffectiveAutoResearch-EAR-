#!/usr/bin/env python3
"""Draw bilingual report figures from public aggregates only.

Outputs inner_progress, evolution_progress and cost_comparison in PDF/PNG/SVG.
Requires matplotlib; Chinese rendering uses an installed CJK font.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from recompute import PUBLIC_ROOT, recompute

NAVY, TEAL, AMBER, MUTED = "#263C5C", "#58739A", "#A18563", "#5C6674"


def configure(language):
    families = ["Noto Sans CJK SC", "Noto Sans CJK JP", "WenQuanYi Zen Hei"] if language == "cn" else ["DejaVu Sans"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    family = next((f for f in families if f in available), None)
    if not family:
        raise RuntimeError("Chinese figures need an installed CJK font, for example Noto Sans CJK SC.")
    plt.rcParams.update({
        "font.family": family, "font.size": 10, "axes.titlesize": 11,
        "axes.titleweight": "bold", "axes.labelcolor": "#232A32",
        "text.color": "#232A32", "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": "#D5DAE2", "axes.labelsize": 9,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "axes.unicode_minus": False, "figure.facecolor": "white", "axes.facecolor": "white",
    })


def decorate(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#E6E9EF", linewidth=.7)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def save(fig, destination, stem):
    destination.mkdir(parents=True, exist_ok=True)
    for suffix in ["pdf", "png", "svg"]:
        kwargs = {"dpi": 220} if suffix == "png" else {}
        metadata = {"Title": stem, "Author": "EAR"} if suffix == "pdf" else None
        fig.savefig(destination / f"{stem}.{suffix}", bbox_inches="tight", metadata=metadata, **kwargs)
    plt.close(fig)


def inner_progress(metrics, language, destination):
    cn = language == "cn"
    rows = metrics["inner_rounds"]
    x = [r["round"] for r in rows]
    passes = [r["current_passes"] for r in rows]
    scores = [r["current_mean_score"] for r in rows]
    cohort_n = rows[0]["manuscripts"]
    retained = rows[-1]["selected_best_passes_at_cutoff"]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.15), gridspec_kw={"wspace": .33})
    axes[0].plot(x, passes, color=TEAL, marker="o", markersize=7, linewidth=2.3)
    axes[0].fill_between(x, passes, color=TEAL, alpha=.07)
    axes[0].set_ylim(0, 19)
    axes[0].set_yticks([0, 5, 10, 15])
    axes[0].set_title(f"当前版本通过数 / {cohort_n}" if cn else f"Current-version passes / {cohort_n}", loc="left", pad=13)
    for t, y in zip(x, passes):
        axes[0].annotate(str(y), (t, y), xytext=(0, 9), textcoords="offset points", ha="center", color=TEAL, weight="bold")
    axes[1].plot(x, scores, color=NAVY, marker="o", markersize=7, linewidth=2.3)
    axes[1].set_ylim(4.3, 6.12)
    axes[1].set_yticks([4.5, 5.0, 5.5, 6.0])
    axes[1].set_title("当前版本平均评分" if cn else "Current-version mean score", loc="left", pad=13)
    for t, y in zip(x, scores):
        axes[1].annotate(f"{y:.2f}", (t, y), xytext=(0, 9), textcoords="offset points", ha="center", color=NAVY, weight="bold")
    labels = ["初评", "修订 1", "修订 2", "修订 3"] if cn else ["Initial", "Revision 1", "Revision 2", "Revision 3"]
    for ax in axes:
        decorate(ax)
        ax.set_xticks(x, labels, fontsize=8)
        ax.set_xlim(-.2, 3.2)
    fig.text(.08, -.02,
             f"G0–G3 固定 {cohort_n} 个完整稿件；历史模型评审。最佳版本保留后最终通过数为 {retained}。" if cn else
             f"G0–G3: {cohort_n} completed manuscripts. Best-version retention yields {retained} final passes separately.",
             fontsize=8, color=MUTED)
    fig.subplots_adjust(bottom=.15, top=.84, left=.08, right=.98)
    save(fig, destination, "inner_progress")


def evolution_progress(metrics, language, destination):
    cn = language == "cn"
    rows = sorted((r for r in metrics["generation_comparison"] if r["role"] == "selected"),
                  key=lambda r: r["generation"])
    x = [r["generation"] for r in rows]
    rates = [100 * r["pass_rate"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.8, 3.3))
    ax.plot(x, rates, color=TEAL, marker="o", markersize=8, linewidth=2.5)
    ax.fill_between(x, rates, color=TEAL, alpha=.06)
    for t, rate, row in zip(x, rates, rows):
        label = f"{rate:.0f}%\n{row['selected_best_assessor_passes']}/{row['episodes']}"
        ax.annotate(label, (t, rate), xytext=(0, 10), textcoords="offset points",
                    ha="center", color=TEAL, weight="bold", fontsize=11, linespacing=1.35)
    ax.set_title("每代选中策略的模型评阅通过率" if cn else
                 "Selected strategy: model-assessment pass rate", loc="left", pad=14)
    ax.set_ylim(-5, 105)
    ax.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xticks(x, [f"G{i}" for i in x])
    ax.set_xlim(min(x)-.3, max(x)+.3)
    decorate(ax)
    fig.text(.10, -.02,
             "G0 初始化，随后演化三代；每个点统计当代选中策略的 4 次研究尝试。" if cn else
             "G0 initialization, then three generations. Each point covers four attempts with that generation's selected strategy.",
             fontsize=8, color=MUTED)
    fig.subplots_adjust(bottom=.16, top=.83, left=.10, right=.98)
    save(fig, destination, "evolution_progress")


def cost_comparison(metrics, language, destination):
    cn = language == "cn"
    rows = [r for r in metrics["selected_cost"] if r["generation"] == 3]
    base = next(r for r in rows if r["role"] == "baseline")
    selected = next(r for r in rows if r["role"] == "selected")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.35), gridspec_kw={"wspace": .35})
    specs = [
        ("research_invocations_per_pass", "研究调用 / 通过" if cn else "Research invocations / pass"),
        ("outer_proxy_per_pass", "研究＋评阅＋修订 / 通过" if cn else "Research + review + revision / pass"),
    ]
    for ax, (key, title) in zip(axes, specs):
        vals = [base[key], selected[key]]
        ax.bar([0, 1], vals, width=.55, color=[NAVY, TEAL], zorder=3)
        reduction = 100 * (1 - vals[1] / vals[0])
        ax.set_title(title, loc="left", pad=14)
        ax.set_xticks([0, 1], ["初始策略", "选中策略"] if cn else ["Original", "Selected"])
        ax.set_ylim(0, max(vals) * 1.40)
        for i, value in enumerate(vals):
            ax.text(i, value + max(vals) * .055, f"{value:.2f}", ha="center", fontsize=11, weight="bold")
        ax.text(.97, .94, f"−{reduction:.1f}%", transform=ax.transAxes, ha="right", va="top", color=TEAL, weight="bold", fontsize=13)
        decorate(ax)
    fig.text(.08, -.02,
             "G3：每组 4 次尝试。通过采用历史模型评阅规则；修订次数按记录推得。" if cn else
             "G3: four attempts per strategy. Historical model assessment; revision counts reconstructed from records.",
             fontsize=8, color=MUTED)
    fig.subplots_adjust(bottom=.15, top=.85, left=.08, right=.98)
    save(fig, destination, "cost_comparison")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PUBLIC_ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=PUBLIC_ROOT / "figures")
    parser.add_argument("--language", choices=["all", "en", "cn"], default="all")
    args = parser.parse_args()
    metrics = recompute(args.data_dir)
    for language in (["en", "cn"] if args.language == "all" else [args.language]):
        configure(language)
        destination = args.output_dir / language
        inner_progress(metrics, language, destination)
        evolution_progress(metrics, language, destination)
        cost_comparison(metrics, language, destination)
        print(f"Drew {language}: inner_progress, evolution_progress, cost_comparison (PDF/PNG/SVG)")


if __name__ == "__main__":
    main()
