# stage r4_experiment_run — 跑一个实验

> 新引擎上下文(Codex,tx-118)。experiment_request + 论文真码真数据 → 可验收产物。**产物之后会被另一个 Codex 过 X1-X6,绝不能造假。**

## 槽位 `{{SLUG}}` `{{EXPID}}`
## 输入(只读):`campaigns/{{SLUG}}/ledger/experiment_queue.json` 里 `{{EXPID}}` 的 request、`papers/{{SLUG}}/`(论文码/数据,**只读,绝不改、绝不 git**)。

## 规则
0. **先检查执行域**：若 `campaigns/{{SLUG}}/REMOTE_ONLY.md` 存在，必须先完整读取并遵守。该文件存在时，任何数据准备、统计、推理、训练、评测和 smoke run 都只能在文件声明的远端执行；本机只允许静态 lint、编排和保存小型摘要/哈希。不得因为任务是 CPU-only 就在本机运行。
1. 用论文**真实**数据/已有码;**绝不 np.random/合成/toy 当数据源**(bootstrap 重采样真数据可以)。
2. codex 写 `driver.py` → 本机静态 lint → 跑(CPU on tx-118;需 GPU → `ExpAuto/NewInfra/runner/zj.sh` ZJM=A + `gpu_lock.sh`,**全套 timeout**)→ 存 `{raw,derived}`。
3. **绝不编数字**；运行时限优先服从 experiment request 中显式注册的
   remote wall-time budget。未显式注册时默认 40 分钟。跑不出、数据缺或
   超时 → `status:failed|partial` + 原因（合法结局，下游走 warrant
   阶梯让步）。不得为了满足默认 40 分钟而截断一个 request 已明确允许
   更长时间、且正在正常收敛的多 epoch 远端训练。
4. 工作目录只 `campaigns/{{SLUG}}/experiments/{{EXPID}}/`。

## 输出(全放上面目录):`results.json`(`{raw,derived}`,derived 带 recipe)、`run.log`、`driver.py`、`manifest.json`(host/started_utc/duration_sec/seed_count/sample_count/data_source_path/**data_fingerprint**/model_id/cmd)。receipt:`{expid, status, key_numbers, data_source_path}`。
