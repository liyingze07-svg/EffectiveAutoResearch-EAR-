# rebuttal-tips.md — concern 分类学 + 应对手册（paper-agnostic）

四个来源提炼(MLNLP Paper-Rebuttal-Tips 28 条 / awesome-rebuttal / Paper2Rebuttal / Devi Parikh)。r2 用它分类,r6 写作时注入。**核心信条:Good rebuttal = Respect + Evidence + Clarity。行动而非承诺(Tip 12)。**

---

## 分类学(r2 打标签用)

### 类 I — 创新 / 动机 / 理论 / 边界
| concern | Poor Response（禁） | Recommended（论证 DAG 的 warrant 方向） |
|---|---|---|
| novelty 不足 / 只是组合 | "我们承认是组合但…"(认框架) | 甩消融:朴素组合会失败 → 组合非平凡 → 我们的机制才是贡献 |
| 贡献不清 | 重复 abstract | 一句话锚定唯一核心贡献 + 指到证据 |
| 动机弱 | 空谈重要性 | 具体失败案例/gap 证明问题真实存在 |
| 理论浅 | 堆公式 | 指出定理边界 + 说清它保证了什么 |
| limitation 讨论浅 | 加一段免责 | 精确划边界(在 X 内成立),把 limitation 变成 scope |

### 类 II — 表述 / 相关工作 / 沟通
| concern | Poor | Recommended |
|---|---|---|
| 写得不清楚 | "我们会改" | 直接在 rebuttal 里给清晰版 + 指 §定位 |
| related work 缺 | 罗列引用 | 差异化:我们 vs 他们在哪条轴上不同(带 warrant) |
| **reviewer 误读** | 逐字反驳 | 礼貌指出 paper 已在 §X 说明 + 引原文;不指责 |

### 类 III — 实验证据
| concern | Poor | Recommended |
|---|---|---|
| 缺 baseline / 缺和 Z 比 | "Z 不可比" | 补真实 baseline(公平 tuning)或指已有对比;真打不过就诚实让步+说 scope |
| 消融不足 | "已经够了" | 补关键消融证明每个组件必要 |
| 算力成本 | 回避 | 给真实数字 + 对比同类 |
| 泛化 | "应该能" | 补一个 held-out/跨域点 |
| 统计显著性 | 只报均值 | 补方差/显著性检验 |
| 数据泄漏 | 否认 | 说清 split 协议 |
| 可复现 | 承诺放码 | 现在就给关键细节/伪码 |

---

## 应对总则(写作时的 warrant 选择)
1. **误读**(misread)→ 类 II 打法:指位置 + 引原文,不补新东西。
2. **真实缺口**(gap)→ 类 III:补真实实验/文献,或诚实让步 + 划 scope。
3. **frame-lock** → 别逐条回,先用最强证据打破框架(如消融打破"只是组合")。

## Devi Parikh 心法(节选,写作 Avoid 清单)
- 别防御性/情绪化;假设 reviewer 善意。
- 别用"future work / camera-ready 再加"搪塞 P0(空承诺 = 弹药)。
- 先答最重要的(P0),别按 reviewer 顺序流水账。
- 每个回应自包含:reviewer 不该回去翻 paper 才懂。
- 给 AC 一句话:这篇为什么该收(confidential comment)。

## per-reviewer strategy matrix(awesome-rebuttal)
每个 reviewer 一套姿态,不统一:低分高信心的 P0 reviewer 是主战场(涨他的分最能提总分);高分 reviewer 维持即可,别节外生枝开新攻击面。
