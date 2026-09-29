# 策略 s1 — 证据锁定 / 事实安全(最稳锚)

> **必须先读 `CRAFT.md`**(总则+立场+concern 打法+措辞)。本文件只定这个姿态的差异化取舍。

## 一句话理论
**用数字和页码级证据把每个 concern 钉死;能证明的一律正面证明,不辩空话、不认软话。** 靠"data beats arguments"移动 reviewer。

## 适配画像(gate 会选它当 fit)
心结是 **Evidence / Soundness / Reproducibility / Missing-baseline / Ablation** 的 reviewer——他们要的是"证明给我看",不是态度。

## 差异化取舍
- **立场**:以 CRAFT 的 ③辩护 + ①纠正 为主;**让步最少**——只在真拿不到 warrant 时,且一句带过。
- **开场**:每个 concern 第一句甩**最强证据**(已有表/新实验 derived 数字)夺回框架,不先复述攻击。
- **顺序**:按证据强度排,P0 的硬证据最前。
- **语气**:精确、自信、页码/表级("Table 3 shows ...","Sec 3.1 L142 states ...")。
- **每句 = 一个 warrant 绑真实证据的 claim 节点**(论证编译);证据槽位必来自 evidence_map,不能编。

## 失败模式(本策略要避开的)
- 含糊 hedging、"standard practice" 不给出处、用形容词代替数字、把可证的 concern 用嘴辩。

## 与另两个的区别
最不做说服心理建模、证据密度最高——**保底锚**:哪怕别的策略更会移动人,它保证"事实站得最稳、弹药最少"。
