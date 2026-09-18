# MonkeyOCR 原版复现与 MinerU 0.9.3 基线对比

本仓库记录一次**可核验的复现实验**：复现原版 MonkeyOCR，并以 MinerU 0.9.3 作为对照基线，
在 OmniDocBench v1.0 的同一份分层子集上用官方评测代码打分。

**先说清楚完成度**：MonkeyOCR 侧是完整结果；MinerU 侧的环境修复与单页验证已完成，
但 120 页正式跑批完成 **81 页（零失败）后因算力不足、实例中断而停止**，剩余 **39 页未处理**。
因此 MinerU 的评测只有中间态结果，本仓库在每一处都标注了覆盖页数，**不把不完整的分当作结论**。

---

## 仓库范围

**本仓库只包含复现实验本身**：代码、脚本、配置、实验数据与实验报告。申请邮件、汇报 PPT、
答辩讲稿等个人材料不在此仓库内。

## 目录结构

| 目录 | 内容 | 来源 |
|---|---|---|
| `chatgpt-run/` | 早期搭建阶段的调研文档、部署包、MonkeyOCR 源码快照、第一批实验证据 | 前序执行者 |
| `takeover-session/` | 接管后完成的环境修复、跑批与评测脚本、实验报告、本阶段全部实验数据 | 本阶段 |

`takeover-session/` 关键位置：

```
takeover-session/
├── deliverables/                            实验报告与对比数据（见下表）
├── remote/                                  服务器上执行的全部脚本
│   ├── rebuild_mineru_env_v3.sh             隔离环境重建
│   ├── place_pins.sh / fix_leaf_and_smoke.sh 依赖钉版本与补齐
│   ├── patch_*.py|sh / guard_v2.sh          三处兼容性补丁及其前置排查
│   ├── run_batch_sharded.py                 分片跑批（原子抢页锁 + 断点续跑）
│   ├── mineru_to_omnidocbench_md.py         结果格式适配
│   └── reeval_both.sh / pipeline_tail.sh    双基线评测与一键收尾
├── sync/                                    实验数据
│   ├── outputs/monkeyocr_formal_120/        120 页预测结果与逐页运行日志
│   ├── outputs/crop_ablation_50/            裁剪消融的 150 份样本与模型响应
│   └── OmniDocBench/result/                 官方评分文件（总体指标 + 逐页明细）
├── build_final_report.py                    实验报告生成器（数据程序化读取）
├── extract_paper.py                         论文文本抽取（论文原文不随仓库分发）
└── security_scan.py                         发布前凭据扫描
```

### 实验报告清单（`takeover-session/deliverables/`）

| 文件 | 说明 |
|---|---|
| `MinerU_vs_MonkeyOCR_报告.md` / `.html` | 完整技术报告（10 章 + 3 附录，含环境修复全过程、结果、失败归因与偏差声明） |
| `MonkeyOCR论文_中文全译.md` / `.docx` | 论文全文中文翻译（含缩写术语表、核心数字速查、阅读注意事项） |
| `compare/comparison_table.md` | 双基线指标对比表（含覆盖页数标注） |
| `compare/comparison.json` | 对比数据的机器可读版本 |

> 报告中的全部数字由 `build_final_report.py` 从实验产物程序化读取，
> 因此修改数据后重新运行脚本即可同步，不会出现文档与数据不一致。

---

## 复现对象与保真度

| 项目 | 值 |
|---|---|
| 代码提交 | `b5e94d3aed972e2e07e7d5c654a0dc588419f4b9`（2025-06-13） |
| 权重 | `echo840/MonkeyOCR` 原版 3B（非 pro-1.2B / pro-3B / v2） |
| 对话模型后端 | LMDeploy 0.8.0（官方默认，未替换） |
| 版面 / 阅读顺序 | `doclayout_yolo` / `layoutreader` |
| 对照基线 | `magic-pdf==0.9.3`（MinerU） |

实验环境由我们自己搭建，**不等同于论文作者内部环境**，故全部指标附依赖版本清单；
`albumentations`、`torch` 版本等偏差在报告中逐条声明。

## 评测设置

- **数据集**：OmniDocBench v1.0，revision `f5f559bddf50e36f7f9899d842d0006f13ce8afc`
- **子集**：120 页确定性分层抽样（种子 250605），覆盖 9 类文档来源、3 种语言、5 类版式；
  含表格 48 页、公式 40 页、复杂版式 90 页
- **口径**：官方 `pdf_validation.py`，`end2end_eval` + `quick_match`
- **指标**：`Edit_dist`（文本块/公式/表格/阅读顺序）、`TEDS`、`TEDS_structure_only`
- **可比性**：两个基线使用同一份标注、同一配置结构、同一匹配方式，唯一差异是输出目录

---

## 结果

### MonkeyOCR（完整，118/120 页有效评分）

| 指标 | 值 |
|---|---|
| 文本块 Edit_dist ↓ | **0.2022** |
| 公式 Edit_dist ↓ | 0.4136 |
| 表格 TEDS ↑ | **0.8081** |
| 表格 TEDS（仅结构）↑ | 0.8696 |
| 表格 Edit_dist ↓ | 0.2041 |
| 阅读顺序 Edit_dist ↓ | 0.2363 |

### MinerU 0.9.3（**不完整，21/120 页中间态，仅备查**）

| 指标 | 值 | 说明 |
|---|---|---|
| 文本块 Edit_dist ↓ | 0.2054 | 21 页所见，不可外推 |
| 公式 Edit_dist ↓ | 0.3853 | 同上 |
| 表格 TEDS ↑ | 0.6020 | 同上 |
| 阅读顺序 Edit_dist ↓ | 0.2424 | 同上 |

> ⚠️ `Edit_dist` 是页面级均值，而本实验实测单页耗时跨度极大（约 32 秒至 767 秒），
> 说明页面难度差异显著。21 页样本无法代表 120 页分布，**不得作为 MinerU 整体能力结论**。

---

## 主要发现

### 1. MinerU 长期跑不起来，根因是环境隔离被破坏（不是模型或配置）

此前的运行环境并非独立环境，而是基于 MonkeyOCR 解释器创建的**残缺 venv**：

```
bin/python -> .../monkeyocr/bin/python     (符号链接)
pyvenv.cfg:  include-system-site-packages = true
lib/python3.10/ 下只有 site-packages，缺 os.py 等标准库
```

导致 MinerU 0.9.3 实际运行在 MonkeyOCR 的 `transformers`/`torch` 之上，两套依赖互相冲突，
冒烟测试在这一状态下**不可能通过**。重建真正隔离的 conda 环境并逐项钉版本后，
此前连续失败的页面一次通过，产出 Markdown、HTML 表格、LaTeX 公式及全套中间件。

修复过程共排除 **10 个阻断问题**，详见 `takeover-session/TAKEOVER_NOTES.md` 与报告第四节。
其中三个属于"新版库与老代码不兼容"，需要在代码里处理（均不改变推理算法）：
`return_dict` 重复传参、自定义解码器不支持 SDPA、torchtext 无兼容构建。

### 2. 失败来自流程，而非模型能力（最有价值的发现）

MonkeyOCR 的 **8 个失败页全部集中在笔记（note）类单栏页面**，错误类型统一为 `IndexError`
——不是"认错了字"，而是**整页没有输出**。原因是检测环节未找到有效区域时直接报错退出，
而这类页面恰好稀疏、留白多。

| 统计口径 | 文本块 Edit_dist | 覆盖 |
|---|---|---|
| 官方提交口径（失败页计缺失） | 0.2022 | 118 页 |
| 剔除整页无产出的页面 | **0.1442** | 差值 **+0.058** |

整页失败单独贡献约 **0.058** 的差距，大于任何"识别质量"层面的差异，且修复成本远低于提升模型能力。

### 3. 部分错误源于裁剪过紧（消融实验）

对 50 个疑似裁剪不当区域，按原始框 / 外扩 2% / 外扩 5% 各识别一次（共 150 次）：

| 档位 | 平均区域编辑距离 | 改善 | 持平 | 退化 |
|---|---|---|---|---|
| 原始框 | 0.6064 | — | — | — |
| 外扩 2% | 0.5813 | 23 | 18 | 9 |
| **外扩 5%** | **0.5741** | 33 | 10 | 7 |

扩框有效（说明错误部分来自裁剪过紧），但有 7 例退化，故不应无脑放大，需按版式自适应。

---

## 未完成的部分（如实说明）

| 项目 | 状态 | 原因 |
|---|---|---|
| MinerU 跑批 | 81/120 页 | 算力不足、实例中断；中断前零失败 |
| MinerU 官方评测 | 21/120 页中间态 | 依赖上项 |
| MinerU 中途产物 | 丢失 | 存于已下线的实例，本地无备份 |
| CDM 公式指标 | 未包含 | 依赖未安装（两基线口径一致，对比仍公平） |

**补齐成本**：环境重建约 1 小时（脚本全自动）+ 剩余 39 页约 40–90 分钟 + 评测出表约 10 分钟 ≈ 2 小时。

## 复现方式

```bash
# 1) 服务器环境重建（脚本按序执行）
bash scripts/rebuild_mineru_env_v3.sh
bash scripts/place_pins.sh
bash scripts/fix_leaf_and_smoke.sh
bash scripts/patch_torchtext4.sh && bash scripts/patch_attn2.sh && bash scripts/guard_v2.sh
bash scripts/smoke_v3.sh                      # 单页验证

# 2) 120 页跑批（3 路并行，支持断点续跑）
python scripts/launch_mineru_workers.py --shards 3 --timeout 3600

# 3) 一键收尾：格式适配 -> 双基线官方评测 -> 对比表 -> 报告
bash scripts/pipeline_tail.sh
```

> 注意：magic-pdf 的 CLI 会检查 `./configs/mineru093/magic-pdf.json`，脚本必须在**项目根目录**执行；
> 多进程依赖原子抢页锁避免重复处理同一页。

## 数据与证据

`takeover-session/sync/` 内含：MonkeyOCR 120 页预测结果、逐页运行日志（耗时/状态）、
OmniDocBench 官方评分 JSON（总体指标与逐页明细）、裁剪消融的 150 份样本图与模型响应。
`chatgpt-run/复现工程/deliverables/evidence/` 内含早期阶段的错误图谱证据。

---

## 免责与归属

- 本仓库中的 MonkeyOCR、MinerU、OmniDocBench 源码与模型权重版权归各自作者所有；
  仓库内包含的第三方代码快照仅用于复现记录，遵循其原始许可证。
- 实验数据与结论由本仓库的复现流程产生，非官方发布结果。
- 提交前的密钥扫描见 `takeover-session/security_scan.py`；**仓库不包含任何私钥或访问凭据**。
