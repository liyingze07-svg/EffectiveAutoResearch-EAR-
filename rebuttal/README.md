# AutoRebuttal

> **从审稿人的疑问出发，用证据组织回应，在迭代中打磨论证。**

Rebuttal 的难点，不只是把回复写得更流畅：哪些疑虑真正影响了审稿人的判断？论文中的哪些内容可以直接回应？哪些问题需要补充实验？如何在有限篇幅中把关键证据讲清楚？

AutoRebuttal 将这些工作串成一条面向 **EMNLP / ACL Rolling Review（ARR）** 的审稿回复工作流。输入论文、审稿意见和回复任务卡，从证据映射与疑虑诊断开始，经过策略起草、多模型审查和逐轮修改，生成面向各位目标审稿人的回复草稿，以及给领域主席（Area Chair，AC）的说明。

**18 个阶段提示词 · 两条迭代循环 · 四道审查关卡 · Codex × DeepSeek**。

你可以只使用现有证据完成回复，也可以在配置实验执行环境后启用实验循环，将通过验收的新增结果纳入论证。最终文本之外，工作流还保留证据对应关系、各审稿人的处理结果和交付记录。

本项目属于 [EAR — Effective Auto Research](../README.md)。请使用完整的 EAR 仓库；共享的环境配置与安全工具位于仓库根目录。

[核心工作流](#workflow) · [四道审查关卡](#gates) · [快速开始](#quick-start) · [输出文件](#outputs) · [单独使用评审器](#standalone) · [运行配置](#runtime)

---

## 从一组审稿意见，到一套回复材料

AutoRebuttal 围绕三个输入组织任务：

| 输入 | 内容 | 在工作流中的作用 |
| --- | --- | --- |
| **论文源码** | LaTeX 主文件及其引用的章节文件 | 为论断、数值和方法说明提供来源 |
| **完整审稿意见** | 保留审稿人 ID、原始评分和意见文本 | 明确每位审稿人的疑虑与回复对象 |
| **回复任务卡** | 论文信息、审稿人评分、目标列表及运行限制 | 指定本轮回应谁、追求什么目标，以及如何运行 |

产出也不只是一份长文档，而是按沟通对象与证据记录分别整理：

| 产出 | 保存位置 | 用途 |
| --- | --- | --- |
| **审稿人回复草稿** | `campaigns/<case>/drafts/<reviewer>.md` | 分别回应选定审稿人的意见 |
| **AC 说明** | `campaigns/<case>/AC_COMMENT.md` | 整理需要向领域主席传达的信息 |
| **证据与处理记录** | `campaigns/<case>/ledger/` | 查看论断依据、各审稿人的处理结果与待解决事项 |

草稿和记录保存在本地案例目录中。工作流负责起草与打包，不会自动向会议提交回复。

---

<a id="workflow"></a>

## 核心工作流：先找准疑虑，再写出回应

AutoRebuttal 将**证据准备**和**回复打磨**分成两条循环。前者处理可选的补充实验，后者处理面向审稿人的文字与论证；两者通过证据合并阶段衔接。

```text
论文 + 审稿意见 + 回复任务卡
          │
          ▼
r0a 任务卡提取（任务卡已准备好时，可从 r1 开始）
          ▼
r1 证据映射 → r2 疑虑诊断 → B1 疑虑关卡 → r3 分流
          │
          ├─ 仅写作：沿用现有证据
          │
          └─ 可选实验循环
             S-ante 前置关卡 → r4 执行 → 代码审计 → S-exp 说服力关卡
             未达到要求 → 重新设计并运行，或明确记录尚未解决的问题
          │
          ▼
r5 证据合并：新增实验仅纳入通过验收的结果
          ▼
审稿人回复循环
沿策略阶梯起草 → r7 共识关卡 → B2 忠实性关卡 → B3 把柄检查
未通过 → 根据评审反馈重写；达到迭代上限 → 坦诚说明未解决的疑虑
          ▼
mt 多轮对话：交付前压力测试
          ▼
ac 打包：审稿人回复 + AC 说明 + 交付记录
```

### 1. 先弄清楚审稿人担心什么

流程从 `r1` 的证据映射和 `r2` 的疑虑诊断开始：一边整理论文论断与支持材料之间的关系，一边识别审稿意见中需要回应的问题。

随后，**B1 疑虑关卡**检查诊断是否抓住了审稿人真正关心的内容，再进入 `r3` 分流。这样，回复的起点是明确的问题与对应材料，而不是先生成一段通用的感谢和解释。

已经准备好任务卡时，可以直接从 `r1` 进入。需要模型协助提取任务卡信息时，则使用默认的 `r0a` 入口。

### 2. 把“补充证据”和“修改措辞”分开处理

仅写作模式直接使用已有证据，不启动新实验。需要补充实验时，可以启用独立的实验循环：

```text
前置检查 → 实验执行 → 代码审计 → 说服力检查 → 证据合并
```

实验先经过 `S-ante` 前置关卡，再由 `r4` 执行，随后接受代码审计和 `S-exp` 说服力检查。如果结果不足以回应疑虑，流程可以继续重新设计与运行，或记录仍然无法解决的问题。

**只有通过验收的新增实验才进入 `r5` 证据合并。** 实验运行和证据采用是两个不同步骤，后续写作围绕合并后的材料展开。

### 3. 沿策略阶梯起草，用审查反馈驱动修改

审稿人回复循环使用 `harness/strategies/` 中的写作策略，结合共享的 `CRAFT.md` 与 `s1/s2/s3`，按预设阶梯起草。

默认情况下，流程在首个草稿通过关卡后停止继续尝试策略。需要在每轮展开全部策略时，可以使用 `--fanout-all`。

草稿依次进入 **r7 共识、B2 忠实性和 B3 把柄检查**。未通过时，根据评审反馈重写；达到迭代上限后，保留对未解决疑虑的坦诚说明，并记录对应状态。

这使每轮修改都有明确来源：不是单纯要求“再写好一点”，而是针对上一轮审查指出的问题继续调整。

### 4. 在交付前进行多轮对话压力测试

审稿人回复循环之后，`mt` 阶段通过多轮对话对草稿进行交付前压力测试。该环节的轮数由 `--mt-rounds` 控制，与回复循环的 `--max-iter` 分开设置。

最后，`ac` 阶段整理回复草稿、AC 说明和交付索引。尚未解决的问题会继续保留在处理记录中，便于与最终文本一起查看。

---

<a id="gates"></a>

## 四道审查关卡：分别检查问题、论证和证据

四道关卡承担不同任务。B1 位于诊断之后；r7、B2 和 B3 位于回复循环中。

| 关卡 | 核心问题 | 检查内容 |
| --- | --- | --- |
| **B1 · 疑虑识别** | 回应的是审稿人真正关心的问题吗？ | 检查诊断是否准确捕捉了审稿人的疑虑 |
| **r7 · 跨模型家族共识** | 论证是否达到了该评分区间的要求？ | 由不同服务商的两个模型判断回复的说服力 |
| **B2 · 忠实性** | 数值、引用和实验依据能否追溯？ | 检查证据来源，以及是否把未通过验收的实验用于论证 |
| **B3 · 把柄检查** | 草稿是否出现削弱自身论证的表述？ | 检查自损表述、空泛承诺和夸大论断；采用语义判断，而不是正则匹配 |

实验循环中的 `S-ante` 与 `S-exp` 分别负责实验前置检查和结果说服力检查，与这里的四道主关卡分开处理。

### 根据审稿人的初始评分设置回复目标

不同评分区间采用不同的评审侧重点与停止标准。OA 指审稿人在回复前给出的总体评分。

| 初始评分 | 回复目标 | 评审侧重点 |
| --- | --- | --- |
| **OA ≤ 2** | 回应关键疑虑，争取提分 | 回复是否具备促使审稿人提高评分的说服力 |
| **OA = 3** | 打磨临界评分下的回应 | 重点考察回复质量与提分潜力 |
| **OA ≥ 4** | 稳住已有评分 | 回应疑虑，并维持审稿人对论文的支持 |

EMNLP 评审器提供通用模板，也为 **OA=3 的临界评分审稿人**提供专门的诊断器。

### 写作与评审如何分工

在线运行显式区分 Codex 写作模型与评审模型，并通过 DeepSeek 引入第二家服务商。

| 角色 | 配置方式 | 作用 |
| --- | --- | --- |
| **Codex 写作端** | `--model` | 执行写作相关任务 |
| **Codex 评审端** | `--judge-model` | 使用与写作端不同的模型 ID 执行评审任务 |
| **DeepSeek** | `rebuttal_verifier/.env` | 作为第二家服务商参与跨模型家族共识 |

两个 Codex 模型 ID 都需要在当前账户下可用。只使用单一模型家族时，可显式选择 `--no-deepseek`；运行记录会反映实际采用的模式。

---

<a id="quick-start"></a>
<a id="install-and-run"></a>

## 快速开始

推荐先运行无凭据的离线演示，再用现有论文证据完成一次仅写作任务。实验循环可在后续配置好执行环境后启用。

### 1. 克隆仓库，运行离线演示

离线演示只需要 **Python 3.10+**，无需模型账户、API Key 或第三方 Python 包。已经克隆 EAR 时，可以跳过克隆步骤。

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR

python3 scripts/doctor.py --offline
python3 scripts/offline_demo.py
```

演示提供模拟论文、两份审稿意见和一张任务卡，生成全部五份契约文件，并调用实际编排器执行 `--dry-run`。

预期输出：

```text
PASS: idea validation/report, five contracts, and synthetic rebuttal dry-run.
```

程序打印的临时目录中包含 `rebuttal/DRY_RUN.txt`。这一步展示输入、契约生成与流程衔接，不调用模型，也不生成审稿回复。

### 2. 准备在线运行环境

| 项目 | 要求 |
| --- | --- |
| 操作系统与 Shell | Linux / WSL2、Bash |
| Python | 3.10 或更新版本 |
| Codex CLI | 已完成登录认证；安装需要 Node.js 和 npm |
| 写作与评审模型 | 两个当前账户可以访问、彼此不同的 Codex 模型 ID |
| 第二家模型服务 | DeepSeek API Key，用于跨模型家族共识 |
| Python 依赖 | 在虚拟环境中安装 `requirements.txt` |

从 EAR 仓库根目录继续执行：

```bash
npm install -g @openai/codex
codex login                          # 已完成认证时可跳过

cd rebuttal
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

cp -n rebuttal_verifier/.env.example rebuttal_verifier/.env
```

编辑 `rebuttal_verifier/.env`，设置 `DEEPSEEK_API_KEY`，并检查其中的模型与服务端点配置。`cp -n` 会保留已有文件。凭据放在本地配置文件中，不写入回复任务卡或提交到版本库。

随后检查本地环境：

```bash
python3 ../scripts/doctor.py --component rebuttal
```

`doctor` 检查本地依赖，不会登录或访问模型服务。`AUTOREBUTTAL_ROOT` 通常根据仓库位置自动推断，只有需要指定其他根目录时才覆盖。

`requirements-server.txt` 用于 HTTP 验证服务，`requirements-research.txt` 用于研究与数据处理工具；主工作流不需要安装这两组可选依赖。

### 3. 添加论文与审稿意见

**后续配置和运行命令均在 `rebuttal/` 目录执行。** 为案例选择一个新名称，下面以 `my-paper` 为例：

```bash
mkdir -p papers/my-paper/Tex campaigns/my-paper
cp -n examples/offline-demo/REBUTTAL_CARD.json campaigns/my-paper/REBUTTAL_CARD.json
```

补齐以下输入：

```text
papers/my-paper/
  review.md                 完整审稿意见，保留审稿人 ID 和评分
  Tex/main.tex              LaTeX 主文件，以及同目录下被引用的章节文件

campaigns/my-paper/
  REBUTTAL_CARD.json         当前案例的论文信息、回复目标与运行设置
```

复制的任务卡包含模拟数据，需要替换为当前论文的标题、论断、初始疑虑、审稿人 ID 与评分、目标列表及字数限制。字段说明见 [REBUTTAL_CARD 结构定义](harness/templates/REBUTTAL_CARD.schema.json)。

审稿意见块使用以下格式，审稿人 ID 与任务卡保持一致：

```text
Official Review of Submission<number> by Reviewer <id>
```

格式可参考[模拟审稿意见](examples/offline-demo/review.md)。在 `target.require_raise_on` 或 `target.maintain` 中填写本轮需要回应的审稿人，并替换模板中的示例评分与目标。

首次仅写作运行时，保持 `allow_new_experiments: false`，将 `max_iter` 设置为 `1`。这样可以先用已有证据走通回复流程，再决定是否增加轮次或启用实验。

### 4. 生成案例契约

```bash
python3 harness/instantiate.py --slug my-paper
```

生成的五份文件分别记录本轮任务的不同方面：

| 文件 | 内容 |
| --- | --- |
| `CLAUDE.md` | 当前案例的执行指令 |
| `GOAL.md` | 回复目标 |
| `SPEC.md` | 任务约束 |
| `VERIFY.md` | 检查要求 |
| `RESOURCE.md` | 可用资源 |

`CLAUDE.md` 是沿用的文件名，不代表 Shell 工作流需要 Claude。

已有契约及其版本标记会保留。修改任务卡并确认需要重新生成契约时，再使用 `--force`；草稿与台账不会因此被清除。

### 5. 先查看执行计划

```bash
python3 harness/runner/orchestrate.py --paper my-paper --from r1 --dry-run
```

这会打印计划执行的阶段，不调用模型，也不修改案例产物。它用于检查流程衔接，不代替完整的输入校验或模型访问测试。

这里从 `r1` 开始，是因为任务卡已经准备完毕；默认入口 `r0a` 用于模型辅助的任务卡提取。

### 6. 指定写作与评审模型，启动在线运行

将两个占位符替换为当前 Codex 账户可访问的、彼此不同的模型 ID：

```bash
EAR_WRITER_MODEL="REPLACE_WITH_AVAILABLE_WRITER_MODEL"
EAR_JUDGE_MODEL="REPLACE_WITH_AVAILABLE_JUDGE_MODEL"

python3 harness/runner/orchestrate.py --paper my-paper --from r1 \
    --model "$EAR_WRITER_MODEL" --judge-model "$EAR_JUDGE_MODEL" \
    --max-iter 1 --mt-rounds 1
```

写作与评审模型通过参数明确指定，DeepSeek 使用前面配置的第二家服务商信息。

`--max-iter 1` 限制审稿人回复循环轮数，`--mt-rounds 1` 限制多轮对话轮数。两者都不是 Token、总耗时或支出上限；一次运行可能包含多次模型调用，并使用账户额度或产生费用。

---

<a id="outputs"></a>

## 输出文件：按审稿人查看回复，沿证据记录回看依据

所有案例产物集中在 `campaigns/<case>/`。以 `my-paper` 为例，核心交付结构如下；AC 说明和交付索引在打包阶段完成后生成。

```text
campaigns/my-paper/
  REBUTTAL_CARD.json          案例任务卡
  CLAUDE.md                  执行指令
  GOAL.md                    回复目标
  SPEC.md                    任务约束
  VERIFY.md                  检查要求
  RESOURCE.md                可用资源

  drafts/
    <reviewer>.md            每位目标审稿人的回复草稿

  AC_COMMENT.md              面向领域主席的说明

  ledger/
    evidence_map.json        论文论断与支持证据的对应关系
    loop_results.json        各审稿人的处理结果
    package.json             交付索引与仍待解决的事项
```

查看结果时，可以先阅读每位目标审稿人的草稿，再结合 `evidence_map.json` 回看依据，通过 `loop_results.json` 了解处理状态，最后查看 AC 说明与交付索引。

### 如何理解处理状态

| 状态或字段 | 含义 |
| --- | --- |
| `HONEST_CONCEDE` | 仍有未解决的疑虑，回复中需要保留对应说明 |
| `PASS_SINGLE_FAMILY` | 单一模型家族模式下的通过状态 |
| `cross_family=false` | 本次结果没有形成跨模型家族共识 |

草稿、关卡记录和交付索引分别描述内容与执行状态，查看时应结合使用。确认每位目标审稿人都有对应文件，并在 `ledger/` 中查看相关关卡和证据记录。

---

## 按任务需要调整运行方式

### 两种证据路径

| 模式 | 适用方式 | 配置 |
| --- | --- | --- |
| **仅写作** | 基于现有论文与证据起草、审查和修改回复 | 保持 `allow_new_experiments: false` |
| **包含新实验** | 在可选实验循环中运行补充实验，将通过验收的结果合并到证据中 | 启用新实验，并单独准备执行环境 |

实验是否启用，与 Shell 是否联网、是否允许不受限执行，是不同的配置。可以先完成仅写作流程，再按实验实际需要配置环境和权限。

### 恢复运行、展开策略与调整轮数

| 参数 | 作用 |
| --- | --- |
| `--from r6r7` | 上游产物已经具备时，从审稿人回复循环恢复运行 |
| `--max-iter N` | 限制审稿人回复循环轮数 |
| `--mt-rounds N` | 限制多轮对话轮数 |
| `--fanout-all` | 每轮按全部策略起草，不在首个通过的策略处停止 |
| `--no-deepseek` | 显式使用单一模型家族模式 |
| `--allow-network` | 允许生成的 Shell 命令联网，并启用实时搜索 |
| `--unsafe` | 显式允许实验阶段不受限制地执行，仅用于外部隔离环境 |

`--max-iter` 与 `--mt-rounds` 用于控制迭代规模。逐次调用的成本记录由 `harness/runner/cost.py` 管理，`scripts/cost_report.py` 可根据台账生成成本分析。

---

<a id="standalone"></a>

## 已经有回复草稿？单独使用评审器

`rebuttal_verifier/` 可以独立使用。准备一份包含审稿意见、候选回复与审稿人背景的验证案例，即可调用评审器，不必重新运行完整起草流程。

从 `rebuttal/` 目录开始，使用前面配置的虚拟环境与 DeepSeek：

```bash
cd rebuttal_verifier
python3 verify_rebuttal.py --case /path/to/your/case.json --template auto
```

这里的 `case.json` 是**验证器输入**，不是 `REBUTTAL_CARD.json`。

| 文件 | 服务于什么任务 | 主要内容 |
| --- | --- | --- |
| `REBUTTAL_CARD.json` | 管理整轮回复工作流 | 论文元数据、审稿人、目标与运行设置 |
| 验证器的 `case.json` | 审查一份候选回复 | 审稿意见、候选回复和审稿人背景信息 |

EMNLP 案例还需要提供 `initial_overall`，即回复前的总体评分，采用 5 分制。输入示例见 [EMNLP 验证器文档](rebuttal_verifier/README_emnlp.md)。

验证器还提供单个及批量验证命令行入口，以及可选的 HTTP 服务；HTTP 服务依赖单独列在 `requirements-server.txt` 中。

---

## 项目结构与开发入口

### 两个主要组件

| 组件 | 职责 |
| --- | --- |
| **`harness/`** | 流程框架（`v0.8`）：18 个阶段提示词、实验循环、审稿人回复循环、固定策略阶梯与四道关卡 |
| **`rebuttal_verifier/`** | 评审模板与跨模型家族共识关卡：EMNLP 通用模板、OA=3 专用诊断器，以及独立验证入口 |

阶段提示词以文件形式保存，不依赖特定执行引擎；`harness/runner/orchestrate.py` 负责流程编排。仓库同时保留早期 ICLR 模板，作为前身版本，不参与当前工作流。

### 目录索引

```text
harness/
  HARNESS.md                          工作流概览
  GOAL.md                             目标与停止条件相关说明
  LOOP.md                             审稿人回复循环
  EXPERIMENT_LOOP.md                   实验循环
  stages/*.md                         18 个阶段提示词
  strategies/                         CRAFT.md、s1/s2/s3 与固定策略阶梯
  shared-assets/                      把柄检查清单、实验阶梯、策略说明
  templates/                          契约模板与 REBUTTAL_CARD 结构定义
  runner/orchestrate.py               流程编排器
  runner/cost.py                      逐次调用的成本台账

rebuttal_verifier/
  prompt_template_emnlp.py             EMNLP 通用评审模板
  prompt_template_emnlp_oa3.py         OA=3 临界评分诊断器
  prompt_template.py                   早期 ICLR 模板
  consensus_gate.py                    跨模型家族共识关卡
  verify_rebuttal.py                   单个 / 批量验证命令行工具
  serve.py                             HTTP 服务

scripts/
  cost_report.py                       根据台账生成成本分析
  cascade_replay.py                    评审级联的离线回放
  test_orchestrate.py                  纯函数单元测试
  secret_scan.sh                      提交前凭据扫描

examples/
  offline-demo/                        完整模拟输入，用于根目录离线演示
  demo-argument-compiler/              模拟案例的契约文件展示
```

### 从哪个示例开始

`examples/offline-demo/` 包含模拟论文、审稿意见与任务卡，是运行离线检查的入口。

`examples/demo-argument-compiler/` 用于查看生成后的任务卡、目标、约束、检查与资源文件。它侧重展示契约形式；运行演示请使用包含完整输入的 `offline-demo/`。

---

<a id="runtime"></a>

## 运行配置与数据流

### 执行权限

默认 CLI 阶段使用各自声明的只读或 `workspace-write` 沙箱，不弹出审批提示，并关闭 Shell 网络访问。

| 配置 | 行为 |
| --- | --- |
| 默认执行 | 使用阶段声明的沙箱与写入范围，无审批提示，Shell 不联网 |
| `--allow-network` | 允许 Shell 联网并启用实时搜索 |
| `--unsafe` | 显式开放不受限制的实验执行，仅用于已从外部隔离的环境 |

Shell 网络开关不阻断 Codex 模型通信或直接的 DeepSeek API 调用。

需要不受限制宿主机访问权限的实验阶段，会在未显式提供 `--unsafe` 时被阻止。首次仅写作运行无需为此扩大权限；保持 `allow_new_experiments: false` 即可按该模式准备任务。

### 服务调用与本地记录

在线运行会将论文、审稿意见、草稿及相关工具结果发送给配置的 Codex/OpenAI、DeepSeek，或显式指定的其他服务端点。

案例目录、回执、日志和 CLI 会话历史可能在本地保留输入与输出。服务端保留方式取决于服务商及账户设置。完整说明见 [EAR 数据处理文档](../docs/operations.md#execution-safety-and-data-handling)。

---

## 许可证

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu.

详见 [LICENSE](../LICENSE)。
