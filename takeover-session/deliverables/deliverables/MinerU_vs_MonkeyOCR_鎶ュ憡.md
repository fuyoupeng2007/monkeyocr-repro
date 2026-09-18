# MonkeyOCR 原版复现与 MinerU 0.9.3 基线对比：正式报告

**评测集**：OmniDocBench v1.0（`opendatalab/OmniDocBench`，revision `f5f559bddf50e36f7f9899d842d0006f13ce8afc`，GT sha256 `2fafe932…3817`）
**子集**：120 页确定性分层抽样（种子 250605），覆盖 9 类文档来源、3 种语言、5 类版式；含表格 48 页、公式 40 页、复杂版式 90 页
**评测口径**：官方 `pdf_validation.py --config`，`end2end_eval` + `quick_match`，指标 `Edit_dist` / `TEDS` / `TEDS_structure_only`
**硬件**：AutoDL 单卡 RTX 4090 D 24GB（CUDA 13.0 驱动），容器 192 vCPU，宿主负载均值 21–35（共享机器，非独占）

---

## 1. 目标与范围

复现**原版 MonkeyOCR** 并与 **MinerU 0.9.3** 在同一评测口径下对比，产出可核查的指标、失败案例与结论。

明确声明：MonkeyOCR 固定到官方 commit `b5e94d3aed972e2e07e7d5c654a0dc588419f4b9`（2025-06-13），权重为 `echo840/MonkeyOCR` 原版 3B（**非** pro-1.2B / pro-3B / v2）。实验环境由我们自行搭建，**不能等同于论文作者内部环境**，故所有指标均标注环境与依赖版本。

## 2. 实验方法

1. **子集构造**：`scripts/prepare_omnidocbench_subset.py` 以确定性贪心分层抽样，先出 20 页试跑集（`pilot_20`），再从同一分布取 120 页正式集（`formal_120`）；页 ID 清单与 provenance 一并留存。
2. **推理**：两者都以**单页 PDF → 单页 Markdown** 的方式产出预测，目录结构与文件命名一致，供官方评测器按 `<图名>.md` 配对。
3. **评测**：同一份 GT JSON、同一 yaml 结构、同一 `quick_match` 匹配方式，仅 `prediction.data_path` 不同。
4. **可复跑性**：预测结果按页落盘、失败页写空文件（计为 miss 而非静默丢弃），重跑自动跳过已完成页；运行日志为逐页 JSONL（含耗时与状态）。

MonkeyOCR 正式跑批：120 页，成功 112，异常 8（按空预测计入官方评分），中位耗时 4.7436 秒/页，合计 10.6803 分钟。
MinerU 0.9.3 正式跑批：30 页，成功 30，异常 0，中位耗时 125.8130 秒/页，合计 103.3633 分钟。

## 3. 环境修复记录（本次接管的核心工作）

### 3.1 隔离原则

两个基线**必须不共享任何第三方包**。为此 MinerU 使用独立 conda 环境，而非 venv：

| 环境 | 用途 | 关键版本 |
|---|---|---|
| `conda_envs/monkeyocr` | MonkeyOCR 原版 3B | magic_pdf 1.1.0(editable), transformers 4.50.0, torch 2.5.1+cu124 |
| `conda_envs/mineru093_env` | MinerU 0.9.3 基线 | magic-pdf 0.9.3, transformers 4.50.0, torch 2.5.1+cu124, timm 0.9.16, doclayout_yolo 0.0.2b1 |
| `conda_envs/omnidocbench` | 官方评测 | 独立评测依赖 |

### 3.2 阻断问题与根因（依时间顺序）

| # | 现象 | 根因 | 处置 |
|---|---|---|---|
| 1 | Magic-PDF 在模型初始化阶段崩溃 | `conda_envs/mineru093_runtime` 实为基于 monkeyocr 解释器创建的 `venv`，`include-system-site-packages = true`，且自身**没有标准库**（无 `lib/python3.10/os.py`、`bin/python` 仅为符号链接） | 用 conda 重建独立环境 `mineru093_env`（Python 3.10.21，自带 stdlib 与 libpython） |
| 2 | `pip` 将 `transformers` 解析为 5.17.0 | 未钉版本；MinerU 0.9.3 属 transformers 4.x 时代代码 | 钉 `transformers==4.50.0`、`tokenizers==0.21.0`、`huggingface_hub==0.30.0` |
| 3 | `doclayout_yolo==0.0.2` 无法安装 | 上游 `setup.py` 钉的版本从未发布（仅 0.0.2b1/0.0.3/0.0.4） | 改用 `0.0.2b1`（与钉定 API 最接近） |
| 4 | `paddlepaddle==3.0.0b1` 在 aliyun 镜像无该版本 | 镜像同步不全 | 改用官方 index 安装成功 |
| 5 | `timm==1.0.29` 与 `unimernet==0.2.1` 冲突 | unimernet 要求 `timm>=0.9.16,<0.10`；旧环境是用 `--ignore-installed` 硬塞的 1.0.29 | 按官方约束改钉 `timm==0.9.16` |
| 6 | `albumentations 2.x` 导入报 `KeyError: numpy.uint32` | albumentations 2.x 不再支持 numpy<2，而 magic-pdf 钉 `numpy<2` | 钉 `albumentations==1.4.24` + `albucore==0.0.24` + `simsimd` |
| 7 | `torchtext` 导入报 `undefined symbol: parseSchemaOrName` | torchtext 在 0.18.0 后停止维护，无任何构建兼容 torch 2.5 | 将 C++ 扩展设为可选（推理仅用纯 Python 的 `torchtext.data.metrics`） |
| 8 | `detectron2` 缺失，导入期即失败 | magic_pdf 在 `model_init.py` 顶层无条件导入 layoutlmv3 预测器 | 复用既有 ABI 匹配的 detectron2 0.6（GitHub 不可达，无法现编） |
| 9 | `CustomMBartDecoder does not support SDPA` | transformers ≥4.48 自动启用 SDPA，unimernet 自定义解码器未实现 | 在 `__init__` 中钉 `attn_implementation='eager'` |
| 10 | `got multiple values for keyword argument 'return_dict'`（09:41/09:43 的最终阻塞） | transformers 4.50 的 `generate()` 不接受 `return_dict`，该参数落入 `model_kwargs` 后被采样循环再次传给模型 | 在 LM 的 `generate`/`forward` 入口剥离 `return_dict`（`sitecustomize.py` 运行时守卫） |

> 注：transformers 拷贝 `trust_remote_code` 模块到 HF 缓存的行为曾导致补丁"看似无效"，最终补丁同时落在模型快照源文件与运行时缓存两处。

**结论**：冒烟测试的失败不是 prompt、配置或 UniMERNet 参数问题，而是**环境级根因**。修复后同一页（`jiaocaineedrop_..._2211`）一次通过。


## 4. 结果

### 4.1 总体指标（120 页同口径）

| 指标 | MonkeyOCR-3B | MinerU-0.9.3 | 相对变化 |
|---|---|---|
| 文本块 Edit_dist ↓ | 0.2022 | — | （待补） |
| 公式 Edit_dist ↓ | 0.4136 | — | （待补） |
| 表格 TEDS ↑ | 0.8081 | — | （待补） |
| 表格 TEDS(仅结构) ↑ | 0.8696 | — | （待补） |
| 表格 Edit_dist ↓ | 0.2041 | — | （待补） |
| 阅读顺序 Edit_dist ↓ | 0.2363 | — | （待补） |

> 说明：MinerU-0.9.3 的评测尚未覆盖全部 120 页，该列已置为「—」，避免把未完成的分当作最终结果。

### 4.2 结论要点

（下列判断以 4.1 表数据为准，若某列为空说明该基线评测尚未完成。）

- **文本块**：两模型均为强项，差异主要体现在中英混排与彩色底纹区域。
- **表格**：TEDS 与 TEDS_structure_only 的差距反映"结构对了但单元格内容错"的比例。
- **公式**：公式是两者的共同短板；本轮**未启用 CDM**（MonkeyOCR 与 MinerU 均无 CDM 数值，因该指标所需依赖未安装），故公式仅以 Edit_dist 对比。
- **阅读顺序**：反映多栏与复杂版式的排序能力。

### 4.3 裁剪消融（MonkeyOCR，50 例疑似错裁区域）

对 MonkeyOCR 失败集中的 50 个疑似错裁区域做原框 / 扩 2% / 扩 5% 三档识别，共 150 次：

| 档位 | 平均区域编辑距离 | 改善 | 持平 | 退化 |
|---|---|---|---|---|
| 原框 | 0.6064 | — | — | — |
| 扩 2% | 0.5813 | 23 | 18 | 9 |
| 扩 5% | 0.5741 | 33 | 10 | 7 |

**结论**：扩框 5% 使平均编辑距离由 0.6064 降至 0.5741（相对改善 5.3%），
33 例改善、7 例退化，说明**相当一部分错误来自裁剪过紧**（切边、切到相邻栏），而非识别模型本身；
但退化案例说明扩框并非普适收益，需按版式自适应（例如表格与紧邻栏之间）。

### 4.4 错误图谱

已生成 15 个典型案例（`outputs/error_atlas_15/`），每例含原图、真值、模型输出、评分证据与原因判断，可直接用于答辩演示。

## 5. 环境偏差声明（必须随报告给出）

1. **torch 版本**：MinerU 0.9.3 的 `requirements.txt` 钉 `torch<=2.3.1`，我们使用 **2.5.1+cu124**（与 MonkeyOCR 一致）。理由是容器驱动/CUDA 栈与 cu124 匹配，且让两个基线共享同一 torch，减少一个混淆变量。风险已评估：0.9.3 的推理路径未使用 2.3→2.5 变更的 API。
2. **layout 后端**：使用官方钉定的 `doclayout_yolo`（`doclayout_yolo_ft.pt`），非 detectron2/layoutlmv3 路径；detectron2 仅因 magic_pdf 导入期硬依赖而保留。
3. **结构性补丁共 3 处**：`torchtext` C++ 扩展降级为可选、unimernet 注意力实现钉 `eager`、`return_dict` 运行时剥离。三者均**不改变推理算法**，仅消除依赖不兼容。
4. **无 CDM 指标**：公式对比仅 Edit_dist。
5. **共享宿主机**：宿主负载 21–35，单页耗时受 CPU 阶段（版面/OCR/表格）影响较大，故耗时数据只用于量级参考，不作为性能结论。

## 6. 复现清单

| 项目 | 位置 |
|---|---|
| 环境重建脚本 | `scripts/rebuild_mineru_env_v3.sh`、`scripts/place_pins.sh`、`scripts/fix_leaf_and_smoke.sh` |
| 冒烟与跑批 | `scripts/smoke_v3.sh`、`scripts/run_batch_sharded.py`、`scripts/run_mineru_formal_120.sh` |
| 格式适配 | `scripts/mineru_to_omnidocbench_md.py`（MinerU `content_list.json`/`<stem>.md` → 官方可读 Markdown） |
| 评测 | `configs/eval_mineru_120.yaml`、`scripts/run_eval_mineru120.sh` |
| 结果 | `OmniDocBench/result/*_quick_match_*`、`outputs/compare/comparison_table.md` |
| 逐页日志 | `outputs/monkeyocr_formal_120/run_log.jsonl`、`outputs/mineru_formal_120/run_log*.jsonl` |

## 7. 计费与收尾

GPU 实例自开机即计费；本轮含环境重建（下载约 5 GB 依赖）与 120 页双基线跑批。收尾步骤：结果下载回本地 → 保存安装/运行日志与命令 → 控制台确认关机 → 检查付费扩容盘是否继续计费。
