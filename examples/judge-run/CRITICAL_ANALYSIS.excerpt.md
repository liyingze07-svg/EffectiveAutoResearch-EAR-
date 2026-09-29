# Critical Analysis: landscape 四维批判（节选 3/16）

**生成方**: Codex MCP, gpt-5.5, `model_reasoning_effort=xhigh`
**输入**: `LANDSCAPE.md` + `LANDSCAPE.json`（8 个预识别 gap）
**输出**: 16 条 critique manifest，作为 Phase 2b 生成 idea 的锚点

> 节选说明：原文 16 条，此处保留 3 条以展示格式。批判的对象是**已发表工作的公开主张**，
> 不含本项目未发表的方案。

## 维度 1：Unverified Assumptions

### CRITIQUE-01 — 人类一致性 ≠ 构念效度
- **Category**: Unverified Assumption
- **Description**: 领域常把"与人类偏好标签一致"当作 LLM judge 有效的证据。但人类一致性只是 reliability 目标，不等于 judge 测量的是 intended construct——一致也可能来自 shared shortcut、annotator bias 或 benchmark artifact。
- **Affected**: 主流 judge 评测基准与多个 panel/jury 方法
- **Why Exploitable**: 把 human-agreement、construct validity、robustness 三者分离的论文，将动摇当前 judge 验证 protocol 的根基。

### CRITIQUE-02 — Bias 类别的非可加性交互
- **Category**: Unverified Assumption
- **Description**: 现有 bias 分类（position / verbosity / familiarity / recency / provenance / prompt variance）被当作可分离因子。实际上它们可能交互：verbosity 改变 position bias；familiarity 看起来像 self-preference；provenance 标签改变 perceived expertise。
- **Affected**: 多 bias taxonomy 类工作
- **Why Exploitable**: factorial study 若显示 non-additive interactions，则 one-bias-at-a-time 的分类框架不完整。

### CRITIQUE-03 — Panel diversity 假设错误
- **Category**: Unverified Assumption
- **Description**: 多 judge 面板被假定能通过多样性降低方差，隐含假设是各 judge 的误差近似独立。若 judge 来自相近的预训练分布，误差高度相关，面板的有效规模远小于其名义规模。
- **Affected**: 多 judge 投票/聚合类方法
- **Why Exploitable**: 直接测量跨模型误差相关性并给出有效面板规模的论文，会改变面板方法的设计前提。

---

**Phase 2b 的硬约束**：每个生成的 idea 必须声明它攻击哪一条 `CRITIQUE-ID`，且 ≥50% 的 idea
各自锚定不同批判（单条批判最多支撑 3 个 idea）。本次 run 从 16 条批判产出 10 个 idea。
