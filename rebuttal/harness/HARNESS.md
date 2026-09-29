# AutoRebuttal Harness（本体索引）

> Paper-agnostic 的 rebuttal 操作系统。输入(论文 + 审稿意见)→ 并行策略写 rebuttal → 冻结涨分门裁决 → goal 模式硬约束涨分否则 loop。方法论迁移自 ExpAuto(`<expauto-root>`),完整设计见 `../rebuttal_harness_design.md`。
>

## 第一性原理(地基)
1. **A loop can DRIVE; it cannot ACQUIT** —— worker 写,冻结涨分门(异家族)判,物理隔离,worker 看不到判官内部。
2. **写作是论证编译,不是 next-token** —— 战略目标 → 论证 DAG → 查逻辑/冗余/第一性原理 → 渲染 → 反编译校验。
3. **涨分门是唯一 the bar** —— DeepSeek+Codex **合议**达标才算过(跨家族防 Goodhart);bar 分数感知(OA≤2 raise / OA=3 强度 / OA≥4 维持)。**权威 Codex 判官跑在独立 `JUDGE_MODEL`(默认 gpt-5.6-sol),绝不复用写手模型**(否则 GPT 写手自我 ACQUIT)。冻结 SPEC、诚实亮线、弹药 grep==0。
4. **Paper-agnostic** —— 换 case = 换 `REBUTTAL_CARD.json`,不改 harness。

## 执行模型(v0.3:物化阶段 + Codex 引擎 + 强制门)
- 显式目标/循环:`GOAL.md`(分区停机 predicate)+ `LOOP.md`(MoE-select-refine 循环协议)。
- 物化阶段 prompt:`stages/*.md`(**12 个**,r0a→ac,每个显式 I/O+规则+DO-NOT)。
- 通用 MoE:`strategies/MANIFEST.json` + 共享大脑 `CRAFT.md` + s1/s2/s3(可插拔合并)。
- 薄驱动:`runner/orchestrate.py`(读 MANIFEST/GOAL/LOOP,每阶段 `codex exec` 新进程,验 receipt,跑循环)。

## 生命周期 r0a → ac
r0a 抽卡 → r1 证据基底 → r2 concern 诊断 → **B1 心结门** → r3 响应模式 triage → **【实验 goal 循环** `EXPERIMENT_LOOP.md`**】S-ante 前置门(要不要加)→ (r4 跑 → X1-X6 验收 → **S-exp 说服力门**(分区路由,STRENGTH 才停机)→ 非 STRENGTH 则 `r4_experiment_redesign` 产"为什么+怎么重设计"→ 重跑)* 到 STRENGTH 或诚实让步 → **r5 证据合并**(只并已验收且过说服力门的证据) → r6 MoE 论证编译(遵 `framing_hint`) → r7 涨分合议门+goal loop → **B2 忠实门 + B3 弹药门** → ac 打包。
> 两个 goal 循环:**实验循环**(`EXPERIMENT_LOOP.md`,把实验迭代到能说服)+ **reviewer 循环**(`LOOP.md`,把 rebuttal 迭代到过 r7)。停机判据分别是 S-exp / r7,都复用冻结 `bar_met`。

## 目录
```
harness/
├── stages/*.md                       ★ 12 物化阶段(r0a/r1/r2/b1/r3/r4_run/r4_accept/r5/r6/r7/b2/ac,引擎无关)
├── strategies/MANIFEST.json + CRAFT.md + s*.md  ★ 通用 MoE(CRAFT=共享大脑,可插拔)
├── runner/orchestrate.py             ★ 薄驱动(Codex 引擎派发)
├── instantiate.py                REBUTTAL_CARD.json → 契约(镜像 ExpAuto)
├── templates/
│   ├── GOAL.tmpl.md            ★ 方法论心脏(r0→r7 + goal loop + 每轮硬收尾)
│   ├── SPEC.tmpl.md              冻结验收(涨分门合议 + 诚实闸)
│   ├── VERIFY.tmpl.md           独立验证器(重跑门判 ACQUIT)
│   ├── CLAUDE.tmpl.md            per-campaign briefing
│   ├── RESOURCE.tmpl.md         预算(门调用/写作/实验)
│   └── REBUTTAL_CARD.schema.json 卡片 schema + 示例
├── runner/
│   ├── loop_runner.py           r7 门 scaffolding(ICLR + EMNLP OA=3)
│   ├── coach_loop.py            诊断器教练循环编排器
│   └── moe_loop.py              MoE-select-refine 编排器(选最高→过门→carry-forward)
└── shared-assets/
    ├── ammunition-checklist.md   弹药 grep 清单(必 0 命中,含 §B2 表演式诚实)
    ├── rebuttal-tips.md          concern 分类学 + 应对手册(四 repo 提炼)
    └── strategies.md             早期 MoE 池笔记(现役策略见 strategies/CRAFT.md + s*.md)
../rebuttal_verifier/consensus_gate.py  冻结涨分合议门(DeepSeek θ₀ + Codex judge,分区 bar)
campaigns/<case>/                 每 case 实例化的契约工作区 + ledger/drafts/experiments
```

## 复用的外部资产
- 涨分门 DeepSeek 侧:`../rebuttal_verifier/verify_rebuttal.py`(0.805 F1,已 benchmark)+ `consensus_gate.py`(合议)。
- 第二判官:Codex(OpenAI 系,与 ExpAuto ACQUIT 同源),经 `orchestrate.py` 的 `codex exec`,跑独立 `JUDGE_MODEL`。
- 补实验(可选):ExpAuto 的 codegen/runner/recompute。

## 读懂这 4 个就懂 80%(v0.3)
