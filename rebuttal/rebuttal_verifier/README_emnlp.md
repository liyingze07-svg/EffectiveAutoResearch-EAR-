# EMNLP/ARR Rebuttal-Quality Verifier — 现状说明

记录当前 **EMNLP/ARR 版**的 32 篇测试数据与 verifier 落地情况。ICLR 版见
[`README.md`](README.md)（0.805）；两版是**两种不同的决策模型**，各自校准，互不覆盖。

> 一句话结论：EMNLP 版 v2 在 32 篇平衡集上 **macro-F1 = 0.718 / acc = 0.719**，
> 从直接套用 ICLR prompt 的 **0.468（随机水平）**拉起来。核心不是"更会读 rebuttal"，
> 而是发现 **ARR 边缘群的涨/平主要由审稿人的"起点分 + 上移空间"决定**，并把这个先验写进了 prompt。

---

## 一、数据：`data/emnlp_test32.jsonl`（32 篇，16 涨 / 16 平）

### 来源
- 项目 `<arr-corpus>`（ACL Rolling Review 公开评审，ARR 2024 cycle）。
- 每篇论文含 `reviews.json`（review 全文 + `scores.overall_assessment` 1–5、`soundness` 1–5、
  `meta.confidence` 1–5）、`comments.json`（作者 rebuttal + 审稿人后续评论）。

### 标签怎么来的（关键：ground truth 来自审稿人自己的话，不是 LLM 判的）
- **涨（raise）**：审稿人后续评论里**显式**说涨分，且**全部带 "from X to Y" 幅度**
  （如 "I increased the score from 3 to 3.5"）。→ 16 篇，幅度 **Δ=0.5 ×11、Δ=1.0 ×5**。
- **平（same）**：审稿人**显式**维持（"I will keep my score" / "maintain my rating unchanged"），
  且评论中**无任何涨分语**。→ 16 篇。
- 严格清洗：排除 excitement 轴（非 overall）、soundness-only、条件句（"if you…then I can raise"）、
  否定句（"do not feel comfortable raising"）；一篇一条去重；review>350 字、rebuttal>250 字。
- 构建脚本：[`../scripts/build_emnlp_test.py`](../scripts/build_emnlp_test.py)。

### 防泄露
- persona **不放改分后的 overall assessment 终值**。需要初始分时用**真实初始分**：
  涨分用 "from **X**"、平用（未变的）终值 —— 都是 rebuttal 前的值，不泄露答案。

### 字段
| 字段 | 含义 |
|---|---|
| `note_id` | 案例唯一 id |
| `gold` | `raise` / `same`（审稿人原话推出的真值）|
| `reviewer_profile` | persona 文本（ARR 口径：confidence/5 + soundness/5；**不含 overall 终值**）|
| `review` | 审稿人原始 review 全文（`## paper_summary` / `## summary_of_weaknesses` …）|
| `rebuttal` | 作者对该审稿人的 rebuttal |
| `_statement` | 审稿人表态原话（标签依据，供人工核验）|
| `_final_oa` | 该 review 存档的 overall assessment（涨=终值 Y，平=初始）|
| `_delta` | 涨分幅度（`_final_oa - _delta` = 真实初始分）|

带初始 OA 的变体（v2 verifier 用）：`data/cell_emnlp_ratingOA.jsonl`
（由 [`../scripts/build_cells.py`](../scripts/build_cells.py) 生成，persona 加 "your overall assessment was X/5"）。

---

## 二、Verifier：`prompt_template_emnlp.py`（v2）

与 ICLR 版共用 [`verify_rebuttal.py`](verify_rebuttal.py)，通过 `--template prompt_template_emnlp` 切换。

### 设计（数据驱动，非拍脑袋）
1. **起点锚 + room-to-move 先验**：起点低(≤3)→倾向涨、高(≥3.5)→倾向平。
   这是 ARR 边缘群的主导信号（见下方发现）。
2. **fundamental-concern 闸门**：novelty 不足 / 前人已做 / 核心概念没定义 / contribution 有限
   → 补实验也不解决，判平（即使起点低）。
3. **empirical-concern 可赎回**：缺实验/baseline/细节不清被 rebuttal 补上 → 从低起点判涨（+0.5 小步）。

### 模型与配置
- **骨干模型：`deepseek-v4-pro`**（与 ICLR 版同一个；横评冠军）。
- 端点 OpenAI 兼容：`DEEPSEEK_BASE_URL=https://api.deepseek.com`，走 `verify_rebuttal.py` 里的
  `openai` 客户端。配置在 `rebuttal_verifier/.env`：`DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` /
  `DEEPSEEK_MODEL=deepseek-v4-pro`。换模型改 `DEEPSEEK_MODEL` 即可（换后需重新横评，别默认"更大更好"）。

### ⚠️ 输入契约（硬性）
EMNLP 版**必须喂初始 overall assessment**（persona 里的锚点）。**没有它就退回随机水平**
（纯文本推理 = 0.435–0.468）。这是与 ICLR 版最大的使用差异。

---

## 二.5、如何调用 verify（三种方式，全部走 `--template prompt_template_emnlp`）

**输入字段**：`review`（必填）、`rebuttal`（必填）、`initial_overall`（EMNLP **必填**，rebuttal 前的 1–5 总分）、
`confidence`（1–5）、`soundness`（1–5）；或直接给 `reviewer_profile` 自由文本覆盖上面几项。
**输出**：`{reaction: raise|same|lower, quality: high|neutral|counterproductive, reasoning}`。

**① Python 直接调**
```python
import prompt_template_emnlp
from verify_rebuttal import verify_one
verify_one({
    "initial_overall": 3, "confidence": 4, "soundness": 3,
    "review": "## summary_of_weaknesses\n1. Missing baseline X. 2. No ablation.",
    "rebuttal": "We added baseline X (Table 3) and a full ablation (Table 4).",
}, build_messages=prompt_template_emnlp.build_messages)
# -> {"reaction": "raise", "quality": "high", "reasoning": "..."}
```

**按分数自动路由**：
- `--template auto`：只按分数换 **prompt**，模型统一 deepseek-v4-pro（OA=3→诊断器，其他→v2）。
- `--template route`：按分数换 **模型+prompt**——**OA=3 → GPT-5.5 + 诊断器**（横评中 GPT-5.5 对 OA=3 rebuttal 质量判别力最强，分离度 +0.28 vs pro +0.13，*caveat：在 xhigh reasoning 下测*），**其他分数 → deepseek-v4-pro + v2**。响应带 `model_used`/`template_used` 标注实际路由。
```bash
python verify_rebuttal.py --batch reviewers.jsonl --out preds.jsonl --template route
```
`route` 模式需要 **`OPENAI_API_KEY`**（gpt-5.5 走 `https://api.openai.com/v1`）；缺 key 时 OA=3 **优雅回退**到 deepseek-v4-pro。无 key 又想用 GPT-5.5 时，可走远程 Codex 批处理（见项目根 README 的 Codex 流程）。

**② 命令行（单条 / 批量，手动指定模板）**
```bash
# 单条：case.json 里含 initial_overall/confidence/soundness/review/rebuttal
python verify_rebuttal.py --case case.json --template prompt_template_emnlp
# 批量：JSONL 每行一条
python verify_rebuttal.py --batch cases.jsonl --out preds.jsonl --template prompt_template_emnlp
```

**③ HTTP 服务（队友不用拿 DeepSeek key，见 `serve.py`）**
```bash
# 服务端（持有 key）：SERVICE_TOKENS 可选，配了就要求带 token
cd rebuttal_verifier && pip install fastapi uvicorn
SERVICE_TOKENS=alice-tok uvicorn serve:app --host 0.0.0.0 --port 8000
```
```bash
# 调用方（只需一个 service-token）：venue 必须为 "emnlp"，且必须带 initial_overall
curl -s http://HOST:8000/verify -H "Authorization: Bearer alice-tok" \
  -H "Content-Type: application/json" \
  -d '{"venue":"emnlp","initial_overall":3,"confidence":4,"soundness":3,
       "review":"## summary_of_weaknesses ...","rebuttal":"We added ..."}'
# -> {"reaction":"raise","quality":"high","reasoning":"..."}
```
`GET /health` 会回报当前模型（`deepseek-v4-pro`）和是否开启鉴权。缺 `initial_overall` 时服务返回 400。

---

## 三、结果（同一 32 篇平衡集，逐条隔离，temp=0）

| 方法 | acc | macro-F1 | 说明 |
|---|---|---|---|
| ICLR-prompt 直接套用 | 0.469 | 0.468 | 随机水平，**不能迁移** |
| EMNLP-prompt v1（纯文本 concern 分诊）| 0.438 | 0.435 | 无初始分，仍随机 |
| 傻阈值 `初始OA<3.25→涨` | 0.688 | 0.683 | 单特征，揭示信号在起点分 |
| **EMNLP-prompt v2（起点锚 + 先验）** | **0.719** | **0.718** | ✅ 当前落地版，预测文件 `data/emnlp_preds_v2b.jsonl` |
| EMNLP-prompt v3（过度加强闸门）| 0.594 | 0.593 | 过拟合翻车，已回滚 |

**v2 混淆矩阵**（真判别，非挪阈值）：raise→11/5（召回0.69）、same→4/12（召回0.75）。

### 核心发现（这才是"会议差异"的真正内涵）
- **信号在初始分里，不在 rebuttal 文本里**：单看起点分的一行 if 就到 0.68；LLM 纯文本推理在随机线。
- 原因：ARR 这批是"审稿人亲自发帖表态"的**决策边界自选子群**，rebuttal 质量都差不多好、**不区分**涨/平，
  真正区分的是审稿人**有没有上移空间**（低起点会涨、高起点已满意→维持）。
- ICLR 反而有 0.8，是因为它用**全体评分 delta**、混入大量文本上明显可分的简单样本；ARR 这个集全是硬样本。

---

## 四、诚实的边界

- **样本小**：32 条，置信区间约 **±0.08**。v2 的 0.718 vs 傻阈值 0.683 在噪声内 —— 严谨说法是
  **v2 追平"起点分天花板"、稳定到 ~0.72**；但相对 0.468 的 +0.25 远超噪声，是实打实的。
- **不可约天花板**：错误集中在 **OA=3~3.5 区**，数据里就是 ~3 涨/3 平的硬币，文本定不下来。
  在 32 条上继续抠 prompt = 追噪声（v3 已证明会翻车）。
- **分布外**：这是**平衡集**上的数；真实分布（涨仅 ~20%）部署需按 base rate 重校阈值。

---

## 五、复现

```bash
# 1) 建 32 篇测试集（读 <arr-corpus>）
python scripts/build_emnlp_test.py

# 2) 建带初始 OA 的变体
python scripts/build_cells.py            # 产出 data/cell_emnlp_ratingOA.jsonl 等

# 3) 跑 v2 verifier（需 rebuttal_verifier/.env 里的 DEEPSEEK_API_KEY）
cd rebuttal_verifier
python verify_rebuttal.py --batch ../data/cell_emnlp_ratingOA.jsonl \
       --out ../data/emnlp_preds_v2b.jsonl --template prompt_template_emnlp

# 4) 打分见项目内 src/metrics.macro_f1（macro 只对有样本的类求平均）
```

---

## 五.5、OA=3 raise-potential 诊断器（`prompt_template_emnlp_oa3.py`）

**给最关心的 borderline-3 场景专门做的。** 定位从"预测涨/平"转成"**判 rebuttal 够不够强、并给可行动诊断**"——因为在 OA=3，涨/平**受审稿人惰性主导、文本里无显著信号**（置换检验 p 均>0.05），但 rebuttal 的**质量**是有信号的（好 rebuttal 与明显弱的可分，尽管只 ~+0.13）。

**调用**（多两个诊断字段）：
```bash
python verify_rebuttal.py --case case.json --template prompt_template_emnlp_oa3
```
**输出**（比通用版多 3 个可行动字段）：
```json
{"reaction":"same","raise_potential":"low","veto":"novelty",
 "blocker":"卡住分数的那一条首要顾虑",
 "advice":"一条能让这份 rebuttal 变强的具体改动",
 "reasoning":"..."}
```
- `reaction`/`raise_potential`：这份 rebuttal 是否**强到值得涨分**（不是"这个审稿人会不会改分"）。
- `veto`：`none` | `no-delivery`（只承诺/反问/无新证据）| `off-target`（答了次要、blocker 还在）| `novelty`（顾虑是新颖性，补实验无用）。
- `blocker` + `advice`：**给作者的行动清单**——弱在哪、怎么补。

**性能（诚实）**：在 54 条 OA=3 上，对**真好 rebuttal 判"够强"召回 0.78**、对**明显弱的降到 0.67**、质量分离度 **+0.13**。这是个**软质量哨兵，不是利刃**——n=54 上 prompt 微调只在 [+0.06, +0.16] 噪声区间摆动，调不动。**真正的产品价值是 `blocker`/`advice` 的结构化诊断**，可直接用于改写自己的 rebuttal。

## 六、下一步（若要稳超 0.72）

不是继续在 32 条抠 prompt，而是换地基：
1. **扩测试集**：已有 670+328 条干净候选，建 ~150 条、切 **dev(调) / test(报)**，让改进"超噪声可信"。
2. **self-consistency**：v2 多次采样投票，稳 +1~3 点。
3. **few-shot**：从 held-out ARR 挑典型案例（低起点顶死→平、经验解决→涨），**必须在 dev 上验证**。
4. 想突破文本天花板：引入文本外信号（其他审稿人分、meta-review、多轮讨论）——另一个建模层次。

现实上限估计 **~0.75–0.80**（受 OA 3–3.5 硬币区限制）。
