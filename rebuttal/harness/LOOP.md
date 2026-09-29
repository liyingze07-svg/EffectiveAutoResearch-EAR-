# LOOP.md — 显式循环协议(goal 模式)

> per-reviewer 的 r6→r7 循环。引擎按这个**确切步骤序列**跑,不即兴。停机判据见 `GOAL.md`。

## 每个 reviewer 的循环
```
seed = None                                   # carry-forward 种子(上轮 best + advice)
best_ever = None
for round in 1..max_iter:                     # max_iter 来自 card,默认 4
  # ① MoE 生成:每个策略一版(引擎无关,读 strategies/MANIFEST.json)
  drafts = [ engine(stages/r6_write.md, {reviewer, strategy: s, seed}) for s in MANIFEST ]
  # ② 便宜门:弹药 grep + DeepSeek 判官,选最高
  for d in drafts: d.ammo = ammo_hits(d); d.ds = deepseek_judge(case(reviewer, d))
  best = argmax(drafts, key=rank)             # bar_met > rp=high > ammo少 > reaction
  if best.ammo != []: seed = carry(best, "去掉弹药: "+best.ammo); continue   # 便宜拒,不调 Codex
  if not bar_met(best.ds): seed = carry(best, best.ds.advice); continue      # DeepSeek 没过
  # ③ 权威门:Codex(高 reasoning,分区路由),只在便宜门过了才调
  codex = codex_judge(case(reviewer, best))
  con = consensus(best.ds, codex, case)       # authoritative(OA=3) / strict(其余)
  if con.stop and best.ammo == []:
     record(reviewer, best, "PASS"); break     # 达标,退出该 reviewer 循环
  best_ever = better(best_ever, best)
  seed = carry(best, con.advice)               # ④ carry-forward:best 稿 + 裁判 advice + 要避开的弹药
else:
  record(reviewer, best_ever, "HONEST_CONCEDE")   # 轮尽 → 诚实让步
```

## carry-forward 种子(下一轮 r6_write 的输入)
```json
{ "prior_best_rebuttal": "<上轮最优正文>",
  "blocker": "<门给的 blocker>",
  "apply_advice": "<门给的 advice>",
  "avoid_phrases": ["<上轮泄漏的弹药句式>"] }
```
下一轮生成**在 prior_best 上改**(保留有效的、按 advice 补、删 avoid),不从零重写。

## 四条内建(防偷懒/防拟合/防浪费/防震荡)
1. **便宜门先行**:弹药/DeepSeek 没过绝不调昂贵的 Codex 权威判官。
2. **裁判意见驱动重写**:advice + avoid 喂回,不是换措辞碰运气。
3. **best-so-far** 防震荡(别把过的改差)。
4. **max_iter → 诚实让步**,不无限拟合。

## 路由(门不过时 advice 指向哪个阶段)
| 门的 advice 类型 | 回哪个 stage |
|---|---|
| 证据不足/需要数据 | r4(补真实验/文献,或 warrant 阶梯换证据) |
| 逻辑弱/没说到点 | r6(重建论证 DAG) |
| 误解了 concern | r2(重诊断) |
