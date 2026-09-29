# RESOURCE — demo-argument-compiler（预算配额）

Rebuttal campaign 主要烧的是 **API 调用**（涨分门 + 写作 + 诊断）和（可选）**补实验算力**。

## 两条铁律
1. **涨分门调用是最贵的信号,别浪费**：只在注册的 gate 点调（r0 基线 / r7 打分）。每次打分 = 逐 P0 reviewer × {DeepSeek, Codex} × 采样数。别对半成品反复打分。
2. **补实验（若 CARD.allow_new_experiments=true）走 ExpAuto 算力**：推到远程 GPU 跑、结果落 NFS，本机只静态 lint。绝不在本机跑长实验。

## 预算表（parallelism=1 默认）
| 资源 | 每轮上限 | 怎么用 |
|---|---|---|
| 涨分门调用 | P0 数 × 2 判官 × 3 策略 × 采样(默认 3) | r7 一次性批打分（`verify_batch` 并发）;别单条反复试 |
| 写作 sub-agent | 3 个（并行） | 每策略一个,物理隔离,避免相互污染 |
| 诊断/证据 | 主 agent 串行 | r1-r5 在主线跑,中间产物落 ledger 当外部记忆 |
| 补实验 | 见 CARD.experiment_budget（待定,默认关） | 允许时复用 ExpAuto GPU 池,submit-detach 不阻塞 |

## 涨分门调用外壳（照抄）
```python
# DeepSeek 侧（排序 + 主判）
from verify_rebuttal import verify_batch   # $AUTOREBUTTAL_ROOT/rebuttal_verifier/
cases = [{"review": r.text, "rebuttal": draft, "initial_rating": r.rating,
          "confidence": r.conf, "soundness": r.s, "presentation": r.p,
          "contribution": r.c, "note_id": f"{slug}-{r.id}"} for r in p0_reviewers]
ds = verify_batch(cases, workers=8)         # -> [{reaction, quality, reasoning}, ...]

# Codex 侧（合议,独立 prompt,同 persona,绝不喂 label）→ mcp__codex__codex
# 达标 ⇔ 每个 P0 上 ds.reaction==raise AND codex.reaction==raise
```

## 备注
- **worker 看不到涨分门内部**：写作 agent 拿不到 θ₀ prompt 细节,不能对着判据拟合。
- 采样求稳：门有 ±0.05 噪声,每 (reviewer, 判官) 多采样几次取多数,别信单次。
- 默认 `parallelism=1`：一篇一篇串行,把一篇做到合议涨分再换下一篇。
