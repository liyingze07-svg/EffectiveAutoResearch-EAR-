# write-direct-rebuttals — r6 对外呈现的主方法(应答编译范式)

> 蒸馏自 `campaigns/01-wdData/lyzHandCraft/skills/write-direct-rebuttals/`(用户人工手改验证的 ground truth,01-wdData)。
>
> **范式**:rebuttal = 对 reviewer 每个问题 slot 的**最小、字面、诚实的直接应答**的编译。**Directness 压倒一切修辞——绝不让叙事润色稀释直接性。**
>
> **分工**:`CRAFT.md`(§0–5:心结诊断 / 立场三分流 / 14 concern 打法)提供**内部 logic**(想清楚"该答什么心结、用什么证据");**本文件管对外呈现**——最终 reviewer-facing 稿按此产出。两遍:先原子精确,再编译成连续 W 散文。

## 两遍流程

1. **原子应答**:把每个 reviewer 问题拆到"一个 answer slot",逐 slot 字面直答(内部工作稿带 `Direct answer / Why / Camera-ready change` 脚手架)。
2. **编译**:把相关原子对合并成每 W 一段**连续散文**,删掉脚手架标签,过 deletion + ammunition 测试。

## 锁定来源
- reviewer 原文 = **唯一引用来源**(verbatim,不插造的省略号)。
- 手稿 = 核对定义/假设/公式/已有结果。
- 技术笔记/实验摘要 = 证据,不是抄的散文。
- 要求的格式 + 修订时态。
- **第一遍写作把旧 rebuttal 草稿排除在外**(旧的 indirect/risky 语言会锚定污染)。

## 原子化拆解 + 字面映射(硬规则)
拆到每单元一个 answer slot,保留 reviewer 的**主/谓/宾**。**多部分问题的每个 clause 都要答**,必要时拆块。**不把礼貌语当独立问题**("Can you speak to this?"并入其后的实质问题,别答"Yes, we can speak to this")。

| Reviewer slot | 直答开头(第一句必须这样起) |
|---|---|
| `What is X?` | `X is …` |
| `What is the input for X?` | `The input for X is …` |
| `Is it A, B, or both?` | `It is …`(A/B/both 分别答) |
| `Do you think X works for Y?` | `Yes, we think X works for Y when …` |
| `How many n are needed?` | `The required n is …`(给规则 + 支持的工作点) |
| `How would it hold under Z?` | `The method holds under Z by …` |
| `Could X cause harm Y?` | `X did / did not cause measured Y …` |
| `Please define/change/add X` | `In the camera-ready version, we will define/change/add X …` |

**若直答开头不能紧跟引用之后 → 问题还太宽,或答得 evasive。**

## 每个原子应答的规则
- **答案在前**,context/nuance/公式/证据在后。
- 公式只在"证明答案或消除明说的误解"时用;数字只在"回答 reviewer 要的量/结果"时用。
- **时态三分(硬)**:已有理论=现在时;完成的实验=过去/现在完成时;**手稿编辑=将来时 `In the camera-ready version, we will …`**。
- **技术边界写成正向条件,不是道歉/limitation**:写 "The theorem applies **when** the composition is inherited across rounds",不写 "limitation: 我们没覆盖 X"。

## 编译成 W 块
每 W 一段连续散文(不是 checklist):
```
**W1 (“逐字最小 reviewer 引用”):** <立刻直答> <必要的解释与证据> In the camera-ready version, we will <具体改动>.
```
块内:①保留字面直答开头 → ②premise → mechanism → evidence → camera-ready action 排序 → ③合并重复的定义/证据 → ④不同 answer slot 作连续显式句 → ⑤**删掉 `Core question/Direct answer/Why/Camera-ready change` 等工作标签**。
**绝不在 W1 前加通用致谢段或复述 reviewer 好评。**

## 可读性(散文手艺,硬规则)
应答编译是要"逻辑严格"的推理任务,但**渲染出来必须像正常人说话**——严格 ≠ 拗口。逐句过:
- **一量一句**:一句只承载一个主张/一个量。**禁止**把三四个并列量(下界 / 兑换率 / 斜率带 …)塞进同一句用括号定理号串起来。多个量 → 拆成 "The first is … The second is … The third is …"(中文"第一个是…第二个是…第三个是…")。
- **绝不用破折号(em-dash `—` / 中文 `——`)当从句连接器**。它是拗口和"非人类"的头号来源。改法:该停就用**句号**另起一句;补充说明用**冒号**;并列用逗号或"and/而"。
- **绝不用"不是 X 而是 Y"式对比句纠正 reviewer**(中文 `不是…而是` / `而不是` / `而非`;英文 `not X but Y` / `rather than` / `instead of` / `X, not Y`)。这类对比读起来像在**辩驳/纠正**对方,对咄咄逼人的 reviewer 尤其显得对抗。改法:**只正面陈述你要的那个 Y**,让 X 自然出局——"贡献不在定理,而在协议"→"贡献在于它所支撑的协议";"IC 不测忠实性,它测行为耦合"→"IC 测的就是行为耦合,仅此而已";"不要信任标量,而要读两坐标"→"读两个坐标即可,标量在这里有 46% 的时候是错的"。**例外**:reviewer 原句里的 `而不是 / rather than` 是 verbatim 引用,原样保留不动。
- **定理/命题编号只做尾注**:写完这句话的自然主张,再用括号 `(Thm 2, 结构形式见 Thm 3)` 收尾。**不要**让编号打断句子主干。
- **数值区间在散文里用"到 / from X to Y"**,不写 `7.0–31.0%` 这种夹在句中的连字符区间(区间号在正文里读起来像破折号)。括号内的 CI `[0.39, 0.53]`、复合词连字符(`sign-mismatch`、`e-SNLI`、`camera-ready`)不受影响。
- **自检**:把每段**读出声**。凡是"一口气念不完 / 要回读才懂主谓宾"的句子,就是塞太多了,拆开。

## deletion test + ammunition test(交付前逐句过)
**deletion test**:每句必须**恰好承担**一个功能——①答 slot ②定义必要术语/条件 ③连接前提到答案 ④给证据 ⑤指定 camera-ready 编辑。**删掉功能之外的任何句子。**

**ammunition test**:问"reviewer 能否把这句直接抄进新的批评"。改写或删掉:
- volunteer 未问的弱点;
- `we do not claim / we did not test / future work / our sample is limited`;
- 把 claim 扩到证据之外(over-claim);
- 无根据地声称真实世界普遍性;
- **把实质反对说成"only a clarity issue"**;
- 引入答案不需要的**新 promise / metric / setting / assumption**。
> 但**绝不隐瞒回答 reviewer 所必需的事实**;必要边界写成正向技术条件。

## 交付前 8 项验收(内部 Q-A audit)
1. 每条引用与原 review **精确匹配**。
2. 每个实质问题都有直答。
3. 每个直答开头 **mirror reviewer 的主/谓/宾**。
4. 礼貌语没被当独立问题答。
5. 每个定量 claim 都映射到手稿结果或所给证据。
6. 每处手稿编辑用 **camera-ready 将来时**。
7. 每个原子答案在终稿 W 块里**恰好出现一次**。
8. 每句都过 deletion + ammunition 测试。
9. 每句都过**可读性**:一量一句 / 0 破折号(`—`、`——`)/ **0「不是 X 而是 Y」对比句**(`不是…而是`、`而不是`、`而非`、`not X but Y`、`rather than`,reviewer 引用内的除外)/ 定理号只作尾注 / 读出声一口气念得完。

## 双语交付
英文提交稿 = 连续散文;中文单独 `逻辑：` 文件记录每 W 块的:字面 answer slot / mirror 后的答案 / 必要证据链 / camera-ready 改动 / 是否造攻击面。(**逻辑在内部、直接在对外**——这就是论证编译,只是把脚手架留在内部。)

## 对错各一例
- ✗ 问"input for X?"→ 答"The key distinction is between identity and composition."(reframe,没直答)
- ✓ 问"input for X?"→ 答"The input for the admission filter is the current-round candidate pool. The composition inherited by the next round is …"
- ✗ 问"…would it work for a low-resource language?"→ "Yes, we can speak to this."(答了礼貌语)
- ✓ 同问 → "Yes, we think the approach would work for a low-resource language when …"
