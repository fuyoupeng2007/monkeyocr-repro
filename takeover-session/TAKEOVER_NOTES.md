# 接管笔记：MonkeyOCR 复现 / MinerU 0.9.3 对比实验

> 接管时间：本地 2026-09-18（远程容器时钟 09:4x）。接管前的执行者是 ChatGPT。

## 0. 接管通道（已验证可用）

```powershell
# 本地工作区 D:\haeness\monkeyocr-takeover
pwsh -f .\rcmd.ps1 -Cmd "nvidia-smi"
# 多行脚本：把 .sh 转成 LF 后通过 stdin 喂给远端 bash
((Get-Content -Raw .\remote\x.sh) -replace "`r`n","`n") | ssh -p 29127 -i $HOME\.ssh\monkeyocr_autodl_rsa -o BatchMode=yes root@connect.cqa1.seetacloud.com "bash -s"
```

- 远端：AutoDL 容器 `autodl-container-9d1044903a-e0797c2f`，root@connect.cqa1.seetacloud.com:29127
- 显卡：单张 RTX 4090 D 24GB（接管时 0% 利用率 / 0MiB 占用，空闲）
- 项目根：`/root/autodl-tmp/monkeyocr-repro`
- 私钥：`~/.ssh/monkeyocr_autodl_rsa`（远端 authorized_keys 里名为 `monkeyocr-autodl-rsa-temporary`，ChatGPT 之前的会话放进去的）

## 1. 项目目标（据 README_先读.md / 租用与计费清单.md）

- 复现**原版 MonkeyOCR**（`echo840/MonkeyOCR`，3B，固定 commit `b5e94d3aed972e2e07e7d5c654a0dc588419f4b9`，2025-06-13）。
- 候选对比基线：**MinerU 0.9.3**（`magic-pdf==0.9.3`）。
- 评测集：**OmniDocBench v1.0**，已用 `scripts/prepare_omnidocbench_subset.py` 抽子集。
- 报告必须写明固定 commit，不能声称"等同论文作者内部环境"。

## 2. 已完成（接管前）

| 工作 | 产物 | 状态 |
|---|---|---|
| MonkeyOCR 环境+权重安装 | `outputs/monkeyocr_pilot_20`（20 页）、`outputs/monkeyocr_formal_120`（120 页，00:36 完成） | 完成 |
| OmniDocBench 官方评测 | `OmniDocBench/result/predictions_quick_match_*`（00:40） | 完成 |
| 裁剪消融 50 例 | `outputs/crop_ablation_50` + `summary_comparison.json`（01:31） | 完成 |
| 错误图谱 15 例 | `outputs/error_atlas_15`（01:11） | 完成 |
| MinerU 0.9.3 安装+模型下载 | `outputs/mineru093_install.log`、`mineru093_models.log`（416KB） | 完成 |
| MinerU 冒烟测试 | 见下 | **未通过** |

## 3. 当前卡点（接管时正在做，全部失败）

MinerU 0.9.3 单页冒烟测试，连续失败：`mineru_smoke_yolo*`（13 次）、`final`~`final6`、`struct`（09:43 最后一次，失败）。

两次最终形态的错误：

1. `final6`（09:41，table_model 回退成 `rapid_table`）：
   `magic_pdf.tools.cli:parse_doc:109 - 'float' object is not iterable`
2. `struct`（09:43，`table-config.model = struct_eqtable` 生效）：
   `TypeError: Qwen2ForCausalLM(...) got multiple values for keyword argument 'return_dict'`
   —— 崩在 `~/.cache/huggingface/modules/transformers_modules/StructEqTable/modeling_internvl_chat.py` 的 `generate()`

### 已确认的根因（本次接管新查出的，ChatGPT 没定位到）

`/root/autodl-tmp/conda_envs/mineru093_runtime` **不是一个完整环境，而是用 `python -m venv` 基于 monkeyocr 的解释器建出来的残缺 venv**：

```
bin/python -> /root/autodl-tmp/conda_envs/monkeyocr/bin/python   (符号链接)
pyvenv.cfg: home = /root/autodl-tmp/conda_envs/monkeyocr/bin
lib/python3.10/ 下只有 site-packages，没有 os.py 等标准库
无 libpython3.10.so
```

实测 `sys.path`：

```
/root/autodl-tmp/conda_envs/mineru093_runtime/lib/python3.10/site-packages   <- magic_pdf 0.9.3
/root/autodl-tmp/conda_envs/monkeyocr/lib/python3.10/site-packages           <- click / transformers / torch 全从这来
__editable__.magic_pdf-1.1.0.finder.__path_hook__                            <- MonkeyOCR 的 magic_pdf 1.1.0 可编辑安装
```

即：MinerU 0.9.3 的 `magic_pdf` 配的是 MonkeyOCR 环境的 `transformers 4.50.0` / `torch` / `click`，两套库版本与补丁互相打架 → 表格识别阶段 `return_dict` 重复传参、`'float' object is not iterable`。

**结论：冒烟测试必须先修环境，修 prompt/配置都是白费。**

## 3.1 修复结果（接管后）

环境重建为 `conda_envs/mineru093_env`（conda 自建 Python 3.10.21，自带 stdlib/libpython，与 monkeyocr 零共享）。
按官方 `setup.py [full]` 逐项钉版本后，还需 3 处**代码级补丁**（原件与改后文件都留在 `outputs/`）：

| 补丁 | 位置 | 原因 |
|---|---|---|
| `return_dict` 运行时剥离 | `sitecustomize.py`（guard LM 的 `generate`/`forward`） | transformers 4.50 的 `generate()` 不接受 `return_dict`，它落入 `model_kwargs` 后被采样循环再次传给模型 → `got multiple values for keyword argument` |
| 注意力实现钉 `eager` | `unimernet/models/unimernet/encoder_decoder.py` | transformers ≥4.48 自动启用 SDPA，unimernet 自定义 MBart 未实现 |
| torchtext C++ 扩展降级为可选 | `torchtext/_extension.py` | torchtext 0.18.0 后停止维护，无任何构建兼容 torch 2.5（`undefined symbol parseSchemaOrName`）；推理只用纯 Python 的 `torchtext.data.metrics` |

另有环境级依赖坑（详见正式报告 3.2 表）：transformers 被解析到 5.17.0、`timm==1.0.29` 违反 unimernet 的 `timm<0.10`、
`doclayout_yolo==0.0.2` 上游从未发布（改 0.0.2b1）、`paddlepaddle==3.0.0b1` 镜像缺失、`albumentations 2.x` 与 `numpy<2` 冲突。

**结果**：同一页（`jiaocaineedrop_jiaocai_needrop_en_2211`）一次通过，产出 Markdown 3873 字符 + HTML 表格 + LaTeX 公式 + content_list/layout/model/spans 全套。
`trust_remote_code` 的坑：transformers 每次导入都会把模型快照里的 remote code 拷到 HF modules 缓存，只改缓存无效——补丁必须落在**快照源文件**。

## 3.2 评测踩坑与修正（重要）

1. **评分文件被覆盖**：官方 `pdf_validation.py` 用「预测目录 basename + match_method」命名结果，
   MonkeyOCR 的预测目录也叫 `predictions`，于是 MinerU 的前置评测把 MonkeyOCR 的 `predictions_quick_match_*.json` 覆盖了。
   处置：两边各建独立命名的预测目录（`outputs/eval_inputs/{model}_formal_120`）+ 独立 config，结果前缀分别为
   `monkeyocr_formal_120_quick_match_*` 与 `mineru_formal_120_quick_match_*`；被污染文件已隔离到 `outputs/_quarantine/`。
2. **数值以重算为准**：MonkeyOCR 文本块 Edit_dist 由早前的 0.1960 修正为 **0.2022**（重算覆盖 118/120 页；
   早前那次评分在预测尚未写全时执行）。全部对比以 `*_formal_120_quick_match_*` 为准。
3. **worker 必须显式 cwd**：magic-pdf CLI 会检查 `./configs/mineru093/magic-pdf.json`，
   在 `$HOME` 下启动会直接失败（表现为 `empty markdown`）。已改成绝对 `--config` + `cwd=项目根`。
4. **并发抢页**：多个 worker 共享 manifest 时靠"预测文件是否存在"判断会重复处理同一页并写坏共享 raw 目录，
   已加**原子抢页锁**（`os.link`，`.page_locks/`）。

## 4. 中断事件与当前状态（重要）

**2026-09-18 13:50 左右，AutoDL 实例下线，SSH 连接被拒绝（`Connection refused`）。**
诊断：`connect.cqa1.seetacloud.com` 本身可达（ping 通、22 端口开），但代理端口 **29127 拒连**
→ 说明是该实例被关机/重启，**不是网络问题**。重启后 **SSH 端口会变**，且需要重新确认。

### 中断时的进度（已核实）

| 项目 | 状态 |
|---|---|
| MinerU 隔离环境重建 | ✅ 完成（`conda_envs/mineru093_env`） |
| MinerU 单页冒烟 | ✅ 通过（Markdown + HTML 表格 + LaTeX 公式 + 中间件） |
| MinerU 120 页跑批 | ⏸️ **81/120 完成，0 失败**，被容器下线中断 |
| MinerU 官方评测 | ❌ 未完成（只有 21 页的中间态评分，已置「—」） |
| MonkeyOCR 官方评测 | ✅ 完成（官方评测器重算，覆盖 118/120 页） |
| 对比表 / 报告 / 幻灯片 | ✅ 已产出（报告按"未完成"口径书写，不虚构结论） |

### 续跑步骤（实例恢复后）

```bash
# 0) 端口变了，用新的 host:port（AutoDL 控制台可见）
# 1) 自动续跑，跳过已完成的 81 页
cd /root/autodl-tmp/monkeyocr-repro
setsid nohup /root/autodl-tmp/conda_envs/mineru093_env/bin/python \
  scripts/launch_mineru_workers.py --shards 3 --timeout 3600 \
  > outputs/workers_resume.log 2>&1 < /dev/null &
# 2) 跑完自动：适配 → 双基线评测（独立命名，不会撞名）→ 对比表 → 报告/PPT
bash /root/autodl-tmp/launch.sh scripts/pipeline_tail.sh pipeline_tail_nohup.log
```

### 本地已保全的资产（即使实例永远不回来也能出报告）

- MonkeyOCR 120 页预测 Markdown + `run_log.jsonl`（含逐页耗时）
- OmniDocBench 官方评分 JSON 20 个（含逐页 edit 文件）
- 消融 50 例 ×3 档的裁剪图与模型响应（150 份）
- 全部脚本（环境重建、跑批、适配、评测、对比、出报告、幻灯片）
- 正式报告、HTML 幻灯片、讲解稿

### 本地与远端的差异（诚实说明）

远端还有但**未同步到本地**的：MinerU 的 81 页预测与 raw 输出、`error_atlas_15` 中 7 例的证据文件、
`mineru093_env` 环境本身（可脚本重建）。

## 5. 待用户确认

- **实例已下线**：请在 AutoDL 控制台确认状态；若要续跑，请把**新的 SSH 端口**给我。
- 是否需要补 **CDM** 公式指标？（两基线目前都只有 Edit_dist）
- 汇报材料除了 HTML 幻灯片与原生 `.pptx`，是否还需要 PDF？

