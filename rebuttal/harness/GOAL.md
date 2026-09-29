# GOAL.md — 显式目标与停机判据(一等公民)

> 引擎每轮读这个文件判"停没停"。**这是一个可检查的 predicate,不是叙事。**
>
> ⚠️ **单一真相源 + 防漂移**:分区 bar 的**权威实现**是 `rebuttal_verifier/consensus_gate.bar_met` / `consensus`;下面的表是它的人类可读镜像。**改判据必须三处同改**:①本表 ②`bar_met`/`consensus` ③`consensus_gate._selfcheck()` 里对应的断言。`orchestrate.py` 启动时跑 `_selfcheck()`,本表与实现漂移(如 H4:OA≥4 应是维持 bar 不是 raise bar)会**当场拒绝开跑**,不会带病跑一整晚。
>
> 🔎 **谁在用这根 bar**:r7 涨分门(整稿停机)+ **实验说服力门 S-exp**(`stages/r4_experiment_persuasion.md`,r4→r5 之间,对**单个实验真结果**逐 concern 调**同一个** `bar_met`)。S-exp 是这根 bar 的**消费者**,不新增判据 → **不属于**上面的三处同改。

## 目标(一句话)
对**每个 targeted reviewer**,让 rebuttal 在**跨家族合议门**下清掉**该 reviewer 分区对应的 bar**;全清则 DONE,否则按 `LOOP.md` 继续 roll,到 `max_iter` 仍不清 → **诚实让步**输出 best-so-far。

## 分区 bar(按 reviewer 的 overall_assessment,由 `consensus_gate.bar_met` 判)
| 分区 | bar(必须两家族都满足) |
|---|---|
| **OA = 3(borderline)** | 诊断器 `veto == 'none'` **且** `raise_potential == 'high'`(= 强度达标;**不是**预测涨分结局——borderline 结局文本不可测) |
| **OA ≤ 2(低起点)** | `reaction == 'raise'`(低起点 raise 信号存在) |
| **OA ≥ 4(高起点)** | `reaction != 'lower'`(维持不掉) |

## 停机判据(DONE ⟺ 全 true)
合议是**分区路由的**(见 `consensus_gate.consensus`),不是所有分区都用同一条 AND。停机对每个 targeted reviewer:
```
DONE ⟺  ∀ reviewer ∈ target.require_raise_on ∪ target.maintain:
            consensus(deepseek, codex, case).stop == True   # 分区路由(见下)
        AND ammo_hits(final_rebuttal) == []                 # 弹药硬门(全分区)
        AND no_fabrication(rebuttal, evidence)              # 每个 claim 追溯真实证据

其中 consensus(...).stop 按分区:
  · OA ≤ 2 / OA ≥ 4 (strict 模式)  ⟺  bar_met(deepseek) AND bar_met(codex)   # 两家族都清
  · OA = 3 border  (authoritative 模式) ⟺  bar_met(codex_primary) AND deepseek.reaction != 'lower'
```
- **为何 OA=3 不强制 strict**:borderline 处 DeepSeek 质量分离弱(README §7,+0.13 vs Codex +0.28),强行要 DeepSeek 也 `bar_met` 会注入假阴性、把 loop 卡死。故权威判官=Codex/GPT-5.5(高 reasoning)主判,DeepSeek 降级为**否决权软检查**(只要它没判 `lower` 就不挡)。其余分区两家族对等,strict 双清。
- **仍是跨家族**:即便 authoritative 模式,DeepSeek 的 `lower` 否决仍能挡停机——单靠 Codex 拟合过不了(不可违反 #4 成立)。

## 出口
- **DONE** → 打包 per-reviewer rebuttal + AC 评论。
- **迭代 = max_iter 仍未 DONE** → 每个未清的 reviewer 输出 best-so-far + 诚实让步 + 缺口清单,标 `HONEST_CONCEDE`。**绝不为"看起来过了"编实验/拟合判官。**

## 不可违反(否则整轮作废)
1. 绝不编数字/引用;做不到写 `[TBD]`(不是空承诺)。
2. 弹药 grep == 0(含"表演式诚实/过度让步"这类软弹药,见 ammunition-checklist)。
3. worker 看不到门内部 prompt,不对判据拟合。
4. 停机必须跨家族合议,不靠单判官。
