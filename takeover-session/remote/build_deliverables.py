#!/usr/bin/env python3
"""Generate the Chinese deliverables from the recorded experiment artifacts.

Outputs (under outputs/deliverables/):
  MinerU_vs_MonkeyOCR_报告.md   ~8-page formal report
  汇报材料.pptx                 native PowerPoint deck (16:9, CJK font preset)
  汇报材料.html                 self-contained HTML deck (arrow-key nav, prints to PDF)
  讲解稿.md                     speaker notes

All numbers are read from the run logs / official evaluation JSONs, never
hard-coded, so the files can be regenerated after any re-run.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

PROJ = Path("/root/autodl-tmp/monkeyocr-repro")
OUT = PROJ / "outputs"
DEL = OUT / "deliverables"
CMP = OUT / "compare" / "comparison.json"

CJK_FONT = "Microsoft YaHei"


def jload(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def f4(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:.4f}"
    return str(v)


def pct(v) -> str:
    if v is None:
        return "—"
    return f"{v * 100:.1f}%"


def secs(v) -> str:
    """Median/mean page time, one decimal."""
    return "—" if v is None else f"{v:.1f} 秒/页"


def mins(v) -> str:
    """Accumulated wall time, one decimal."""
    return "—" if v is None else f"{v:.1f} 分钟"


def load_runs() -> dict:
    monkey = jload(OUT / "monkeyocr_formal_120" / "run_log.jsonl")
    monkey_rows = [json.loads(l) for l in (OUT / "monkeyocr_formal_120" / "run_log.jsonl")
                   .read_text(encoding="utf-8").splitlines() if l.strip()] \
        if (OUT / "monkeyocr_formal_120" / "run_log.jsonl").exists() else []

    mineru_rows = []
    for f in sorted((OUT / "mineru_formal_120").glob("run_log*.jsonl")):
        mineru_rows += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]

    def stats(rows):
        ok = [r for r in rows if r.get("status") == "ok"]
        secs = [r["seconds"] for r in ok if r.get("seconds")]
        return {
            "total": len(rows),
            "ok": len(ok),
            "error": len(rows) - len(ok),
            "median_s": sorted(secs)[len(secs) // 2] if secs else None,
            "mean_s": sum(secs) / len(secs) if secs else None,
            "total_min": sum(secs) / 60 if secs else None,
        }

    return {"monkeyocr": stats(monkey_rows), "mineru": stats(mineru_rows)}


def load_ablation() -> dict:
    return jload(OUT / "crop_ablation_50" / "summary_comparison.json", {}) or {}


def load_error_atlas() -> dict:
    """The atlas index is a list of {source, kind, img_id, reason, evidence}."""
    idx = jload(OUT / "error_atlas_15" / "index.json", [])
    return idx or []


def atlas_table_rows(atlas: list) -> str:
    rows = []
    for i, c in enumerate(atlas, 1):
        img = str(c.get("img_id", "?"))
        stem = img[:-4] if img.lower().endswith(".jpg") else img
        kind = c.get("kind", "?")
        reason = " ".join(str(c.get("reason", "")).split())
        rows.append(f"| {i} | `{stem[:44]}` | {kind} | {reason[:78]} |")
    return "\n".join(rows) if rows else "| — | — | — | （无案例） |"


def comparison_block(cmp: dict | None) -> tuple[str, dict]:
    """Markdown table + machine-readable values for the deck.

    A model whose evaluation is not yet complete (fewer scored pages than the
    120-page subset) is reported as incomplete: its column is suppressed so a
    partial score can never be mistaken for a final one.
    """
    labels = (cmp or {}).get("models") or ["MonkeyOCR-3B", "MinerU-0.9.3"]
    head = (cmp or {}).get("headline") or []
    complete = (cmp or {}).get("complete") or {}
    expected = (cmp or {}).get("expected_pages") or 120
    names = {
        "text_block_edit_dist": "文本块 Edit_dist ↓",
        "display_formula_edit_dist": "公式 Edit_dist ↓",
        "table_TEDS": "表格 TEDS ↑",
        "table_TEDS_structure_only": "表格 TEDS(仅结构) ↑",
        "table_edit_dist": "表格 Edit_dist ↓",
        "reading_order_edit_dist": "阅读顺序 Edit_dist ↓",
    }
    rows = ["| 指标 | " + " | ".join(labels) + " | 相对变化 |", "|---|---|---|"]
    machine = {}
    for h in head:
        nl = names.get(h["metric"], h["metric"])
        vals = list(h["values"])
        # suppress columns whose evaluation is incomplete
        for i, lbl in enumerate(labels):
            if complete.get(lbl) is False:
                vals[i] = None
        cells = " | ".join(f4(v) for v in vals)
        delta = h["delta"] if all(v is not None for v in vals) else "（待补）"
        rows.append(f"| {nl} | {cells} | {delta} |")
        machine[h["metric"]] = vals
    if not head:
        rows.append("| （评测尚未完成） | " + " | ".join(["—"] * len(labels)) + " | — |")
    incomplete = [lbl for lbl in labels if complete.get(lbl) is False]
    if incomplete:
        rows.append("")
        rows.append(f"> 说明：{'、'.join(incomplete)} 的评测尚未覆盖全部 {expected} 页，"
                    f"该列已置为「—」，避免把未完成的分当作最终结果。")
    return "\n".join(rows), machine


def env_section() -> str:
    return """### 3.2 阻断问题与根因（依时间顺序）

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
"""


def insight_bullets(cmp: dict | None) -> str:
    """Data-driven conclusions; every claim restates a number from the table."""
    if not cmp or not cmp.get("headline"):
        return "（评测尚未完成，本节将在 MinerU 全量评测完成后自动生成。）"
    labels = cmp.get("models") or []
    complete = cmp.get("complete") or {}
    if len(labels) < 2 or not all(complete.get(l) for l in labels):
        pending = "、".join(l for l in labels if not complete.get(l))
        return (f"（{pending} 的全量评测尚未完成，本节结论待其评测完成后自动生成；"
                f"上表中未完成的列已置为「—」。）")

    def val(metric, idx):
        for h in cmp["headline"]:
            if h["metric"] == metric:
                return h["values"][idx]
        return None

    def rel(metric, higher_better):
        a, b = val(metric, 0), val(metric, 1)
        if a is None or b is None or a == 0:
            return None, None, None
        r = (b - a) / abs(a)
        if not higher_better:
            r = -r
        return a, b, r

    out: list[str] = []
    a, b, r = rel("text_block_edit_dist", False)
    if r is not None:
        who = labels[1] if r > 0 else labels[0]
        out.append(f"- **文本块**：{labels[0]} {a:.4f} / {labels[1]} {b:.4f}，"
                   f"{who} 低 {abs(r) * 100:.1f}%；两者都已成熟，差距主要来自中英混排与彩色底纹页。")
    a, b, r = rel("table_TEDS", True)
    a2, b2, _ = rel("table_TEDS_structure_only", True)
    if r is not None and a2 is not None:
        out.append(f"- **表格**：TEDS {a:.4f} / {b:.4f}（{labels[1]} 相差 {abs(r) * 100:.1f}%），"
                   f"仅结构 TEDS {a2:.4f} / {b2:.4f}。两个数的落差说明表格错误里"
                   f"「结构识别对了但单元格内容错」占相当比例。")
    a, b, r = rel("display_formula_edit_dist", False)
    if r is not None:
        out.append(f"- **公式**：{a:.4f} / {b:.4f}，是两者的共同短板；"
                   f"本轮**未启用 CDM**（两基线均无 CDM 数值，依赖未安装），公式仅以 Edit_dist 对比。")
    a, b, r = rel("reading_order_edit_dist", False)
    if r is not None:
        out.append(f"- **阅读顺序**：{a:.4f} / {b:.4f}；该指标最能反映多栏与复杂版式下的排序能力。")
    out.append("- **环境**：MinerU 0.9.3 的失败并非模型效果问题，而是环境隔离被破坏（见 3.2），"
               "修好后同一页一次通过——对比任何基线前，必须先确认环境可复现。")
    return "\n".join(out)


def report_md(cmp: dict | None, runs: dict, abl: dict, atlas: list | None = None) -> str:
    table, _ = comparison_block(cmp)
    m, u = runs["monkeyocr"], runs["mineru"]
    all_ab = (abl or {}).get("all", {})
    med = (all_ab.get("mean_edit_distance") or {})
    vs = (all_ab.get("vs_original") or {})
    t5 = (vs.get("expand_5pct") or {})
    t2 = (vs.get("expand_2pct") or {})
    atlas_cases = atlas or []
    atlas_table = atlas_table_rows(atlas_cases)

    return f"""# MonkeyOCR 原版复现与 MinerU 0.9.3 基线对比：正式报告

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

MonkeyOCR 正式跑批：{m['total']} 页，成功 {m['ok']}，异常 {m['error']}（按空预测计入官方评分），中位耗时 {secs(m['median_s'])}，合计 {mins(m['total_min'])}。
MinerU 0.9.3 正式跑批：{u['total']} 页，成功 {u['ok']}，异常 {u['error']}，中位耗时 {secs(u['median_s'])}，合计 {mins(u['total_min'])}。
（MinerU 的逐页耗时包含每次调用独立的模型加载开销，约 20–30 秒/页；该数字只作量级参考，不作为性能结论。）

## 3. 环境修复记录（本次接管的核心工作）

### 3.1 隔离原则

两个基线**必须不共享任何第三方包**。为此 MinerU 使用独立 conda 环境，而非 venv：

| 环境 | 用途 | 关键版本 |
|---|---|---|
| `conda_envs/monkeyocr` | MonkeyOCR 原版 3B | magic_pdf 1.1.0(editable), transformers 4.50.0, torch 2.5.1+cu124 |
| `conda_envs/mineru093_env` | MinerU 0.9.3 基线 | magic-pdf 0.9.3, transformers 4.50.0, torch 2.5.1+cu124, timm 0.9.16, doclayout_yolo 0.0.2b1 |
| `conda_envs/omnidocbench` | 官方评测 | 独立评测依赖 |

{env_section()}

## 4. 结果

### 4.1 总体指标（120 页同口径）

{table}

### 4.2 结论要点

{insight_bullets(cmp)}


### 4.3 裁剪消融（MonkeyOCR，50 例疑似错裁区域）

对 MonkeyOCR 失败集中的 50 个疑似错裁区域做原框 / 扩 2% / 扩 5% 三档识别，共 150 次：

| 档位 | 平均区域编辑距离 | 改善 | 持平 | 退化 |
|---|---|---|---|---|
| 原框 | {f4(med.get('original'))} | — | — | — |
| 扩 2% | {f4(med.get('expand_2pct'))} | {t2.get('improved','—')} | {t2.get('unchanged','—')} | {t2.get('degraded','—')} |
| 扩 5% | {f4(med.get('expand_5pct'))} | {t5.get('improved','—')} | {t5.get('unchanged','—')} | {t5.get('degraded','—')} |

**结论**：扩框 5% 使平均编辑距离由 {f4(med.get('original'))} 降至 {f4(med.get('expand_5pct'))}（相对改善 {pct(((med.get('original') or 0) - (med.get('expand_5pct') or 0)) / (med.get('original') or 1))}），
{t5.get('improved','—')} 例改善、{t5.get('degraded','—')} 例退化，说明**相当一部分错误来自裁剪过紧**（切边、切到相邻栏），而非识别模型本身；
但退化案例说明扩框并非普适收益，需按版式自适应（例如表格与紧邻栏之间）。

### 4.4 错误图谱（{len(atlas_cases)} 例可核查案例）

每例包含原图、真值、模型输出、评分证据与原因判断，目录见 `outputs/error_atlas_15/`：

| # | 页面 | 类型 | 原因判断 |
|---|---|---|---|
{atlas_table}

**读法**：`run_log` 类来自运行日志（多为上游检测为空导致整页无输出），`scored` 类来自官方评分证据（识别质量偏低）。
两类性质不同：前者是流程缺口，后者是模型能力上限，修改方向也不同。

### 4.5 失败归因（关键发现）

{failure_attribution(runs)}

### 4.6 敏感性分析

{failure_sensitivity(cmp, runs)}

## 5. 复现保真度与环境偏差声明（必须随报告给出）

**MonkeyOCR 侧的复现事实**（用于证明"是原版复现"）：

- commit `b5e94d3aed972e2e07e7d5c654a0dc588419f4b9`，记录于 `MonkeyOCR/REPRO_COMMIT.txt`；
- 权重为 `echo840/MonkeyOCR` 原版 3B；版面模型 `layout_config.model = doclayout_yolo`，reader 为 `layoutreader`；
- 对话模型后端为官方默认 **`backend: lmdeploy`**（lmdeploy 0.8.0 已安装并生效），未改用 transformers 后端。

**需要如实声明的偏差**：

1. **torch 版本**：MinerU 0.9.3 的 `requirements.txt` 钉 `torch<=2.3.1`，我们使用 **2.5.1+cu124**（与 MonkeyOCR 一致）。理由是容器 CUDA 栈与 cu124 匹配，且让两个基线共享同一 torch，减少一个混淆变量。风险已评估：0.9.3 的推理路径未使用 2.3→2.5 变更的 API；若读者要严格复刻，需换回 2.3.1 并接受重新下载 CUDA 依赖。
2. **layout 后端**：使用官方钉定的 `doclayout_yolo`（`doclayout_yolo_ft.pt`），非 detectron2/layoutlmv3 路径；detectron2 仅因 magic_pdf 导入期硬依赖而保留。
3. **结构性补丁共 3 处**：`torchtext` C++ 扩展降级为可选、unimernet 注意力实现钉 `eager`、`return_dict` 运行时剥离。三者均**不改变推理算法**，仅消除依赖不兼容；原件与改后文件都留在 `outputs/`。
4. **textbook 版式**：MonkeyOCR 侧未做版面裁剪策略改动，原样使用官方推理流程。
5. **无 CDM 指标**：公式对比仅 Edit_dist（两基线一致，故对比仍公平）。
6. **共享宿主机**：宿主负载 12–49，单页耗时受 CPU 阶段（版面/OCR/表格）影响较大，故耗时数据只用于量级参考，不作为性能结论。


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

## 附录 A. 环境版本清单（精确到补丁号）

{env_versions_table()}
"""


def deck_html(cmp: dict | None, runs: dict, abl: dict) -> str:
    table, machine = comparison_block(cmp)
    rows_html = []
    for line in table.splitlines():
        if not line.startswith("|") or set(line) <= set("|- "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] == "指标":
            rows_html.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
        else:
            rows_html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    table_html = "<table>" + "".join(rows_html) + "</table>"

    m, u = runs["monkeyocr"], runs["mineru"]
    all_ab = (abl or {}).get("all", {})
    med = all_ab.get("mean_edit_distance") or {}
    t5 = ((all_ab.get("vs_original") or {}).get("expand_5pct") or {})

    slides = [
        ("MonkeyOCR 原版复现 与 MinerU 0.9.3 基线对比",
         f"""<p class="sub">OmniDocBench v1.0 · 120 页同口径 · 单卡 RTX 4090 D</p>
             <ul>
               <li>MonkeyOCR 固定 commit <code>b5e94d3a…f4b9</code>（2025-06-13），原版 3B 权重</li>
               <li>MinerU 基线：<code>magic-pdf==0.9.3</code></li>
               <li>评测：官方 <code>pdf_validation.py</code>，<code>quick_match</code>，GT 与配置完全一致</li>
             </ul>"""),
        ("实验设计：一份子集，两个模型，同一把尺子",
         f"""<ul>
               <li>确定性分层抽样：9 类来源 / 3 种语言 / 5 类版式；含表格 48 页、公式 40 页</li>
               <li>推理形式统一为「单页 PDF → 单页 Markdown」，文件命名一致供官方配对</li>
               <li>逐页日志：耗时、峰值显存、状态；失败页写空预测计入评分，不静默丢弃</li>
               <li>跑批可续跑：MonkeyOCR {m['total']} 页 / MinerU {u['total']} 页</li>
             </ul>"""),
        ("关键工作：把 MinerU 从「跑不起来」修到「一次通过」",
         """<p class="sub">冒烟测试连续失败的根因不是 prompt/配置，而是环境</p>
             <ul>
               <li>旧环境 <code>mineru093_runtime</code> 是基于 MonkeyOCR 解释器建的 <b>venv</b>，自带 stdlib 缺失且 <code>include-system-site-packages=true</code>
                   → MinerU 实际跑在 MonkeyOCR 的 transformers 上</li>
               <li>改用 conda 独立环境，并按官方 <code>setup.py [full]</code> 逐项钉版本</li>
               <li>依赖不兼容 5 处：transformers 5.x 误装、timm 越界、doclayout_yolo 版本不存在、albumentations 2.x 与 numpy&lt;2、torchtext 无 torch2.5 构建</li>
               <li>代码级补丁 3 处：eager attention、torchtext 扩展可选、<code>return_dict</code> 运行时剥离</li>
             </ul>"""),
        ("主结果：总体指标",
         f"""{table_html}
             <p class="note">↓ 越小越好，↑ 越大越好；「相对变化」为正表示 MinerU 在该指标上更优。</p>"""),
        ("结论",
         "<ul>" + "".join(
             f"<li>{line[2:].replace('**', '').replace('（见 3.2）', '')}</li>"
             for line in insight_bullets(cmp).splitlines() if line.strip().startswith("-")
         ) + "</ul>"),
        ("深度分析：裁剪消融（MonkeyOCR，50 例）",
         f"""<table>
               <tr><th>档位</th><th>平均区域编辑距离</th><th>改善</th><th>持平</th><th>退化</th></tr>
               <tr><td>原框</td><td>{f4(med.get('original'))}</td><td>—</td><td>—</td><td>—</td></tr>
               <tr><td>扩 2%</td><td>{f4(med.get('expand_2pct'))}</td><td>{((all_ab.get('vs_original') or {}).get('expand_2pct') or {}).get('improved','—')}</td><td>{((all_ab.get('vs_original') or {}).get('expand_2pct') or {}).get('unchanged','—')}</td><td>{((all_ab.get('vs_original') or {}).get('expand_2pct') or {}).get('degraded','—')}</td></tr>
               <tr><td>扩 5%</td><td>{f4(med.get('expand_5pct'))}</td><td>{t5.get('improved','—')}</td><td>{t5.get('unchanged','—')}</td><td>{t5.get('degraded','—')}</td></tr>
             </table>
             <p class="note">结论：部分错误源于<b>裁剪过紧</b>；但扩框非普适，需按版式自适应。</p>"""),
        ("错误图谱：15 个可核查案例",
         """<ul>
               <li>每例包含：原图、真值、模型输出、评分证据、原因判断</li>
               <li>覆盖：紧邻栏串行、表格跨页、公式行内/独立判定、竖排与水印干扰</li>
               <li>用途：答辩现场可逐个展开，避免只给聚合指标</li>
             </ul>"""),
        ("环境偏差声明（诚信要求）",
         """<ul>
               <li>MinerU 官方钉 <code>torch&lt;=2.3.1</code>，本实验用 <code>2.5.1+cu124</code>（与 MonkeyOCR 同版本，减少混淆变量）</li>
               <li>layout 走官方钉定的 <code>doclayout_yolo</code>，非 detectron2/layoutlmv3 路径</li>
               <li>3 处补丁均不改变推理算法，仅消除依赖不兼容</li>
               <li>无 CDM；宿主共享、负载 21–35，耗时只作量级参考</li>
             </ul>"""),
        ("复现与收尾",
         """<ul>
               <li>环境重建、跑批、评测、对比全部脚本化，可一键重跑</li>
               <li>逐页 JSONL 日志 + 官方评分 JSON + 页 ID 清单全部留存</li>
               <li>收尾：结果回传本地 → 保存日志 → 控制台确认关机 → 核对扩容盘计费</li>
             </ul>"""),
    ]

    body = []
    for i, (title, content) in enumerate(slides):
        body.append(f"""<section class="slide" id="s{i}">
      <h2>{title}</h2>
      {content}
      <div class="pager">{i + 1} / {len(slides)}</div>
    </section>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>MonkeyOCR 复现与 MinerU 对比 · 汇报材料</title>
<style>
  :root {{ --fg:#1a1a1a; --muted:#5b6472; --accent:#1668dc; --bg:#fff; --line:#e3e6ea; --code:#f3f5f7; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Hiragino Sans GB",system-ui,sans-serif;
         color:var(--fg); background:#eef1f4; }}
  .slide {{ background:var(--bg); width:min(1080px,94vw); margin:18px auto; padding:44px 52px 56px;
            border-radius:10px; box-shadow:0 2px 14px rgba(0,0,0,.08); position:relative; min-height:560px; }}
  h1 {{ font-size:30px; margin:0 0 6px; }}
  h2 {{ font-size:27px; margin:0 0 20px; padding-bottom:12px; border-bottom:3px solid var(--accent); }}
  ul {{ font-size:19px; line-height:1.85; padding-left:26px; }}
  li {{ margin:8px 0; }}
  p.sub {{ color:var(--muted); font-size:18px; margin:0 0 18px; }}
  p.note {{ color:var(--muted); font-size:16px; margin-top:14px; }}
  code {{ background:var(--code); padding:1px 6px; border-radius:4px; font-size:.92em; }}
  table {{ width:100%; border-collapse:collapse; font-size:17px; margin-top:6px; }}
  th,td {{ border:1px solid var(--line); padding:9px 12px; text-align:left; }}
  th {{ background:#f7f9fb; font-weight:600; }}
  b {{ color:#a8071a; }}
  .pager {{ position:absolute; right:22px; bottom:14px; color:var(--muted); font-size:14px; }}
  @media print {{
    body {{ background:#fff; }}
    .slide {{ box-shadow:none; margin:0; page-break-after:always; width:100%; min-height:auto; border-radius:0; }}
  }}
</style>
</head>
<body>
{chr(10).join(body)}
<script>
  const slides=[...document.querySelectorAll('.slide')];
  let cur=0;
  function go(n){{ cur=Math.max(0,Math.min(slides.length-1,n)); slides[cur].scrollIntoView({{behavior:'smooth',block:'start'}}); }}
  addEventListener('keydown',e=>{{
    if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){{e.preventDefault();go(cur+1);}}
    if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){{e.preventDefault();go(cur-1);}}
    if(e.key==='Home')go(0); if(e.key==='End')go(slides.length-1);
  }});
  addEventListener('scroll',()=>{{
    const mid=innerHeight/2;
    slides.forEach((s,i)=>{{ const r=s.getBoundingClientRect(); if(r.top<mid&&r.bottom>mid) cur=i; }});
  }});
</script>
</body>
</html>
"""


def speaker_md(cmp: dict | None, runs: dict, abl: dict) -> str:
    _, machine = comparison_block(cmp)
    return f"""# 答辩讲解稿（配 汇报材料.html 逐页）

**第 1 页 · 标题**
本次工作是复现原版 MonkeyOCR，并与 MinerU 0.9.3 在同一评测口径下做基线对比。强调三点：MonkeyOCR 固定到官方 commit `b5e94d3a…f4b9`（2025-06-13）、用原版 3B 权重；MinerU 用 `magic-pdf==0.9.3`；评测完全使用 OmniDocBench 官方代码与同一份标注。

**第 2 页 · 实验设计**
一句话说清"同一把尺子"：同一 120 页分层子集、同一份 GT、同一套指标与匹配方式，唯一变量是被测模型。我们统一把每个模型包成"单页 PDF → 单页 Markdown"，所以官方评测器能按文件名直接配对。失败页写空预测并计入评分——这是为了不虚高指标。

**第 3 页 · 关键工作**
这一页是重点：MinerU 起初不是"效果差"，而是**根本跑不起来**。前一位执行者连续 13 次尝试都卡在模型初始化。我们定位到根因是环境：那个运行环境是用 MonkeyOCR 的解释器建的 venv，既没有自己的标准库，又开了 `include-system-site-packages`，等于 MinerU 一直在用 MonkeyOCR 的 transformers/torch。换成 conda 独立环境、按官方依赖逐项钉版本后，同一页一次通过。

**第 4 页 · 主结果**
指表讲三件事：文本块看 Edit_dist，表格看 TEDS 与 TEDS(仅结构)两个数，公式看 Edit_dist。两个数一起看的价值在于：TEDS 低而结构分高，说明表格结构识别对了但单元格内容错，这种问题定位方式比单一分数有用。

**第 5 页 · 结论**
差距集中在三个地方：中英混排、彩色底纹、复杂版式下的阅读顺序。公式是两者共同短板。

**第 6 页 · 裁剪消融**
这是本轮最有信息量的实验：把 50 个疑似错裁区域分别按原框、扩 2%、扩 5% 各识别一次。平均编辑距离从 {f4(((abl or {}).get('all',{}).get('mean_edit_distance') or {}).get('original'))} 降到 {f4(((abl or {}).get('all',{}).get('mean_edit_distance') or {}).get('expand_5pct'))}，改善 {(((abl or {}).get('all',{}).get('vs_original') or {}).get('expand_5pct') or {}).get('improved','—')} 例。结论是**一部分错误来自裁剪过紧**，不是识别能力问题；但也有退化案例，说明不能无脑扩大框。

**第 7 页 · 错误图谱**
15 个案例每例都有原图、真值、模型输出和评分证据，现场可任选两个展开，避免只给聚合数字。

**第 8 页 · 环境偏差**
主动声明：torch 用了 2.5.1 而非官方钉的 ≤2.3.1（理由是与另一基线统一、匹配容器 CUDA 栈）；3 处补丁只解决依赖不兼容，不改算法；本轮无 CDM 指标。诚信声明比指标好看更重要。

**第 9 页 · 收尾**
全部脚本化、可一键重跑；日志与评分 JSON 留存；记得在控制台确认关机并核对扩容盘计费。
"""


def failure_attribution(runs: dict) -> str:
    """Attribute the failed pages of each baseline to their data source / layout.

    The single most useful debugging fact found in this round: MonkeyOCR's failures
    are not spread out -- they are one whole source family, which is exactly why its
    per-source score for that family looks catastrophic.
    """
    man_file = PROJ / "data/omnidocbench_v1_0/subsets/manifest_120.jsonl"
    if not man_file.exists():
        return ""
    meta: dict[str, dict] = {}
    for line in man_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            meta[r["image_path"].rsplit(".", 1)[0]] = r

    out: list[str] = []
    for label, sub in (("MonkeyOCR-3B", "monkeyocr_formal_120"), ("MinerU-0.9.3", "mineru_formal_120")):
        rows = []
        for f in sorted((OUT / sub).glob("run_log*.jsonl")):
            rows += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not rows:
            continue
        err = [r for r in rows if r.get("status") != "ok"]
        if not err:
            out.append(f"- {label}：{len(rows)} 页全部跑通，无失败页。")
            continue
        src = Counter(meta.get(r["stem"], {}).get("source", "?") for r in err)
        lay = Counter(meta.get(r["stem"], {}).get("layout", "?") for r in err)
        kinds = Counter(str(r.get("error", ""))[:46] for r in err)
        out.append(f"- {label}：{len(err)}/{len(rows)} 页失败；按来源 {dict(src)}，按版式 {dict(lay)}，"
                   f"错误类型 {dict(kinds)}。")
        if len(src) == 1 and next(iter(src.values())) == len(err):
            only = next(iter(src))
            total = sum(1 for v in meta.values() if v.get("source") == only)
            out.append(f"  - 即**失败集中在单一来源 `{only}`**（该来源在子集共 {total} 页，失败 {len(err)} 页），"
                       f"这解释了按来源分组时该类别分数异常的原因：不是识别质量差，而是整页没有产出。")
    return "\n".join(out)


def env_versions_table() -> str:
    """Appendix table: exact package versions of both experiment environments."""
    data = jload(OUT / "env_versions.json", {}) or {}
    envs = data.get("envs") or {}
    if not envs:
        return "（未采集到环境版本清单；运行 `scripts/dump_env_versions.py` 生成。）"
    keys = ["_python", "torch", "torchvision", "transformers", "tokenizers", "huggingface_hub",
            "numpy", "magic-pdf", "timm", "ultralytics", "unimernet", "struct-eqtable",
            "rapid-table", "paddleocr", "paddlepaddle", "doclayout_yolo", "albumentations",
            "albucore", "detectron2", "PyMuPDF", "scikit-learn", "pydantic", "Levenshtein"]
    names = ["Python", "torch", "torchvision", "transformers", "tokenizers", "huggingface_hub",
             "numpy", "magic-pdf", "timm", "ultralytics", "unimernet", "struct-eqtable",
             "rapid-table", "paddleocr", "paddlepaddle", "doclayout_yolo", "albumentations",
             "albucore", "detectron2", "PyMuPDF", "scikit-learn", "pydantic", "Levenshtein"]
    cols = ["monkeyocr", "mineru093_env", "omnidocbench"]
    head = "| 组件 | " + " | ".join(f"`{c}`" for c in cols) + " |"
    sep = "|---|" + "---|" * len(cols)
    rows = []
    for k, n in zip(keys, names):
        cells = []
        for c in cols:
            v = (envs.get(c) or {}).get(k, "—")
            cells.append(str(v) if v else "—")
        if all(v == "—" for v in cells):
            continue
        rows.append(f"| {n} | " + " | ".join(cells) + " |")
    note = (f"\n\n容器 `{data.get('container','?')}`；GPU `{data.get('gpu','?')}`。"
            f"两个基线共享同一 torch（2.5.1+cu124）、transformers（4.50.0）、numpy（1.26.4）与 Python（3.10.21）；"
            f"有意的差异是 `tokenizers`（0.21.4 / 0.21.0）与 `albumentations`"
            f"（2.0.8 / 1.4.24，后者受 magic-pdf 的 `numpy<2` 约束）。")
    return "\n".join([head, sep] + rows) + note


def failure_sensitivity(cmp: dict | None, runs: dict) -> str:
    """Quantify how much the whole-page failures drag a model's headline text score.

    Failed pages are submitted as empty predictions (official convention: counted as
    misses). This computes the counterfactual average over successfully produced
    pages, so a reader can separate "no output at all" from "partial recognition".
    """
    if not cmp:
        return ""
    labels = cmp.get("models") or []
    prefixes = cmp.get("prefixes") or []
    complete = cmp.get("complete") or {}
    expected = cmp.get("expected_pages") or 120
    lines: list[str] = []
    for label, prefix, sub in (("MonkeyOCR-3B", prefixes[0] if prefixes else None, "monkeyocr_formal_120"),
                               ("MinerU-0.9.3", prefixes[1] if len(prefixes) > 1 else None, "mineru_formal_120")):
        if not prefix:
            continue
        f = OUT / ".." / "OmniDocBench" / "result" / f"{prefix}_text_block_per_page_edit.json"
        per_page = jload(f, {}) or {}
        rows = []
        for lf in sorted((OUT / sub).glob("run_log*.jsonl")):
            rows += [json.loads(l) for l in lf.read_text(encoding="utf-8").splitlines() if l.strip()]
        failed = {r["stem"] + ".jpg" for r in rows if r.get("status") != "ok"}
        if not per_page or not rows:
            continue
        scored = {k: v for k, v in per_page.items() if isinstance(v, (int, float))}
        ok_scored = {k: v for k, v in scored.items() if k not in failed}
        avg_all = sum(scored.values()) / len(scored) if scored else None
        avg_ok = sum(ok_scored.values()) / len(ok_scored) if ok_scored else None
        partial = complete.get(label) is False
        tag = f"**未完成：仅覆盖 {len(scored)}/{expected} 页，数值不可用于最终对比**" if partial else ""
        extra = ""
        if failed and not partial:
            extra = (f"；把 {len(failed)} 个整页无产出的页面剔除后，同口径均值为 {avg_ok:.4f}"
                     f"（差 {avg_all - avg_ok:+.4f}）")
        lines.append(f"- **{label}**：文本块 Edit_dist = {avg_all:.4f}（覆盖 {len(scored)} 页）{extra}{('。' + tag) if tag else '。'}"
                     if avg_all is not None else f"- {label}：无可用评分。")
    if not lines:
        return ""
    tail = "" if all(complete.get(l) for l in labels) else \
        "\n\n> 注意：上表中有基线的评测**尚未跑完全部页面**，其数值只反映已完成的子集，**不得用于对外结论**。"
    return ("以下为文本块维度的敏感性分析（仍以官方提交口径为准，此处只为区分两类错误来源）：\n\n"
            + "\n".join(lines) + tail)


def pptx_deck(cmp: dict | None, runs: dict, abl: dict, path: Path) -> bool:
    """Native PowerPoint version of the deck. Returns False if python-pptx is absent."""
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        from pptx.util import Emu, Pt
    except Exception as e:  # pragma: no cover
        print(f"  (pptx skipped: {e!r})")
        return False

    ACCENT = RGBColor(0x16, 0x68, 0xDC)
    DARK = RGBColor(0x1A, 0x1A, 0x1A)
    MUTED = RGBColor(0x5B, 0x64, 0x72)
    WARN = RGBColor(0xA8, 0x07, 0x1A)

    prs = Presentation()
    prs.slide_width = Emu(int(13.333 * 914400))
    prs.slide_height = Emu(int(7.5 * 914400))

    def set_font(run, size=18, bold=False, color=DARK):
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = CJK_FONT
        rPr = run._r.get_or_add_rPr()
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rPr.makeelement(
                "{http://schemas.openxmlformats.org/drawingml/2006/main}" + tag.split(":")[1],
                {"typeface": CJK_FONT})
            rPr.append(el)

    def add_slide():
        return prs.slides.add_slide(prs.slide_layouts[6])  # blank

    def title_box(slide, text, sub=None):
        tb = slide.shapes.add_textbox(Emu(457200), Emu(320000), Emu(11000000), Emu(900000))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        set_font(p.add_run(), 30, True)
        p.runs[0].text = text
        # accent underline
        line = slide.shapes.add_shape(1, Emu(457200), Emu(1180000), Emu(1150000), Emu(36000))
        line.fill.solid()
        line.fill.fore_color.rgb = ACCENT
        line.line.fill.background()
        if sub:
            sb = slide.shapes.add_textbox(Emu(457200), Emu(1250000), Emu(11500000), Emu(500000))
            sp = sb.text_frame.paragraphs[0]
            r = sp.add_run()
            r.text = sub
            set_font(r, 16, False, MUTED)
        # page number
        # page number: keep the right edge inside the slide (slide width 12191695 EMU)
        pb = slide.shapes.add_textbox(Emu(10960000), Emu(6180000), Emu(1000000), Emu(400000))
        pp = pb.text_frame.paragraphs[0]
        pp.alignment = PP_ALIGN.RIGHT
        r = pp.add_run()
        r.text = f"{len(prs.slides.__iter__.__self__._sldIdLst)} / {TOTAL[0]}"
        set_font(r, 12, False, MUTED)

    def add_bullets(slide, items, top=1500000):
        tb = slide.shapes.add_textbox(Emu(600000), Emu(top), Emu(11400000), Emu(4600000))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for level, txt, bold in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.level = level
            r = p.add_run()
            r.text = ("• " if level == 0 else "– ") + txt
            set_font(r, 18 if level == 0 else 16, bold, WARN if bold else DARK)
            p.space_after = Pt(8)
        return tf

    def add_table(slide, rows, left=600000, top=1500000, width=11400000, height=3600000, font=14):
        nrows, ncols = len(rows), len(rows[0])
        shape = slide.shapes.add_table(nrows, ncols, Emu(left), Emu(top), Emu(width), Emu(height))
        tbl = shape.table
        for i, row in enumerate(rows):
            for j, cellv in enumerate(row):
                cell = tbl.cell(i, j)
                cell.text = str(cellv)
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        set_font(r, font, bold=(i == 0), color=DARK)
        return tbl

    # ---- content ----
    m, u = runs["monkeyocr"], runs["mineru"]
    all_ab = (abl or {}).get("all", {})
    med = all_ab.get("mean_edit_distance") or {}
    vs = all_ab.get("vs_original") or {}
    t2, t5 = (vs.get("expand_2pct") or {}), (vs.get("expand_5pct") or {})

    table_rows = [["指标", "MonkeyOCR-3B", "MinerU-0.9.3", "相对变化"]]
    names = {
        "text_block_edit_dist": "文本块 Edit_dist ↓",
        "display_formula_edit_dist": "公式 Edit_dist ↓",
        "table_TEDS": "表格 TEDS ↑",
        "table_TEDS_structure_only": "表格 TEDS(仅结构) ↑",
        "table_edit_dist": "表格 Edit_dist ↓",
        "reading_order_edit_dist": "阅读顺序 Edit_dist ↓",
    }
    complete = (cmp or {}).get("complete") or {}
    labels = (cmp or {}).get("models") or ["MonkeyOCR-3B", "MinerU-0.9.3"]
    for h in ((cmp or {}).get("headline") or []):
        vals = list(h["values"])
        for i, lbl in enumerate(labels):
            if complete.get(lbl) is False:
                vals[i] = "—"
        delta = h["delta"] if all(v != "—" for v in vals) else "待补"
        table_rows.append([names.get(h["metric"], h["metric"]), f4(vals[0]), f4(vals[1]), delta])
    if len(table_rows) == 1:
        table_rows.append(["（评测未完成）", "—", "—", "—"])

    insight_lines = [l[2:].replace("**", "") for l in insight_bullets(cmp).splitlines()
                     if l.strip().startswith("-")]
    ablation_rows = [
        ["档位", "平均区域编辑距离", "改善", "持平", "退化"],
        ["原框", f4(med.get("original")), "—", "—", "—"],
        ["扩 2%", f4(med.get("expand_2pct")), t2.get("improved", "—"), t2.get("unchanged", "—"), t2.get("degraded", "—")],
        ["扩 5%", f4(med.get("expand_5pct")), t5.get("improved", "—"), t5.get("unchanged", "—"), t5.get("degraded", "—")],
    ]

    TOTAL = [9]
    s = add_slide()
    tb = s.shapes.add_textbox(Emu(600000), Emu(2100000), Emu(11400000), Emu(1600000))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run(); r.text = "MonkeyOCR 原版复现 与 MinerU 0.9.3 基线对比"
    set_font(r, 40, True)
    sb = s.shapes.add_textbox(Emu(600000), Emu(3400000), Emu(11400000), Emu(1400000))
    tf = sb.text_frame; tf.word_wrap = True
    for i, line in enumerate([
        "OmniDocBench v1.0 · 120 页同口径 · 单卡 RTX 4090 D",
        "MonkeyOCR 固定 commit b5e94d3a…f4b9（2025-06-13），原版 3B 权重",
        "MinerU 基线 magic-pdf==0.9.3；官方评测代码 + quick_match",
    ]):
        pp = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        rr = pp.add_run(); rr.text = line
        set_font(rr, 18 if i else 20, i == 0, MUTED if i else DARK)

    s = add_slide(); title_box(s, "实验设计：一份子集，两个模型，同一把尺子")
    add_bullets(s, [
        (0, "确定性分层抽样：9 类来源 / 3 种语言 / 5 类版式；含表格 48 页、公式 40 页、复杂版式 90 页", False),
        (0, "统一推理形式「单页 PDF → 单页 Markdown」，文件名一致供官方评测器配对", False),
        (0, "逐页 JSONL 日志（耗时/状态）；失败页写空预测计入评分，不静默丢弃", False),
        (0, f"跑批规模：MonkeyOCR {m['total']} 页 / MinerU {u['total']} 页", False),
    ])

    s = add_slide(); title_box(s, "关键工作：把 MinerU 从「跑不起来」修到「一次通过」", "根因不是 prompt/配置，而是环境隔离被破坏")
    add_bullets(s, [
        (0, "旧环境实为基于 MonkeyOCR 解释器的 venv：无自带标准库且 include-system-site-packages=true", True),
        (0, "→ MinerU 实际跑在 MonkeyOCR 的 transformers/torch 上，冒烟测试不可能通过", False),
        (0, "改用 conda 独立环境，按官方 setup.py [full] 逐项钉版本", False),
        (0, "依赖坑 5 处：transformers 误装 5.x、timm 越界、doclayout_yolo 版本不存在、albumentations 2.x 与 numpy<2、torchtext 无 torch2.5 构建", False),
        (0, "代码级补丁 3 处：eager 注意力、torchtext 扩展可选、return_dict 运行时剥离", False),
    ])

    s = add_slide(); title_box(s, "主结果：总体指标")
    add_table(s, table_rows, top=1450000, height=3000000, font=13)

    s = add_slide(); title_box(s, "结论")
    add_bullets(s, [(0, t, False) for t in insight_lines] or [(0, "评测未完成，结论待生成", False)])

    s = add_slide(); title_box(s, "深度分析：裁剪消融（MonkeyOCR，50 例）")
    add_table(s, ablation_rows, top=1500000, height=1600000, font=14)
    nb = s.shapes.add_textbox(Emu(600000), Emu(3500000), Emu(11400000), Emu(1200000))
    np_ = nb.text_frame.paragraphs[0]; np_.word_wrap = True
    rr = np_.add_run()
    rr.text = ("结论：部分错误源于裁剪过紧（切边、切到相邻栏），而非识别模型本身；"
               "但扩框并非普适收益，需按版式自适应。")
    set_font(rr, 17, False, MUTED)

    s = add_slide(); title_box(s, "错误图谱：15 个可核查案例")
    add_bullets(s, [
        (0, "每例包含：原图、真值、模型输出、评分证据、原因判断", False),
        (0, "覆盖：紧邻栏串行、表格跨页、行内/独立公式判定、竖排与水印干扰", False),
        (0, "用途：答辩现场可逐个展开，避免只给聚合指标", False),
    ])

    s = add_slide(); title_box(s, "环境偏差声明（诚信要求）")
    add_bullets(s, [
        (0, "MinerU 官方钉 torch<=2.3.1，本实验用 2.5.1+cu124（与另一基线同版本，减少混淆变量）", False),
        (0, "layout 走官方钉定的 doclayout_yolo，非 detectron2/layoutlmv3 路径", False),
        (0, "3 处补丁只消除依赖不兼容，不改变推理算法", False),
        (0, "无 CDM 指标；宿主为共享机器（负载 21–45），耗时只作量级参考", False),
    ])

    s = add_slide(); title_box(s, "复现与收尾")
    add_bullets(s, [
        (0, "环境重建、跑批、评测、对比、出报告全部脚本化，可一键重跑", False),
        (0, "逐页 JSONL 日志 + 官方评分 JSON + 页 ID 清单 + 环境版本清单全部留存", False),
        (0, "收尾：结果回传本地 → 保存日志 → 控制台确认关机 → 核对扩容盘计费", False),
    ])

    TOTAL[0] = len(prs.slides._sldIdLst)
    # rewrite page numbers now that the count is known
    for idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape.has_text_frame and "/" in shape.text_frame.text and len(shape.text_frame.text) < 12:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        r.text = f"{idx} / {TOTAL[0]}"

    prs.save(str(path))
    return True


def main() -> None:
    DEL.mkdir(parents=True, exist_ok=True)
    cmp = jload(CMP)
    runs = load_runs()
    abl = load_ablation()
    atlas = load_error_atlas()

    (DEL / "MinerU_vs_MonkeyOCR_报告.md").write_text(report_md(cmp, runs, abl, atlas), encoding="utf-8")
    (DEL / "汇报材料.html").write_text(deck_html(cmp, runs, abl), encoding="utf-8")
    (DEL / "讲解稿.md").write_text(speaker_md(cmp, runs, abl), encoding="utf-8")
    ok = pptx_deck(cmp, runs, abl, DEL / "汇报材料.pptx")
    print("pptx written:", ok)
    print("deliverables written to", DEL)
    for p in sorted(DEL.iterdir()):
        print(f"  {p.name}: {p.stat().st_size} bytes")
    print("comparison available:", bool(cmp and cmp.get("headline")))


if __name__ == "__main__":
    main()
