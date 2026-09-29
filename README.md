# EAR — Effective Auto Research

面向科研全流程的自动化工具集。当前包含两个相互独立、可单独使用的子项目：

| 子目录 | 做什么 |
|---|---|
| **[`autovibeidea/`](autovibeidea/)** | **从研究方向到提案。** 文献调研 → 批判分析 → idea 生成 → 多维筛选 → 深度精炼，输出可实施的 venue-ready 提案 |
| **[`rebuttal/`](rebuttal/)** | **从审稿意见到回复。** 给定论文与审稿意见，产出逐位审稿人的回复与给 AC 的评论。面向 EMNLP / ACL Rolling Review |

两者覆盖科研周期的两端——**投稿前**的选题与方案成形，**投稿后**的审稿应对——共用"外部模型独立评审 + 证据可追溯 + 不编造数字与引用"的设计取向，但不共享代码，可分别 clone 使用。

---

## 快速开始

### autovibeidea — 找 idea

```bash
cd autovibeidea
./run.sh --daemon "你的研究方向" NeurIPS   # 后台跑全流程
./run.sh --status                          # 查看进度
```

产出 `outputs/LANDSCAPE.md`（文献地图 + gap 矩阵）、`outputs/CRITICAL_ANALYSIS.md`（批判清单）、
`outputs/SCREENING_RANKED.md`（多维评分排名）、`refine-logs/FINAL_PROPOSAL.md`（最终提案）。

详见 [`autovibeidea/README.md`](autovibeidea/README.md)。

### rebuttal — 写 rebuttal

给定论文与审稿意见，跑 18 个物化阶段的流水线，经四道 gate 产出回复。
详见 [`rebuttal/README.md`](rebuttal/README.md)。

---

## 共同的设计取向

- **外部模型承担评审角色。** 生成与评审分离，避免自评虚高
- **证据可追溯。** 每条主张都要能指回文献、代码或实验记录
- **不编造。** 不虚构实验数字与引用；检索不到就记录为检索不到
- **降级而不中止。** 外部依赖不可用时自动降级并记录，流水线不停下来等人

---

## License

MIT
