# Contributing

## 提交前

```bash
bash scripts/selfcheck.sh      # 语法 / frontmatter / 命令链接 / 产出目录
```

## 声明纪律（最重要的一条）

`README.md` 的**能力分级**把功能分为 `Implemented / Experimental / Roadmap` 三档。

- 新增功能时，**必须同时更新这张表**。
- **没有对应代码的能力不得写进 Implemented。** 已实现但没做过对照测量的，放 Experimental。
- 涉及评分、排序、novelty 判断的改动，不要写成"更准""更好"，除非附上同模型、同预算、同检索范围下的对照数据。
- 本项目所有分数由 LLM 产生，不是同行评审。任何暗示分数能预测录用结果的表述都不会被接受。
- 方法论来自他人工作的，在 `README.md` 的致谢一节注明出处。

## 加一个 skill

1. `skills/<name>/SKILL.md`，frontmatter 至少含 `name`、`description`、`argument-hint`、`allowed-tools`。
2. 挂上命令：`ln -s ../../skills/<name>/SKILL.md .claude/commands/<name>.md`（**用符号链接，不要复制**，否则会与 SKILL.md 失同步）。
3. 在 `README.md` 的 Slash Commands 表和 `CLAUDE.md` 的 Skills 表各加一行。
4. 外部模型调用必须写明失败时的降级路径——**pipeline 不允许停下来等用户输入**（唯一例外是 `-- mode: socratic-human`）。

## 加一个会场 profile

复制 `venue-profiles/_template.md`，填 calibration tiers（三档 + verdict_range）与 3 个 reviewer persona（`focus` / `accept_when` / `reject_when`）。

约束：profile 是对**公开**评审标准的归纳。不要提交来自任何会议内部材料、非公开审稿数据、或可识别到具体审稿人的内容。措辞保持中性的评审校准描述。

## 写节点时的坑

`tools/dedup_ideas.py` 用文本重叠找候选重复对。**不要给多个节点填同一句占位/模板文本**（例如所有 `thesis` 都写"待补充"）——那会让该字段的相似度恒为 1.0。工具已内置样板检测（被 ≥3 个节点逐字复用的字段值会在比较时跳过），但更好的做法是留空该字段而不是填模板。

## 输出语言

产出文件用中文，技术术语保留英文。代码注释与 commit message 中英皆可。

## 不要提交

- 运行产出（`outputs/`、`refine-logs/`、`archive/`）——已在 `.gitignore`
- API key、SSH 凭证、服务器地址与内网主机名
- **未发表的研究内容**。提 issue 或 PR 时，如需举例，请用公开已发表的研究方向，不要粘贴你正在做但尚未发表的 idea 或提案
