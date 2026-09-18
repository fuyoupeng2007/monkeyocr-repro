# MonkeyOCR 公开权重复现实验

本项目复现 MonkeyOCR 论文的公开权重推理与 OmniDocBench 端到端评测链路。正式实验固定为 120 页分层子集，明确不运行论文的 981 页完整集。20 页试跑属于这 120 页中的固定子集。

## 固定版本

| 项目 | 固定值 |
| --- | --- |
| MonkeyOCR 源码 | `b5e94d3aed972e2e07e7d5c654a0dc588419f4b9` |
| OmniDocBench 评测源码 | `2757e3b8a1dc981eb8b7e94a5a56646891f67143` |
| OmniDocBench 数据集提交 | `f5f559bddf50e36f7f9899d842d0006f13ce8afc` |
| 分层子集 | 120 页，随机种子 `250605` |
| 试跑集 | 20 页，包含于正式 120 页 |
| GPU | NVIDIA RTX 4090D 24 GB |

完整的数据来源、页 ID、哈希及子集生成参数见 `evidence/provenance.json` 与 `evidence/manifest_120.jsonl`。

## MonkeyOCR 重跑

服务器路径以 `/root/autodl-tmp/monkeyocr-repro` 为例。

```bash
/root/autodl-tmp/conda_envs/monkeyocr/bin/python scripts/run_batch_monkeyocr.py \
  --manifest data/omnidocbench_v1_0/subsets/manifest_120.jsonl \
  --data-root data/omnidocbench_v1_0 \
  --output-root outputs/monkeyocr_formal_120 \
  --config MonkeyOCR/model_configs.yaml

cd OmniDocBench
/root/autodl-tmp/conda_envs/omnidocbench/bin/python pdf_validation.py \
  --config /root/autodl-tmp/monkeyocr-repro/scripts/eval_formal_120.yaml
```

脚本会为每页保存 Markdown、`middle.json`、布局可视化和 JSONL 运行日志。发生推理异常的页面会生成空 Markdown 后再进入评测，因此不会因漏页而虚高。

## 评测口径

使用固定历史版 OmniDocBench 的 `quick_match`：文本、展示公式、表格、阅读顺序。公式 CDM 由该历史评测器导出配对 JSON，需外部 UniMERNet CDM 工具才能生成数值，因此报告中不将空值误写为零分。

## MinerU 对照

MinerU 使用 `magic-pdf==0.9.3` 与仓库标签 `magic_pdf-0.9.3-released`，保存在独立环境 `mineru093_runtime`。因遗留 CLI 只接收 PDF，120 张源图先按原始像素写入单页 PDF，再用同一 OmniDocBench 评测配置进行评分。此输入封装差异会在报告中单列为可比性限制。

## 裁框消融

`scripts/run_crop_ablation.py` 从 MonkeyOCR 的 `middle.json` 中挑选与冻结 GT 匹配、但 GT 覆盖率不足的检测框。固定 50 个区域，比较原框、四边各扩 2%、四边各扩 5%，并保存每次裁图、原始回答、GT、检测框及区域级归一化编辑距离。该区域级指标用于诊断裁框影响，不替代 OmniDocBench 端到端分数。
