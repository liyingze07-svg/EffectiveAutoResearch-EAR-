# stage b3_ammunition_gate — 弹药语义门(独立判官,防自伤)

> **由一个新的、异于写手的引擎上下文执行**(DRIVE/ACQUIT 分离)。**语义判断,不是 grep** —— 正则只抓字面、追不上"sharpen/streamline/tighten/polish…"的无限变体,也分不清"空承诺"和"给了确切文本"。本门理解**句意**:一句话是不是在给 reviewer 递攻击面 / 自揭短 / 空承诺 / 过度让步 / 表演诚实 / 造假。过强度门(r7)的稿必须再过本门才算 PASS;命中即拦,回炉改写。

## 槽位 `{{SLUG}}` `{{REVIEWER}}` `{{DRAFT_PATH}}`

## 输入(只读)
- `{{DRAFT_PATH}}`：待查的 rebuttal draft
- `harness/shared-assets/ammunition-checklist.md`：弹药类目 A–E 的定义(判据来源)

## 逐类语义查(理解句意,不匹配字面)
| 类 | 弹药 = | 关键语义区分(正则做不到的) |
|---|---|---|
| **A 自揭短/泄底** | 未测/尚未验证/due to time/we did not test;把没做说成局限而不带转折 | 陈述一个**已界定 scope 的限制**(带 however+证据)≠ 弹药;光秃秃"我们还没测 X"= 弹药 |
| **B 过度让步/认框架** | "we agree this is merely/just a combination";认了 novelty/soundness 攻击的框架且无转折 | 认 clarity/表达 ≠ 认贡献崩;**认一点+立刻重定位价值**≠ 弹药 |
| **B2 表演诚实(软弹药)** | "we honestly concede / will not manufacture / did not spin it / (conceded) 标签 / 反复 fair criticism" | 陈述事实一次 ≠ 弹药;**在正文反复声明"我很诚实"**= 弹药 |
| **C 空承诺 vs 合法编辑承诺** | 用承诺**搪塞 reviewer 要的实质/实验工作** | ⚠️**核心区分(修正旧判据)**:"we will run/add **experiments** / provide new results" 对 P0 **实质** concern = **弹药**(搪塞);但 `In the camera-ready version, we will define/redraw/add-citation/reorder X` 对**编辑请求**(定义术语/重画图/加引用/调顺序)= **合法且时态正确**(手稿编辑本就用将来时)。判"是拖延 reviewer 要的**实质/实验**,还是承诺一次**编辑修订**" |
| **C2 假装已改(overclaim,新增)** | 把**未落地**的手稿编辑写成 "is now stated / the revised X **reads** / we **have revised** X" | rebuttal 阶段论文通常还没 revise;把编辑写成现在(完成)时=谎报已完成=**overclaim**。编辑该用将来时 `we will`,**不是假装已改**(这是旧判据的错,现纠正) |
| **D 开新攻击面 / 轻描淡写 / over-claim** | 主动提没被问的弱点;"另一个可能的问题是…";**把实质反对说成"only a clarity issue"**;把 claim 扩到证据之外;无根据声称真实世界普遍性;引入答案不需要的新 promise/metric/setting/assumption | 回答 reviewer 问的 ≠ 弹药;主动招供 / 轻描淡写实质异议 / 越界声称 = 弹药 |
| **E 不诚实(红线)** | 把没做的实验说成做了 / 编造数字或引用 / 把 FAIL 报成 PASS / 夸大提升 | 直接失败,非改写 |

## 规则
1. **逐句读全文**,对每个可疑句判它属于哪类、为什么、给出**改写建议**(去弹药、保留事实)。
> 🔴 **你的任务是穷尽检出,不是裁决。** 驱动会按 §6 的类别表**在代码里重算** `verdict`,
> 并且把**连续 N 次调用的命中取并集**(默认 N=3)。所以:
> · 你自报的 `verdict` 只作参考,漏报一条命中才是真损失 —— 宁可多报可疑项,也不要漏。
> · 实测依据:同一份稿判 10 次,裁决 10/10 都忠实于 §6(不飘);飘的是**检出** ——
>   同一处实质过度声称(D 类)只有 60%(medium)/ 80%(xhigh)的次数被发现。
> · 逐句通读,不要抽样;每个可疑句都出一条 hit,类别拿不准就按更严重的那类报。

2. 任一 A–D 命中 → `verdict=HAS_AMMO`(拦 PASS,回炉按 rewrite 改)。**E 命中 → HAS_AMMO 且标 `red_line=true`**(造假,退回重做不改数字)。
3. **宁可漏报也别误伤好写法**:编辑类 `In the camera-ready we will …`、带正向条件的 scope 界定、一次性事实陈述——都不是弹药。判据是"这句是否给 reviewer 递了软肋 / 拖延实质工作 / 谎报已改",不是句式。
4. **deletion test(应答编译)**:另标每句是否**恰好承担**一个功能(答 slot / 定义 / 连接 / 证据 / camera-ready-edit);功能之外的句子标 `deletable`(冗余,建议删)——不算 HAS_AMMO,但记进 hits 供精简。
5. **direct-answer mirror check**:每个 W 块第一句是否**字面 mirror reviewer 的主/谓/宾**(不是 reframe/恭维);否则标 `not_direct`(建议改成字面直答)。
6. 有任一 A–D/C2 命中 → `verdict=HAS_AMMO`;全文无命中(deletable/not_direct 仅为建议)→ `verdict=CLEAN`。

## 输出(写这个确切文件)
`campaigns/{{SLUG}}/ledger/B3_{{REVIEWER}}_ammunition.json`:
```json
{ "verdict":"CLEAN|HAS_AMMO", "red_line":false,
  "hits":[ {"quote":"原句", "category":"A|B|B2|C|C2|D|E|deletable|not_direct", "why":"为什么(弹药/冗余/未字面直答)", "rewrite":"改法(保留事实)"} ] }
```
receipt：`{verdict, n_hits, red_line}`。
