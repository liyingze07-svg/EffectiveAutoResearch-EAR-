# VERIFY — {{SLUG}}（独立验证器）

**在 writer 自报 done 后，另起一个新窗口（与 writer 物理隔离）跑本文件。** 你是独立验证器：按冻结的 `SPEC.md` 重新独立核验本 campaign，出具绑定裁决 `ledger/ACQUITTAL.json`（ACQUIT 或 REJECT+理由）。**你不写 rebuttal、不改稿、不软化 SPEC、不看 writer 的"已验证"自报——你只独立核验；你也不改涨分门配置。**

**第一动作**：`ToolSearch select:mcp__codex__codex,mcp__codex__codex-reply,mcp__deepseek__chat`。读 `SPEC.md`、`REBUTTAL_CARD.json`、终稿 `drafts/final_rebuttal.md`、`inputs/reviews/`、`ledger/`（evidence_map / concern_ledger / round*-gate.json）。

## 逐条核验（对 SPEC，全部独立重做）
1. **A·涨分（跨家族合议)**：**自己独立重跑涨分门**——用 `{{HARNESS_DIR}}/shared-assets/verifier/` 的冻结 θ₀，对终稿逐 P0 reviewer 调 DeepSeek V4 Pro 与 Codex 各一遍（persona 带 initial_rating+子分+confidence，**绝不把最终 label 喂进去**）。要求**每个 P0 reviewer 上,DeepSeek 与 Codex 都返回 `raise`**。任一 P0 上任一判官不 raise → A 不过（除非走诚实让步出口）。**不信 writer 在 round*-gate.json 里的自报分,你自己重打。**
2. **B·覆盖**：逐个 P0/P1 concern 核对终稿是否明确回应。有漏 → REJECT。
3. **C·证据诚实**：抽查终稿每个数字/引用/claim。`recompute_check` 重算进正文数字 <1%（有算式对不上 raw → REJECT）；每条引用独立验存在性+相关性（编造引用 → REJECT）；每个"paper 已证明/我们做了"能定位到证据（无支撑却写成已完成 → REJECT）。理论常数等无 raw 算式的量 SKIP、不算失败。
4. **D·无弹药+无新攻击面**：终稿弹药 grep（`{{HARNESS_DIR}}/shared-assets/ammunition-checklist.md`）= 0；独立读一遍看有没有为回应 A 而开了 B 没提的新弱点；字数 ≤ {{WORD_LIMIT}}；正文无 `[TBD]`。
5. **E·独立性自检**：你没复用 writer 的门分结论；你的门调用 persona 没被 writer 过滤、没泄露 label。**iteration-cap={{MAX_ITER}}**（writer 最多 {{MAX_ITER}} 轮;你只核终态，不替它迭代）。

## 出裁决
写 `ledger/ACQUITTAL.json`：
```
{ "verdict": "ACQUIT|REJECT",
  "track": "raise|honest-concede",
  "A_consensus_raise": {"R1":{"deepseek":"raise|same|lower","codex":"raise|same|lower"}, ...},
  "A_all_p0_raise": <bool>,
  "B_coverage_ok": <bool>, "B_missed_concerns": ["..."],
  "C_recompute_max_relerr": <float>, "C_fake_citations": <int>, "C_unsupported_claims": <int>,
  "D_ammo_hits": <int>, "D_new_attack_surface": <bool>, "D_over_wordlimit": <bool>,
  "reasons": ["..."] }
```
**ACQUIT ⇔ A（所有 P0 跨家族合议 raise）∧ B（覆盖全）∧ C（证据诚实）∧ D（零弹药无新攻击面）∧ E（独立）。**
**只拦实打实造假**（数字对不上 raw / 引用不存在 / claim 无支撑却写成已完成 / 弹药>0）；协议措辞小差不当致命,提示改对即可。

**诚实让步出口**：若 {{MAX_ITER}} 轮仍不能合议涨分,但 B/C/D/E 全过且是最诚实的让步式 rebuttal → `{"verdict":"ACQUIT","track":"honest-concede","A_all_p0_raise":false}`。

你的裁决是本 campaign 的终判。
