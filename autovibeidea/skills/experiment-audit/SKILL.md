---
name: experiment-audit
description: "Audit experiment code for academic integrity: data leakage, baseline fairness, evaluation gaming, LLM-generated code tricks, and method-code alignment. Use when user says \"audit code\", \"check experiment\", \"审计代码\", \"检查实验\", \"code integrity\", \"实验审查\", or wants to verify that experiment code maintains academic standards before reporting results."
argument-hint: "[code-directory-or-file] [-- proposal: path/to/FINAL_PROPOSAL.md] [-- venue: ICML|NeurIPS|VLDB]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Experiment Audit — 实验代码学术诚信审计

Audit experiment code for academic integrity: **$ARGUMENTS**

## Overview

当 LLM 为研究 idea 编写实验代码时，可能引入**六类"无意识学术不端"**——这些不是恶意造假，而是模型为了让代码"跑通"或"出好结果"时自然产生的偏差。这个 skill 扮演**内部 Reproducibility Chair** 的角色，在实验结果报告之前对代码进行全面审计。

核心哲学：
1. **代码是方法的唯一真相。** 论文写什么不重要，代码做了什么才重要。
2. **公平比较是底线。** 对自己的方法和 baseline 必须一碗水端平。
3. **可复现是基本功。** 换一台机器、换一个 seed，结果不应该有本质差异。
4. **泛化是真正的贡献。** 只在特定 instance 上 work 的方法没有学术价值。

```
实验代码写完
  → Phase 1 (Claude): 代码扫描与结构理解
  → Phase 2 (Claude): 六大模块逐项审计
  → Phase 3 (Codex/GPT-5.4): 独立交叉代码审计
  → Phase 4 (Claude): 综合评估与修复清单
  → Phase 5: 审计报告输出
```

## Constants

- **REVIEWER_MODEL** = `gpt-5.4` — 用于独立代码审计的外部模型。（**模型可用性依赖账号**：用 ChatGPT 账号登录的 codex 只能用账号自带模型，指定不支持的模型会被 400 拒绝。走 `--codex-cli` 时**不要传 `--model`**，让 codex 用默认模型；走 `--gpt-only` 时该模型必须对你的 OpenAI API key 可用。）
- **SEVERITY_LEVELS** = `{CRITICAL, WARNING, INFO}` — 问题严重程度。
  - `CRITICAL`: 必须修复，否则论文结果不可信（如数据泄露、评估作弊）
  - `WARNING`: 应当修复，否则审稿人会质疑（如缺少多 seed、baseline 不公平）
  - `INFO`: 建议改进，提升论文质量（如代码可读性、文档完整性）
- **VERDICT_OPTIONS** = `{PASS, CONDITIONAL_PASS, FAIL}`
  - `PASS`: 代码通过审计，可以报告结果
  - `CONDITIONAL_PASS`: 存在 WARNING 但无 CRITICAL，修复后可报告
  - `FAIL`: 存在 CRITICAL 问题，必须修复后重新审计
- **MAX_FILES_DEEP_SCAN** = `30` — 深度扫描的最大文件数（超出则按重要性排序取 top-30）

## Input

1. **`$ARGUMENTS`** — 必须包含以下之一:
   - 代码目录路径（e.g., `./experiments/`, `src/`）
   - 单个代码文件路径（e.g., `train.py`）
   - 如未指定路径，扫描当前工作目录下所有 `.py`, `.sh`, `.yaml`, `.json` 文件

2. **`-- proposal:` 指令**（可选但强烈推荐）— 指向 FINAL_PROPOSAL.md 或其他 proposal 文件。用于 Module E（Method-Code 一致性检查）。如未指定，尝试自动查找 `refine-logs/FINAL_PROPOSAL.md`。

3. **`-- venue:` 指令**（可选）— 目标会议，用于校准审稿人视角。默认 `ICML`。

### Parsing Logic

1. 解析 `$ARGUMENTS` 确定代码路径。
2. 解析 `-- proposal:` 获取 proposal 路径。如未指定，依次查找:
   - `refine-logs/FINAL_PROPOSAL.md`
   - `outputs/SCREENING_RANKED.md`（取排名第一的 idea 描述）
   - 如都找不到，Module E 将在无 proposal 参照的情况下运行（仅检查代码内部一致性）。
3. 解析 `-- venue:` 获取目标会议。

---

## Phase 1: 代码扫描与结构理解

在审计之前，先建立对实验代码结构的全局理解。

### Step 1.1: 发现代码文件

```
扫描目标目录，识别:
- 训练脚本 (train.py, run_*.py, main.py 等)
- 评估脚本 (eval.py, test.py, evaluate.py 等)
- 数据处理脚本 (data*.py, dataset*.py, preprocess*.py 等)
- 配置文件 (*.yaml, *.json, *.toml, config*.py 等)
- Baseline 实现 (baseline*.py, 或 baselines/ 目录)
- 工具脚本 (utils*.py, helpers*.py 等)
- Shell 脚本 (*.sh — 通常包含运行参数)
```

用 `Glob` 和 `Grep` 快速定位关键文件。如果文件总数超过 MAX_FILES_DEEP_SCAN (30)，按以下优先级排序:
1. 训练主循环（含 loss 计算的文件）
2. 评估脚本（含 metric 计算的文件）
3. 数据加载/处理文件
4. 配置文件
5. 其余文件

### Step 1.2: 构建代码地图

读取关键文件，输出一份简要的代码结构图:

```markdown
## 代码结构
- 训练入口: train.py (L1-L300)
  - 数据加载: data_loader.py → Dataset 类
  - 模型定义: model.py → ProposedModel 类
  - Loss: losses.py → combined_loss()
  - 评估: eval.py → evaluate()
- Baseline:
  - baselines/method_a.py → MethodA 类
  - baselines/method_b.py → MethodB 类
- 配置: config.yaml
- 运行脚本: run_all.sh
```

### Step 1.3: 识别数据流

追踪数据从原始输入到最终 metric 的完整流向:

```
原始数据 → 预处理 → 数据切分 → 训练集/验证集/测试集
                                    ↓           ↓
                               模型训练    →  评估 → 报告 metric
```

特别关注:
- 预处理参数（mean, std, vocabulary, tokenizer）是在哪里计算的？用了哪些数据？
- 数据切分是什么时候做的？切分之前有没有已经用到了全量数据？
- 有没有从测试集反向流入训练流程的信息？

---

## Phase 2: 六大模块逐项审计

对每个模块中发现的每个问题，记录:
- **问题编号**: `A-01`, `B-02` 等（模块前缀 + 序号）
- **严重级别**: CRITICAL / WARNING / INFO
- **文件位置**: `file_path:line_number`
- **问题描述**: 具体说明什么代码有什么问题
- **影响**: 这个问题会如何影响实验结果的可信度
- **修复建议**: 具体的代码修改建议

### Module A: 数据管线完整性 (Data Pipeline Integrity)

检查数据处理流程中是否存在信息泄露或不当操作。

#### A.1 数据泄露检测

搜索以下模式:

```python
# 反模式 1: 预处理统计量使用了全量数据（含 test）
# 搜索关键词: fit(), fit_transform(), .mean(), .std(), .vocab
# 检查这些操作的输入是否包含测试集数据

# 反模式 2: 特征工程泄露标签信息
# 搜索关键词: target_encode, label_encode (在非目标列使用目标信息)
# 检查是否在特征构建时使用了 y/label/target

# 反模式 3: 时序数据的未来信息泄露
# 搜索关键词: shift(), rolling(), 检查窗口方向
# 检查是否使用了未来时间步的数据

# 反模式 4: 数据切分后的跨集污染
# 搜索: train_test_split 的调用位置
# 检查切分是在预处理之前还是之后

# 反模式 5: 数据增强泄露
# 检查: 增强后的样本是否可能横跨 train/test（如同一张图片的不同 crop 分别在 train 和 test）
```

具体搜索策略:
1. 用 `Grep` 搜索 `fit_transform|\.fit\(|\.mean\(|\.std\(|normalize|standardize|vocab` 等关键词
2. 对每个匹配，追溯其输入数据来源，判断是否包含测试集
3. 用 `Grep` 搜索 `train_test_split|split|\.train\b|\.test\b|\.val\b` 确定切分位置
4. 检查切分调用与预处理调用的相对顺序

#### A.2 数据过滤审查

```python
# 反模式: 静默过滤"难"样本
# 搜索: filter, drop, remove, skip, ignore, mask (在数据集上下文中)
# 检查: 过滤条件是否合理？是否同时应用于所有方法？
# 特别注意: 基于模型输出的过滤（如 "confidence > 0.5 的样本才参与计算"）
```

#### A.3 数据切分合理性

```python
# 检查点:
# 1. 是否使用固定 seed 进行切分？
# 2. 切分比例是否合理且标准？
# 3. 对于有结构的数据（时序、用户、组），是否按结构切分？
# 4. 验证集和测试集是否严格分开？
# 5. 是否存在验证集被当作测试集使用的情况？
```

### Module B: Baseline 公平性 (Baseline Fairness)

这是审稿人最容易攻击的点。LLM 写代码时往往对自己的方法精心调优，对 baseline 草草实现。

#### B.1 资源公平性

对每个 baseline 和 proposed method 检查:

| 检查项 | 具体检查内容 |
|--------|------------|
| **学习率** | 是否所有方法使用了等效的学习率 schedule？proposed method 是否享有更精细的 warmup/decay？ |
| **训练轮次** | 所有方法是否训练了相同的 epoch/step 数？是否有方法提前停止但其他方法训练更久？ |
| **模型容量** | 参数量是否在同一量级？proposed method 是否使用了更大的 backbone？ |
| **数据增强** | 是否所有方法享有相同的数据增强策略？proposed method 是否独享某些增强？ |
| **预训练权重** | 是否所有方法使用了相同来源、相同版本的预训练权重？ |
| **超参搜索预算** | proposed method 是否享有更多的超参调优轮次？ |
| **推理时计算** | 测试时间计算量是否等价？如有 ensemble 或 test-time augmentation，是否公平应用？ |

搜索策略:
1. 用 `Grep` 搜索 `lr|learning_rate|num_epochs|batch_size|warmup|weight_decay` 等超参关键词
2. 对比 proposed method 和每个 baseline 的配置差异
3. 特别检查: 是否存在只对 baseline 设置的 `max_epochs` 限制
4. 检查 baseline 代码是否来自官方实现（搜索 import 和 comment 中的来源信息）

#### B.2 实现完整性

```python
# 反模式 1: Baseline 使用了简化版实现
# 检查: baseline 代码中是否有 "simplified", "basic", "simple" 等注释
# 检查: baseline 是否缺少原论文中的关键组件

# 反模式 2: Baseline 使用了过时的超参
# 检查: baseline 的超参是否与其原论文一致

# 反模式 3: Baseline 缺少必要的 trick
# 检查: 如 baseline 原论文使用了 label smoothing、mixup 等 trick，
#       这里的实现是否也包含？

# 反模式 4: 给 baseline 设置了不利的默认参数
# 检查: baseline 的默认配置是否是其最优配置？
```

#### B.3 Baseline 代码来源验证

```
对每个 baseline:
1. 检查是否有注释标明来源（官方 repo、第三方实现、自行实现）
2. 如果是自行实现，标记为 WARNING: "Baseline [X] 为自行实现，非官方代码。
   建议验证其性能是否与原论文报告一致。"
3. 如果使用官方代码，检查版本是否为最新稳定版
```

### Module C: 评估协议合规性 (Evaluation Protocol Compliance)

#### C.1 随机性控制

```python
# 检查点:
# 1. 是否设置了全局 random seed？
#    搜索: seed, random_state, torch.manual_seed, np.random.seed, random.seed
# 2. 是否运行了多个 seed？(至少 3 个，建议 5 个)
#    搜索: seeds = [...], for seed in, --seed
# 3. 是否报告了 mean ± std？
#    搜索: mean, std, ±, standard deviation
# 4. CUDA 随机性是否控制？
#    搜索: torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark
# 5. 是否有 seed shopping 的迹象？
#    检查: 是否只报告了最好的 seed？seed 列表中的值是否有选择性？
```

#### C.2 Metric 合规性

```python
# 检查点:
# 1. 使用的 metric 是否是该任务的标准 metric？
#    对照该领域的 benchmark 惯例
# 2. 是否报告了所有标准 metric，还是只报告了有利的？
#    标记: 只报告 1 个 metric 时为 WARNING
# 3. 是否存在自定义 metric？
#    如有，检查其定义是否合理，是否有利于 proposed method
# 4. 高是好还是低是好？metric 方向是否一致？
# 5. 是否有统计显著性检验？
#    搜索: t-test, wilcoxon, bootstrap, p-value, significance
```

#### C.3 Checkpoint 选择

```python
# 反模式: 用测试集选最优 checkpoint
# 搜索: best_model, save_best, early_stopping
# 检查: 选择 "best" checkpoint 的依据是验证集还是测试集？
# 正确做法: 在验证集上选 checkpoint，然后在测试集上报告一次性结果
#
# 反模式: 多次在测试集上评估并报告最好一次
# 搜索: 测试集评估的调用频率和结果记录方式
```

#### C.4 结果报告完整性

```python
# 检查点:
# 1. 所有实验的结果是否都被报告了？（不能只挑好的）
# 2. 失败的实验或 negative result 是否被记录？
# 3. 计算资源消耗是否被报告？（GPU 小时、内存使用）
# 4. 推理延迟/吞吐量是否被报告（如果是效率相关的 contribution）？
```

### Module D: 代码特异性检测 (Code Specificity Detection)

这是 LLM 生成代码最容易出问题的地方。LLM 倾向于为特定 instance 编写"刚好能用"的代码。

#### D.1 Hard-coded 值检测

```python
# 搜索: 所有代码中的数字常量（非 0, 1, 2 等常见值）
# 对每个 hard-coded 数字，问:
# 1. 这个值是超参数吗？是否应该放在配置文件中？
# 2. 这个值是 dataset-specific 的吗？（如 num_classes=10 只对 CIFAR-10 有效）
# 3. 这个值是怎么得到的？是否有注释说明来源？
# 4. 如果换一个数据集，这个值还成立吗？
#
# 特别关注:
# - 隐藏在代码中的阈值（如 if confidence > 0.73）
# - 特定维度数（如 hidden_dim=768 直接 hardcode 而非从配置读取）
# - Loss 权重（如 loss = 0.7 * loss_a + 0.3 * loss_b 中的 0.7 和 0.3）
```

#### D.2 条件分支特异性

```python
# 反模式: 针对特定数据集或特定样本的条件分支
# 搜索: if.*dataset.*==, if.*name.*==, if.*"CIFAR", if.*"ImageNet"
# 检查: 这些条件分支是否是合理的适配（如不同数据集的 num_classes）
#       还是不合理的特殊处理（如特定数据集使用不同的 loss）？
#
# 反模式: 针对特定输入形状的硬编码
# 搜索: reshape, view 中的具体数字
# 检查: 这些形状变换是否与数据格式绑定？
```

#### D.3 配置外部化检查

```python
# 检查所有应该是可配置的值是否确实从配置文件读取:
# 1. 模型架构参数（层数、维度、头数等）
# 2. 训练超参（学习率、batch size、epoch 数等）
# 3. 数据路径
# 4. 评估参数
# 5. 硬件相关配置
#
# 标记: 在代码中直接写死但应该可配置的值
```

#### D.4 泛化性结构检查

```python
# 核心问题: 这份代码能否不经修改（或仅改配置）运行在另一个数据集上？
#
# 检查:
# 1. 数据加载是否参数化？(路径、格式、列名等可配置)
# 2. 模型输入输出维度是否参数化？
# 3. 预处理流程是否通用？
# 4. 是否有 dataset-agnostic 的抽象层？
# 5. 如果换一个相同 domain 但不同分布的数据集，代码能否直接运行？
```

### Module E: Method-Code 一致性 (Method-Code Alignment)

如果有 proposal 文件可供参照，逐项对比 proposal 描述的方法与代码实际实现。

#### E.1 算法步骤对齐

```
对 proposal 中描述的每个算法步骤:
1. 找到对应的代码实现
2. 检查代码是否忠实实现了描述的逻辑
3. 标记缺失的步骤: proposal 中有但代码中没有
4. 标记多余的步骤: 代码中有但 proposal 中没描述（"bonus step"）
```

**"Bonus step" 是最危险的信号。** 如果代码中有 proposal 未描述的步骤，这些步骤可能:
- 是让方法 work 的关键 trick（应该写进论文）
- 是对特定数据集的 hack（应该删除）
- 是 LLM 自作主张添加的"优化"（需要审查）

#### E.2 Loss 函数对齐

```python
# 检查:
# 1. 代码中的 loss 公式是否与 proposal 中描述的一致？
# 2. Loss 的各项权重是否与 proposal 一致？
# 3. 是否有 proposal 未提及的正则化项？
# 4. 是否有条件性 loss（某些情况下关闭某个 loss 项）？
```

#### E.3 架构对齐

```python
# 检查:
# 1. 模型架构（层数、维度、激活函数等）是否与 proposal 一致？
# 2. 是否有 proposal 未提及的 skip connection、dropout、normalization？
# 3. 推理路径是否与 proposal 描述一致？
# 4. 训练 vs 推理模式是否有未说明的差异？
```

#### E.4 无 Proposal 模式

如果没有找到 proposal 文件:
1. 跳过步骤对齐检查
2. 仍然进行代码内部一致性检查:
   - 代码注释与实际逻辑是否一致？
   - README/docstring 描述与代码是否一致？
   - 配置文件中的参数名与代码中的使用是否一致？
3. 标记: "⚠️ 无 proposal 参照。Module E 仅执行代码内部一致性检查。建议提供 proposal 文件以启用完整对齐验证。"

### Module F: LLM 代码陷阱检测 (LLM Code Trap Detection)

这是本 skill 最具特色的模块。专门检测 LLM 生成代码时常见的"看起来像在学习，实际上在作弊"的模式。

#### F.1 Pattern Matching 伪装学习

```python
# 反模式: 用 if-else / 字符串匹配 / 正则 / lookup table 代替真正的模型学习
# 搜索:
#   - 大量 if-elif 链条（>5 个分支）在推理路径中
#   - dict / hashmap 用于直接映射输入到输出
#   - 字符串模板用于构造"预测"结果
#   - 硬编码的答案列表
#
# 核心问题: 模型的预测是通过学习得到的，还是通过规则匹配得到的？
# 如果去掉所有规则匹配部分，模型还能工作吗？
```

#### F.2 Memorization 检测

```python
# 反模式: 模型或代码记住了训练/测试样本
# 检查:
# 1. 是否有嵌入在代码中的数据样本？
#    搜索: 长字符串常量、硬编码的向量/矩阵、json 中的样本数据
# 2. 训练过程是否有 overfit 的迹象？
#    检查: 是否有训练到 100% 训练精度才停止？
# 3. 测试样本是否出现在训练代码中？
#    搜索: test_data, eval_data 在训练循环中的引用
```

#### F.3 "Helper" 函数暗箱操作

```python
# 反模式: 看起来无害的 helper 函数实际上在做核心工作
# 检查:
# 1. utils.py 或 helpers.py 中是否有看似通用但实际上包含模型逻辑的函数？
# 2. "post-processing" 步骤是否实际上是方法的核心组件？
#    如果去掉 post-processing，性能下降多少？
# 3. "数据预处理" 是否实际上在做特征工程？
#    预处理应该对所有方法公平，而非只对 proposed method 有利
```

#### F.4 训练时信息泄露

```python
# 反模式: 通过巧妙的抽象在训练时访问测试时信息
# 检查:
# 1. DataLoader 是否在某些模式下返回标签/答案？
# 2. 模型的 forward() 方法在训练模式和评估模式下是否有不当差异？
# 3. 是否存在 "teacher forcing" 在测试时仍然开启的情况？
# 4. Global 变量或类属性是否在训练时存储了不应该存储的信息？
```

#### F.5 代码克隆检测

```python
# 反模式: 代码本质上是从已有 solution 复制的，只是变量名不同
# 检查:
# 1. 代码结构是否与某个知名开源实现高度相似？
# 2. 注释或变量名中是否残留了其他项目的痕迹？
# 3. 如果 proposed method 与 baseline 的代码高度相似，
#    是否真的有本质性的方法差异？
```

---

## Phase 3: 独立交叉代码审计

将关键代码发送给外部 LLM 进行独立审计，避免"自己写的代码自己审"的 bias。

### Step 3.1: 准备审计材料

提取以下材料供外部 LLM 审计:
1. **核心训练循环代码**（train loop + loss computation）
2. **评估代码**（metric computation + result reporting）
3. **数据处理代码**（data loading + preprocessing + splitting）
4. **Baseline vs Proposed Method 的关键差异**
5. **Phase 2 中 Claude 发现的 CRITICAL 问题列表**（让外部 LLM 交叉验证）

如果代码量过大（> 500 行），只发送最关键的部分并附上代码结构摘要。

### Step 3.2: 外部 LLM 审计

```
mcp__codex__codex:
  model: REVIEWER_MODEL
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    你是一位顶级 ML 会议的 Reproducibility Chair。你的任务是审计以下实验代码，
    检查是否存在影响学术诚信的问题。

    这些代码是由 LLM 生成的，因此要特别警惕以下 LLM 特有的代码陷阱:
    1. 为特定数据集/样本量身定做的 hard-coded 值
    2. 用规则匹配伪装成模型学习
    3. 给 baseline 不公平的配置（更少的训练时间、更差的超参）
    4. 数据泄露（预处理统计量使用了测试集、特征工程泄露标签）
    5. 评估作弊（测试集选 checkpoint、seed shopping、只报告有利 metric）
    6. "Bonus step"——代码中有但论文中没描述的步骤（可能是 hack）

    ## 代码结构概览
    [CODE_STRUCTURE_SUMMARY]

    ## 核心训练代码
    ```python
    [TRAINING_CODE]
    ```

    ## 评估代码
    ```python
    [EVALUATION_CODE]
    ```

    ## 数据处理代码
    ```python
    [DATA_CODE]
    ```

    ## Proposed Method vs Baseline 关键差异
    [DIFF_SUMMARY]

    ## 先前内部审计发现的问题（请交叉验证）
    [CLAUDE_FINDINGS]

    请输出:

    ### 1. 独立发现的问题
    对每个问题:
    - 严重级别: CRITICAL / WARNING / INFO
    - 问题类别: 数据泄露 / Baseline不公 / 评估作弊 / 代码特异性 / LLM陷阱 / 其他
    - 具体位置: 文件名 + 代码行或函数名
    - 问题描述
    - 影响评估: 这个问题会如何影响实验结果？能否让结果虚高？偏差有多大？
    - 修复方案

    ### 2. 对先前发现的交叉验证
    对每个先前发现的问题:
    - 是否同意？
    - 如果不同意，理由是什么？
    - 是否需要调整严重级别？

    ### 3. 泛化性评估
    - 这份代码在其他数据集上能直接运行吗？
    - 哪些部分是 dataset-specific 的？
    - 需要修改什么才能泛化？

    ### 4. 总体评估
    - PASS / CONDITIONAL_PASS / FAIL
    - 最大的 3 个风险点
    - 如果是你审稿，你会因为代码质量提什么 concern？
```

**Codex MCP 失败处理**: 如果 `mcp__codex__codex` 不可用:
1. Claude 自行执行交叉审计（使用相同的审计维度）
2. 日志记录: "⚠️ Codex MCP 不可用。交叉审计由 Claude 执行（自审模式——客观性降低）。"
3. 对自审发现的 CRITICAL 问题数量乘以 1.2 系数（补偿自审时可能的漏检）
4. 继续流程，不中断。

### Step 3.3: 整合发现

合并 Phase 2（Claude 审计）和 Phase 3（外部 LLM 审计）的发现:
1. 去重: 两个来源发现的相同问题合并
2. 交叉验证: 如果两个来源对同一问题的严重级别不同，取较高者
3. 独立发现: 只有一方发现的问题标记来源
4. 争议: 如果两方对某问题有不同判断，保留两种观点

---

## Phase 4: 综合评估与修复清单

### Step 4.1: 计算模块得分

对每个模块（A-F），计算得分:

```
模块得分 = 10 - (CRITICAL数 × 3) - (WARNING数 × 1) - (INFO数 × 0.2)
下限为 0，上限为 10
```

### Step 4.2: 计算总体得分

```
AUDIT_SCORE = (
    0.25 × Module_A_score  +   # 数据管线完整性
    0.20 × Module_B_score  +   # Baseline 公平性
    0.20 × Module_C_score  +   # 评估协议合规性
    0.15 × Module_D_score  +   # 代码特异性
    0.10 × Module_E_score  +   # Method-Code 一致性
    0.10 × Module_F_score      # LLM 代码陷阱
)
```

### Step 4.3: 确定总体裁决

| AUDIT_SCORE | CRITICAL 数 | 裁决 |
|-------------|------------|------|
| >= 7.0 且 CRITICAL = 0 | 0 | **PASS** — 代码通过审计，可以报告结果 |
| >= 5.0 或 CRITICAL = 0 | 0 | **CONDITIONAL_PASS** — 修复 WARNING 后可报告 |
| < 5.0 或 CRITICAL > 0 | > 0 | **FAIL** — 存在严重问题，必须修复后重新审计 |

任何存在 CRITICAL 问题的代码自动 FAIL，无论总分如何。

### Step 4.4: 生成修复清单

按优先级排序所有问题:
1. **CRITICAL 问题（必须修复）**: 按影响范围从大到小
2. **WARNING 问题（应当修复）**: 按修复难度从低到高（先解决容易的）
3. **INFO 建议（可选改进）**: 按改善幅度排序

对每个问题提供:
- 具体的修复代码建议（不是笼统的方向）
- 预估修复时间
- 修复后的预期效果

---

## Phase 5: 审计报告输出

创建 `outputs/` 目录（如不存在）:
```bash
mkdir -p outputs
```

### `outputs/AUDIT_REPORT.md`

完整审计报告，包含所有模块的详细发现。

```markdown
# 实验代码审计报告

**审计目标**: [代码路径]
**Proposal 参照**: [proposal 路径 / 无]
**目标会议**: [venue]
**审计日期**: [YYYY-MM-DD]
**总体裁决**: PASS / CONDITIONAL_PASS / FAIL
**总体得分**: X.X/10

## Executive Summary

[2-3 段总结审计结果。发现了多少问题？最严重的问题是什么？总体代码质量如何？]

## 得分概览

| 模块 | 得分 | CRITICAL | WARNING | INFO |
|------|------|----------|---------|------|
| A. 数据管线完整性 | X.X/10 | N | N | N |
| B. Baseline 公平性 | X.X/10 | N | N | N |
| C. 评估协议合规性 | X.X/10 | N | N | N |
| D. 代码特异性 | X.X/10 | N | N | N |
| E. Method-Code 一致性 | X.X/10 | N | N | N |
| F. LLM 代码陷阱 | X.X/10 | N | N | N |
| **总计** | **X.X/10** | **N** | **N** | **N** |

## Module A: 数据管线完整性

### 发现

#### A-01 [CRITICAL] 预处理统计量使用了全量数据
- **位置**: `data_loader.py:45`
- **问题**: `StandardScaler.fit()` 在 train/test 合并后的全量数据上调用
- **影响**: 测试集信息泄入了预处理参数，测试集 metric 虚高
- **修复**: 将 `scaler.fit(all_data)` 改为 `scaler.fit(train_data)`，然后用 `scaler.transform(test_data)`

#### A-02 [WARNING] ...
[...]

## Module B: Baseline 公平性
[同结构]

## Module C: 评估协议合规性
[同结构]

## Module D: 代码特异性
[同结构]

## Module E: Method-Code 一致性
[同结构]

## Module F: LLM 代码陷阱
[同结构]

## 交叉审计结果

### 外部 LLM 独立发现
[列出外部 LLM 独立发现但 Claude 未发现的问题]

### 交叉验证结果
[列出两方一致的发现和分歧]

### 泛化性评估
[外部 LLM 对代码泛化性的评估]

## 总体评估
- **裁决**: PASS / CONDITIONAL_PASS / FAIL
- **CRITICAL 问题数**: N
- **最大风险点**:
  1. [风险1]
  2. [风险2]
  3. [风险3]
- **如果你是审稿人**: [模拟审稿人会提出的关于代码/实验的具体 concern]
```

### `outputs/AUDIT_CHECKLIST.md`

精简的可操作修复清单，供开发者直接执行。

```markdown
# 实验代码修复清单

**审计日期**: [YYYY-MM-DD]
**总体裁决**: PASS / CONDITIONAL_PASS / FAIL
**总体得分**: X.X/10

## CRITICAL — 必须修复（不修复则结果不可信）

- [ ] **A-01** `data_loader.py:45` — 预处理统计量用了全量数据
  - 修复: `scaler.fit(all_data)` → `scaler.fit(train_data)`
  - 预估时间: 10 分钟

- [ ] **C-03** `eval.py:120` — 用测试集选 checkpoint
  - 修复: 改为用验证集选 checkpoint，测试集仅在最终报告时使用一次
  - 预估时间: 30 分钟

## WARNING — 应当修复（审稿人可能质疑）

- [ ] **B-02** `config.yaml:15` — Proposed method 训练 200 epochs，baseline 仅 100 epochs
  - 修复: 统一训练轮次，或使用 early stopping
  - 预估时间: 5 分钟

- [ ] **C-01** `train.py:30` — 只使用了 1 个 random seed
  - 修复: 运行 3-5 个 seed，报告 mean ± std
  - 预估时间: N/A（需要多次运行）

## INFO — 建议改进（提升论文质量）

- [ ] **D-05** `model.py:78` — hidden_dim=768 硬编码
  - 修复: 移至配置文件
  - 预估时间: 5 分钟

## 修复后重新审计

修复完 CRITICAL 和 WARNING 问题后，建议重新运行 `/experiment-audit` 验证修复效果。
```

### Large File Handling

如果 `Write` 失败，使用 Bash heredoc:
```bash
cat << 'AUDIT_EOF' > outputs/AUDIT_REPORT.md
[content]
AUDIT_EOF
```

---

## Execution Order

1. **Parse input**: 确定代码路径、proposal 路径、venue。
2. **Phase 1**: 扫描代码文件，构建代码结构图和数据流图。
3. **Phase 2**: 逐模块审计（Module A → B → C → D → E → F）。Module A-D 可以并行执行，Module E 依赖 proposal 文件。
4. **Phase 3**: 整理 Phase 2 发现，发送给外部 LLM 交叉审计。
5. **Phase 4**: 整合两方发现，计算得分，确定裁决，生成修复清单。
6. **Phase 5**: 写入报告文件。

---

## Key Rules

1. **所有输出使用中文。** AUDIT_REPORT.md 和 AUDIT_CHECKLIST.md 中的问题描述、影响分析、修复建议均使用中文。代码片段、文件路径、技术术语保留英文。
2. **CRITICAL 问题零容忍。** 任何存在 CRITICAL 问题的代码必须判定为 FAIL，无论总分多高。学术诚信没有灰色地带。
3. **给出具体修复代码。** 不要只说"这里有问题"，要说"把第 45 行的 `scaler.fit(all_data)` 改为 `scaler.fit(train_data)`"。可操作性是这个 skill 的生命线。
4. **区分"合理适配"和"不当 hack"。** 不同数据集使用不同的 `num_classes` 是合理适配。不同数据集使用不同的 loss 函数是不当 hack（除非有充分理由）。
5. **双模型交叉验证。** Claude 的发现必须经过外部 LLM 交叉验证。两方独立发现的问题可信度更高。
6. **不要过度报告。** INFO 级别的问题不要超过 10 个。审计报告应该聚焦于真正影响结果可信度的问题，而非代码风格偏好。
7. **Fully autonomous operation.** 不要向用户提问、等待确认或提供选择。所有决策自主完成并记录。
8. **Large file handling**: 如果 Write 工具失败，用 Bash heredoc 写入。不需要询问用户。
9. **ALWAYS use `config: {"model_reasoning_effort": "xhigh"}`** for all Codex calls.
10. **如果代码量过大（> MAX_FILES_DEEP_SCAN），优先审计高风险文件。** 训练循环 > 评估脚本 > 数据处理 > 配置 > 其余。

## Composing with Other Skills

```
/idea-refine → [代码编写] → /experiment-audit  ← you are here → [修复] → [实验执行]
```

- **Input from `/idea-refine`**: `refine-logs/FINAL_PROPOSAL.md` — 用于 Module E 的 Method-Code 一致性检查。
- **This skill is independent**: 也可以独立使用，对任意实验代码进行审计。
- **Output**: `outputs/AUDIT_REPORT.md` 和 `outputs/AUDIT_CHECKLIST.md` 供开发者参考和修复。

审计 skill 是从 idea 到 paper 链条上的最后一道质量关卡。它的存在不是为了阻止研究，而是为了确保研究结果经得起审稿人的推敲。一份通过审计的代码，意味着研究者可以自信地报告结果，而不用担心被审稿人质疑实验设计。
