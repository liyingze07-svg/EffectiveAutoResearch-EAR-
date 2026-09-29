# stage r4_experiment_accept — 实验代码审计门(加完实验后一次·两阶段)

> **由一个新的、没跑过这个实验的引擎执行**(DRIVE/ACQUIT 分离:跑的是一个引擎,审的是另一个)。
>
> **⚠️ 哲学(v0.8)**:验收 = **实验加完后,对代码审一次**——**不是**每次都重跑去证明"真的运行过"。
> 数据默认真实(我们自己控制数据源)。要审的是:**①代码对不对 / 有没有明显 bug ②跑完整没(有没有没跑完就把结果贴上来)
> ③有没有用假数据 ④有没有假模型 / 硬编数字。** 独立复跑降级为**可选抽查**(只在代码审计存疑时才做),**不是默认门**。

## 两阶段(v0.7 保留,去冗余)
- **建原点(审一次)**:做下面的代码审计,ACCEPT 后把 `driver_sha256` + `data_fingerprint` 记进 `origin_audit`。
- **便宜复核(每次)**:`orchestrate.accept_experiment` 查——driver 哈希 + 数据指纹都没变且原点 verdict∈{ACCEPT,PARTIAL} → **直接复用、不重审**;只有 **driver 改了 / 数据换了 / 没原点 / 上次 REJECT** 才重审。**"每次都重跑实验"被禁止。**

## 槽位
`{{SLUG}}` `{{EXPID}}` `{{DATA_SOURCE}}`（真实数据路径）`{{DRIVER_SHA}}`（orchestrator 算的 driver.py sha256,回写 origin_audit）

## 输入(只读)
`campaigns/{{SLUG}}/experiments/{{EXPID}}/`:`driver.py`(审计主对象)`results.json` `run.log` `manifest.json`;`{{DATA_SOURCE}}`(真实数据)。

若 `campaigns/{{SLUG}}/REMOTE_ONLY.md` 存在，必须先完整读取并遵守。验收侧可以在本机做静态代码审计和哈希检查，但任何数据读取、统计重算、模型加载或可选 spot rerun 必须在该文件声明的远端执行；不得在本机运行实验计算。

## 审计项(静态代码审计为主,加完实验后一次)
| # | 查什么 | 通过条件 |
|---|---|---|
| **C1 代码正确** | 有没有明显 bug | 静态读 `driver.py`:**算的是它声称的量**(与 `experiment_request`/goal 一致);无错索引 / 错聚合 / off-by-one / 单位或符号错 / 错误的 baseline;统计口径合理(如 CI 用对 seed) |
| **C2 跑完整** | 没跑完就贴结果? | `run.log` 有**完整收尾**(非中途 crash/timeout/秒退);`results.json` 含**所有声明的 cell/seed/sample**(声明 N seed 就得有 N;声明两臂就两臂都在);无"半截结果当全量" |
| **C3 真数据** | 用了假数据? | 代码从 `manifest.data_source_path` 读**真实数据**;**grep 不到 `np.random/randn/synthetic/fake/toy` 当数据源**(bootstrap 重采样真数据可以);`sample_count` 对得上真数据规模。**cheap 确认**:`manifest.data_fingerprint` 与真数据一致即可,不必每次独立重算 |
| **C4 无假模型/硬编** | mock / 编数字? | 无 `MockModel`/`return <canned>`/monkeypatch 返常数 / 硬编 `derived`;**点估计能从 raw 重算 <1%**(`recompute_check.py`);**过程派生值**(bootstrap CI/置换检验)标 `procedure_derived`,不要求蠢脚本重建。**"无模型"合法**:纯分析复用冻结真实产物(manifest 声明 no-model + 指纹兜底),不需模型加载 |
| **(可选)抽查复跑** | 存疑才做 | **仅当 C1–C4 有疑点**(如怀疑硬编/半截):取 1 seed / 少量样本用同 driver 同数据复跑对一下。**不是默认步骤**——代码审计过了就不必跑。 |

## 规则
- 全静态审 C1–C4;**默认不重跑实验**。抽查复跑只在代码审计存疑时触发。
- 任一不过 → verdict `REJECT` + 具体原因(哪行代码/哪个缺口)→ 退回**改代码/补件**,不改数字。
- 部分完成(某子轴 not_run)→ `partial` + 哪部分没做。

## 输出(写这个文件)
`campaigns/{{SLUG}}/experiments/{{EXPID}}/ACCEPTANCE.json`:
```json
{ "expid":"{{EXPID}}", "verdict":"ACCEPT|REJECT|PARTIAL",
  "C1_code_correct":true, "C2_complete":true, "C3_real_data":true,
  "C4_no_fake_no_hardcode":{"recompute_max_relerr":0.0,"procedure_derived":["bootstrap_2000x_cluster_ci"]},
  "spot_rerun":{"done":false,"reason":"code audit clean; not needed"},
  "origin_audit":{"driver_sha256":"{{DRIVER_SHA}}","data_fingerprint":{"...":"..."}},
  "reasons":[] }
```
receipt:`{expid, verdict, code_audit_clean}`。`origin_audit` 供 orchestrator 判"下次能否便宜复用不重审"。
