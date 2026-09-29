# experiment-ladder.md — 实验决策规格

> 被 `stages/r3_triage_feasibility.md` 与 `stages/r4_experiment_redesign.md` 声明为输入。
> 本文件只给**规格**(决策表 + 契约字段),不含推导过程。

## warrant 回退阶梯

| # | move | warrant 是什么 | 何时用 |
|---|---|---|---|
| 1 | **已有** | 论文里已有的实验/表(reviewer 漏看) | 答案本就在 → 指位置 |
| 2 | **论证无关** | 逻辑:E 测的不在我们 claim 的 scope 内 | E 与 claim 正交(**必须真正交,否则=躲**) |
| 3 | **更便宜代理 E'** | 小实验 E' 承载同样证据重量 | E 太贵:子集/更少 seed/更小模型/单数据集+泛化论证 |
| 4 | **pilot+方向** | 小规模先导结果当方向信号 | E' 还太贵:先导+camera-ready(**先导要独立站住,承诺不能是全部**) |
| 5 | **文献** | 已有 paper 做过 E 或等价 | 别人证过 → 引 |
| 6 | **让步+界定** | 逻辑:承认在 X 下是局限,claim scope 是 Y | 拿不到 warrant → 把弱点变 scope |
| 7 | **真做 E** | E 本身的 raw(→ §1 执行) | E 可行且前 6 条都不够 |

**大多数"加不完"落在 3/5/6,不是 7。** 别默认往 7 冲。


**大多数 concern 落在 3/5/6,不是 7。** 不要默认往 7 冲。

**P0 闸**:当 concern 是 reviewer 明确点名要实验、或质疑「泛化性 / 缺实验 / 未验证 /
只在 X 上测过」时,**落到 move-6 让步之前必须先评估 move-4 pilot**:有无可复用的
基建/数据/代码能小规模跑一个先导?能跑就跑。只有 pilot 明确不可行(无基建 /
需真人标注 / 远超时间预算)才让步,并写下 `pilot_rejected_reason`。

**时间预算**:move-7 的门槛随 rebuttal 剩余窗口变。时间紧或 E 高耗时 → 停在 3/5/6;
窗口宽裕且 E 低耗时 → 倾向补。判据看 `experiment_request.budget` vs 剩余窗口。

## 实验请求契约

### 输入:`experiment_request`(rebuttal agent 写)
```json
{
  "concern_id": "R2-W3",
  "goal": "回应 reviewer 的哪个 concern(一句话)",
  "hypothesis": "要验证/展示什么(可证伪)",
  "what_to_measure": "指标 + 在什么数据/模型上",
  "baseline": "对照(真 baseline,非稻草人)",
  "expected_or_falsifier": "预期结果 + 数值 falsifier(什么结果算失败)",
  "resources": "需要的数据集 / 模型 / 代码入口",
  "budget": "算力/时间上限"
}
```
