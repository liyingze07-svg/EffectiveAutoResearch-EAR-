# EXPERIMENT_LOOP.md — 实验 goal 循环(一等公民)

> 和 `LOOP.md`(reviewer MoE 循环)对称:那个循环把 **rebuttal 文本**迭代到过 r7 涨分门;
> **这个循环把一个实验迭代到过 S-exp 说服力门(STRENGTH),或诚实让步。**
> 停机判据 = S-exp;写手/规划是 DRIVE,判官是 ACQUIT,物理隔离,复用冻结 `bar_met`。

## 目标(一句话)
对每个要补的实验:让它的**真实结果**在跨家族合议下清掉它服务的 (reviewer, concern) 的**分区 bar**(= `STRENGTH`)。
清了 → 进证据池;清不了 → 说清**为什么** + **怎么重设计** → 换更强的真实验重跑;到 `max_experiment_iter`(默认 3)
或重设计不可行 → **诚实让步**,带着**最好的真实结果**出(**绝不重贴成 STRENGTH**)。

## 循环(`orchestrate.experiment_loop`)
```
输入:一个 experiment_request(带 serves[] + expected_or_falsifier)
──────────────────────────────────────────────────────────────
ANTE 门(r3b,跑之前,合议才拦):
   NOT_NEEDED → 便宜 warrant 已够,不必加 → 退出(status=NOT_NEEDED)
   REDESIGN   → 连 best-case 都翻不了 → 先重设计(planner);不可行→诚实让步
   GREENLIGHT → 进下面的循环
──────────────────────────────────────────────────────────────
for it in 1..max_experiment_iter:
   r4_run(A 机 zjexp,danger-full-access,timeout) → results.json
   r4_accept(异引擎 X1-X6 防造假) → ACCEPTANCE.json
      REJECT = 诚实/跑挂了(不是说服问题) → 诚实让步收尾(不算说服迭代)
   S-exp 说服力门(分区路由,OA=3 Codex 主判) → PERSUASION.json
      STRENGTH → 停机,WON(进证据池当硬证据)          ← 唯一停机条件(用户策略)
      非 STRENGTH →
         r4_experiment_redesign(planner,DRIVE 引擎)产:
            why_cannot_persuade(心结哪块没动)+ deficiency(轴错/规模/混淆/baseline/指标/效应)
            + 更强的 new_experiment_request + feasible?
         feasible → 换成新 request(新 expid)→ 下一轮重跑
         infeasible → 诚实让步(warrant 阶梯 move-6),带 best-so-far 真结果
到 max_iter 仍非 STRENGTH → 诚实让步 best-so-far
```

## 停机与出口
- **WON** ⟺ 某轮 S-exp `overall == STRENGTH`(跨家族合议清该分区 bar)。
- **HONEST_CONCEDE** ⟺ 重设计不可行 / X1-X6 REJECT / max_iter 到。带 `final`(最好那轮 expid)+ `why` + `chain`(每轮留痕)。
- **NOT_NEEDED** ⟺ ANTE 判便宜 warrant 已够。
- 留痕:`experiments/<base>/loop.json`(ANTE 决策 + 每轮 accept/persuasion + 重设计链)、`ledger/experiment_loop_results.json`(全实验汇总)。

## 不可违反(否则整轮作废)
1. **只 STRENGTH 停机,但绝不为停机造假**:够 STRENGTH 只能靠**设计更强的真实验**,不能把弱/双刃结果重贴成强;做不到就诚实让步(带真实下界结果,不改标签)。
2. 每轮真跑真数据过 X1-X6;负结果照报;`feasible=false` 是合法结局。
3. 判官(S-exp/accept 的 ACQUIT)≠ 写手/规划(run/redesign 的 DRIVE);判官跑 `JUDGE_MODEL`,规划跑写手引擎。
4. 停机判据 = 冻结 `bar_met` 的跨家族合议,不靠单判官。
5. **死磕有界**:`max_experiment_iter` + 每次重设计过可行性闸;不可行立即让步,不空耗 GPU。

## 和 reviewer 循环的关系
实验循环产出的是**证据**(evidence_pool 里 STRENGTH=met / 让步=unmet + framing_hint);reviewer 循环(`LOOP.md`)再用这些证据把 rebuttal 迭代到过 r7。两个循环解耦:实验先收敛到"能说服的证据",文本循环再收敛到"过涨分门的稿"。
