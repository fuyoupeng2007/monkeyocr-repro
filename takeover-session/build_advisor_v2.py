#!/usr/bin/env python3
"""Rewrite the advisor-facing report with an explicit division of labour:

  * environment engineering is attributed to the AI coding agents (Codex / DSH)
  * the paper-reproduction content is restructured as the spine of the report,
    ordered 读懂论文 -> 固定复现对象 -> 设计评测 -> 实现推理 -> 官方评测 -> 验证论点 -> 新发现

Output: deliverables/给导师的汇报_MonkeyOCR复现_v2.docx
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
DEL = HERE / "deliverables"
SYNC = HERE / "sync"

CJK = "微软雅黑"
ACCENT = RGBColor(0x16, 0x68, 0xDC)
WARN = RGBColor(0xA8, 0x07, 0x1A)
MUTED = RGBColor(0x5B, 0x64, 0x72)

MINERU_DONE, TOTAL = 81, 120


# ---------------------------------------------------------------- helpers
def set_run(run, size=10.5, bold=False, color=None, font=CJK):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font
    if color is not None:
        run.font.color.rgb = color
    rf = run._element.get_or_add_rPr().get_or_add_rFonts()
    rf.set(qn("w:ascii"), font)
    rf.set(qn("w:hAnsi"), font)
    rf.set(qn("w:eastAsia"), font)


def para(doc, text="", size=10.5, bold=False, color=None, align=None,
         space_before=0, space_after=6, indent=0, line=1.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    if text:
        set_run(p.add_run(text), size=size, bold=bold, color=color)
    return p


def heading(doc, text, level=1):
    sizes = {1: 16, 2: 13, 3: 11.5}
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(16 if level == 1 else 12)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.3
    set_run(p.add_run(text), size=sizes.get(level, 11.5), bold=True,
            color=ACCENT if level <= 2 else None)
    if level == 1:
        pPr = p._element.get_or_add_pPr()
        bdr = pPr.makeelement(qn("w:pBdr"), {})
        bdr.append(bdr.makeelement(qn("w:bottom"), {
            qn("w:val"): "single", qn("w:sz"): "8", qn("w:space"): "1", qn("w:color"): "1668DC"}))
        pPr.append(bdr)
    return p


def bullet(doc, text, level=0, head=None):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    pf = p.paragraph_format
    pf.space_after = Pt(3)
    pf.line_spacing = 1.45
    if head:
        set_run(p.add_run(head), size=10.5, bold=True)
    set_run(p.add_run(text), size=10.5)
    return p


def table(doc, rows, widths=None, font=9):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ""
            p = cells[j].paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            set_run(p.add_run(str(val)), size=font, bold=(i == 0))
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows:
                row.cells[j].width = Cm(w)
    return t


def note(doc, text, color=WARN):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(8)
    pf.left_indent = Cm(0.35)
    pf.line_spacing = 1.45
    set_run(p.add_run(text), size=10, color=color)
    return p


def setup(doc, title, subtitle):
    s = doc.sections[0]
    s.top_margin = Cm(2.2)
    s.bottom_margin = Cm(2.0)
    s.left_margin = Cm(2.4)
    s.right_margin = Cm(2.4)
    st = doc.styles["Normal"]
    st.font.name = CJK
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), CJK)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    set_run(p.add_run(title), size=19, bold=True)
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after = Pt(14)
    set_run(q.add_run(subtitle), size=11, color=MUTED)


# ---------------------------------------------------------------- data
def load():
    cmp = json.loads((DEL / "compare" / "comparison.json").read_text(encoding="utf-8"))
    abl = json.loads((SYNC / "outputs" / "crop_ablation_50" / "summary_comparison.json")
                     .read_text(encoding="utf-8"))
    log = [json.loads(l) for l in (SYNC / "outputs" / "monkeyocr_formal_120" / "run_log.jsonl")
           .read_text(encoding="utf-8").splitlines() if l.strip()]
    return cmp, abl, log


# ---------------------------------------------------------------- report
def build() -> Path:
    cmp, abl, log = load()
    m = {h["metric"]: h["values"] for h in cmp["headline"]}
    ok = [r for r in log if r.get("status") == "ok"]
    err = [r for r in log if r.get("status") != "ok"]
    secs = sorted(r["seconds"] for r in ok if r.get("seconds"))
    med = secs[len(secs) // 2] if secs else None
    ab = abl["all"]
    am = ab["mean_edit_distance"]
    t5 = ab["vs_original"]["expand_5pct"]
    t2 = ab["vs_original"]["expand_2pct"]
    imp = (am["original"] - am["expand_5pct"]) / am["original"]

    doc = Document()
    setup(doc, "MonkeyOCR 论文复现汇报",
          "原版 3B 模型的推理复现、官方基准评测与方法验证 · 2026-09-18")

    # ============ 一、摘要
    heading(doc, "一、工作摘要", 1)
    para(doc, "本阶段工作分为两部分：**论文核心内容的复现**（主要工作）与**实验环境的构建**（支撑性工作）。"
              "两部分的分工在报告中明确标注，以便您判断各项成果的性质。", line=1.5)

    table(doc, [
        ["工作部分", "内容", "完成主体"],
        ["论文核心复现", "读懂论文方法、固定复现对象、设计评测子集、实现统一推理流程、"
                         "运行官方评测、验证论文核心论点、产出新的实验发现", "本人主导"],
        ["实验环境构建", "依赖版本解析、环境隔离修复、兼容性问题排查（10 项阻断问题）、"
                         "冒烟验证与跑批脚本", "AI 编程代理（Codex、DSH）主导，本人验收"],
        ["导师汇报材料", "分阶段汇报、正式报告、论文全文中文翻译", "本人整理"],
    ], widths=[3.2, 10.2, 4.0], font=9)

    para(doc, "**核心结论**：论文的方法在本实验条件下复现成功，指标量级与论文趋势一致；"
              "论文提出的「流水线式方法存在误差传播「这一核心论点得到实验证实；"
              "同时发现了一个论文未提及、但影响更大的工程缺陷（详见第七节）。", line=1.5, space_before=4)

    # ============ 二、论文讲的是什么
    heading(doc, "二、论文内容与复现目标", 1)

    heading(doc, "2.1 论文要解决的问题", 2)
    para(doc, "论文（arXiv:2506.05218v1，华中科技大学与金山办公）针对文档解析任务，指出现有两条技术路线各有硬伤：", line=1.5)
    bullet(doc, "把流程拆成一串子模块（版面检测→裁切→识别→表格→公式）。"
                "致命问题是**误差累积**：前一阶段裁切不准，错误会传播并放大。"
                "论文图 2 给出了具体例子——公式检测框稍有偏差，把上一行字符切了进来，"
                "结果公式输出凭空空多出一个上标。", head="流水线式（MinerU、Marker、Docling）：")
    bullet(doc, "把整页直接交给一个大模型。问题是文档分辨率高、序列长，注意力机制是平方复杂度，"
                "速度与可扩展性都受限。论文实测 Qwen2.5-VL-7B 的推理速度只有 MinerU 的 18%，效果还更差。",
           head="端到端式（Qwen2.5-VL 等）：")

    heading(doc, "2.2 论文提出的方法：SRR 三元组范式", 2)
    para(doc, "论文把文档解析拆成三个基本问题，各自用最合适的模型解决：", line=1.5)
    table(doc, [
        ["阶段", "回答的问题", "实现方式"],
        ["结构（Structure）", "在哪里？", "基于 YOLO 的版面检测器，输出边界框与元素类型（文本/表格/公式/图…）"],
        ["识别（Recognition）", "是什么？", "每个区域裁切后，连同**类型专属提示词**并行送入 3B 多模态大模型"],
        ["关系（Relation）", "如何组织？", "专用块级阅读顺序模型，为每个元素预测阅读序号，再重新组装"],
    ], widths=[3.4, 2.6, 11.4], font=9)
    para(doc, "**关键设计是块级并行识别**：每个裁切区域单独识别，不需要把整页塞进超长上下文。"
              "这样既避免了流水线的误差累积（识别模型看到的是完整区域，而非层层传递的错误结果），"
              "又避免了整页端到端的效率问题。", line=1.5, space_before=4)
    para(doc, "配套数据集 **MonkeyDoc** 是论文的另一半贡献：390 万块级实例，覆盖 5 类任务、"
              "十余种文档类型、中英双语；其中结构检测数据 8.8 万页公开数据 + 4.1 万页中文补充，"
              "表格 47 万、公式 52.6 万中文合成样本等。", line=1.5)

    heading(doc, "2.3 论文报告的结果", 2)
    table(doc, [
        ["对比对象", "论文声称的提升"],
        ["vs MinerU（流水线式代表）", "整体平均 +5.1%；公式 +15.0%；表格 +8.6%；中文整体编辑距离 >6%"],
        ["vs Mistral OCR", "整体编辑距离 +13.8%；公式 +9.8%；表格 +9.3%"],
        ["vs Qwen2.5-VL-72B（英文）", "+7.4%"],
        ["vs Gemini 2.5 Pro（英文）", "+0.8%（中文上 Gemini 略优，论文承认仍有提升空间）"],
        ["速度", "单页 0.24 页/秒（MinerU 0.28）；多页 0.84 页/秒（MinerU 0.65）"],
        ["训练成本", "3B 模型，32 张 A800 训练 53 小时；推理可单张 RTX 3090"],
    ], widths=[5.6, 11.8], font=9)

    heading(doc, "2.4 本次复现的目标界定", 2)
    para(doc, "论文的训练成本是 53 小时 × 32 张 A800，且训练数据（MonkeyDoc 390 万实例）未完整公开。"
              "因此本次复现的目标明确限定为**推理复现**：使用官方发布的权重，"
              "在公开基准上独立评测，验证论文的方法与结论是否成立。**不做训练复现**，"
              "这一点必须在报告中说明，避免夸大。", line=1.5)

    # ============ 三、复现核心工作（按步骤）
    heading(doc, "三、论文复现的核心工作（按执行步骤）", 1)
    para(doc, "以下六步构成复现的主体，按依赖顺序排列。每一步都说明「为什么这么做」，"
              "以便区分「照做」与「判断」。", line=1.5, color=MUTED, size=10)

    heading(doc, "步骤一：把论文读成可执行的规格", 2)
    para(doc, "论文是技术报告体例，方法部分给出了三阶段的定义，但没有给出可直接照抄的工程参数。"
              "本步骤把它转成可执行的规格：确定「三阶段各自的输入输出」、"
              "\"识别阶段需要类型专属提示词\"、\"区域之间需要建立阅读顺序\"。", line=1.5)
    bullet(doc, "输出物：SRR 三阶段的流程图与各阶段接口定义（见本报告 2.2 节）。", head="产出：")
    bullet(doc, "论文没有公开 MonkeyDoc 的完整标注，所以训练侧无法复刻；"
                "但评测侧只需官方权重 + 公开基准，这是可以完整复现的部分。", head="判断：")

    heading(doc, "步骤二：固定复现对象，避免「版本漂移」", 2)
    para(doc, "论文正文提到「代码与模型将发布」，但仓库在持续更新，后续的 pro-1.2B、pro-3B、v2 "
              "与论文中的模型**并非同一个**。如果直接拉最新版，指标不可比。", line=1.5)
    table(doc, [
        ["项目", "本次固定的选择", "理由"],
        ["代码提交", "b5e94d3aed972e2e07e7d5c654a0dc588419f4b9（2025-06-13）",
         "属于论文对应的原版代码线，且包含发布后一周内的关键修复（3090 共享内存、单任务推理）"],
        ["模型权重", "echo840/MonkeyOCR 原版 3B", "论文所用模型，非 pro / v2"],
        ["对话模型后端", "LMDeploy 0.8.0", "论文指出与 LMDeploy 集成后可在 3090 运行；官方配置默认即此后端"],
        ["版面/阅读顺序", "doclayout_yolo + layoutreader", "官方配置默认"],
    ], widths=[3.2, 5.6, 8.6], font=9)

    heading(doc, "步骤三：设计评测子集（为什么不能随机抽）", 2)
    para(doc, "论文在 OmniDocBench 全量 981 页上评测。本实验受算力限制，取 120 页子集，"
              "但**没有随机抽取**，而是做确定性分层抽样（随机种子 250605）：", line=1.5)
    bullet(doc, "9 类文档来源各取 13–14 页（试卷、学术文献、彩色教材、图书、报纸、杂志、PPT、研究报告、笔记）；")
    bullet(doc, "语言分布：简中 52 / 英文 44 / 中英混排 24；")
    bullet(doc, "版式分布：单栏 30 / 双栏 23 / 三栏 22 / 混合 23 / 其他 22；")
    bullet(doc, "含表格 48 页、公式 40 页、复杂版式 90 页；先跑 20 页试跑集确认流程，再上 120 页。")
    para(doc, "**为什么这么做**：论文表 3 显示不同文档类型差距极大（MinerU 在图书上 0.055，"
              "在笔记上 0.984）。纯随机抽容易抽偏，导致结果不可比；分层抽样保证每类都有代表。"
              "页号清单、抽样脚本与数据来源 provenance 全部留存，他人可复现同一子集。", line=1.5, space_before=4)

    heading(doc, "步骤四：实现统一推理流程（关键工程判断）", 2)
    para(doc, "官方评测器按预测文件名与真值配对，因此必须把模型输出整理成规定形式。"
              "本步骤做的几个判断：", line=1.5)
    bullet(doc, "把模型包成**"单页 PDF → 单页 Markdown"**，文件命名与真值严格对齐，"
                "否则评测器会配对失败并静默跳过。", head="统一接口：")
    bullet(doc, "**失败页写入空文件**，由官方评测计为缺失，而不是把失败页删掉。"
                "删掉会让指标虚高，这是不能做的。", head="不虚高分数：")
    bullet(doc, "预测按页落盘，逐页记录耗时与状态（JSONL 格式）；重跑自动跳过已完成页。", head="可复跑：")
    bullet(doc, "**自己实现指标容易在归一化环节（表格转 HTML、公式转 LaTeX、文本清洗）产生偏差**，"
                "因此直接调用 OmniDocBench 官方评测代码。", head="用官方评测代码：")

    heading(doc, "步骤五：运行官方评测", 2)
    para(doc, "使用 OmniDocBench 官方 pdf_validation.py，end2end_eval 任务 + quick_match 匹配方式，"
              "指标配置与论文一致。评测集为官方 v1.0（revision f5f559bd…ce8afc），"
              "标注文件校验值已留存。", line=1.5)

    heading(doc, "步骤六：验证论文的核心论点（本步骤最有价值）", 2)
    para(doc, "论文的核心论点是「流水线式方法存在误差传播，检测框不准会导致识别错误」。"
              "这可以直接实验验证：如果该论点成立，那么**把检测框适当放大，应该能救回一部分错误**。", line=1.5)
    para(doc, "为此设计裁剪消融实验：挑选 50 个失败集中的疑似错裁区域，"
              "对**同一块区域**分别用原始框、外扩 2%、外扩 5% 各识别一次，共 150 次，"
              "对比平均区域编辑距离。这把论文的定性论点变成了可量化证据（结果见第八节）。", line=1.5)

    # ============ 四、环境构建（归功AI）
    heading(doc, "四、实验环境构建（由 AI 编程代理完成）", 1)
    note(doc, "说明：本节的依赖解析、环境隔离修复与兼容性排查，主要由 AI 编程代理 Codex 与 DSH 完成；"
              "本人的工作是提出目标、确认诊断结论、验收单页跑通与跑批结果。"
              "这部分属于工程支撑，不构成论文复现的学术贡献，故单列一节。")

    heading(doc, "4.1 环境构建的难点定位", 2)
    para(doc, "MinerU 0.9.3 作为对照基线长期无法启动，连续多轮尝试均卡在模型初始化阶段。"
              "最终定位到的根因**不在模型或配置，而在运行环境本身**：", line=1.5)
    para(doc, "此前使用的「运行环境」并不是独立环境，而是基于 MonkeyOCR 解释器创建的残缺 venv——"
              "它没有自己的标准库，且开启了允许调用外部包的开关，导致 MinerU 实际上运行在 "
              "MonkeyOCR 的 transformers / torch 之上，两套依赖互相冲突。", line=1.5, indent=0.4)
    para(doc, "这个结论解释了一个此前难以理解的现象：无论怎么调整参数与提示词都无效——"
              "因为问题不在被调整的那一层。", line=1.5)

    heading(doc, "4.2 解决方式与工作量", 2)
    para(doc, "AI 代理的处理方式是：用 conda 重建真正隔离的环境（自带解释器与标准库，与另一环境零共享），"
              "再按官方依赖清单逐项固定版本。过程中共排除 10 个阻断问题，其中三个需要在代码层面处理：", line=1.5)
    table(doc, [
        ["#", "问题", "性质", "处置"],
        ["1", "环境隔离被破坏（残缺 venv）", "环境", "conda 重建独立环境"],
        ["2", "依赖被解析到不兼容的新版本", "版本", "逐项固定版本"],
        ["3", "官方指定的某组件版本从未发布", "上游缺陷", "改用最接近的可用版本"],
        ["4", "指定版本在镜像源缺失", "镜像", "切换官方源"],
        ["5", "两个依赖的版本约束互相冲突", "版本", "按上游约束收紧"],
        ["6", "图像增强库新版与 numpy 约束冲突", "版本", "降级到兼容版本"],
        ["7", "某库已停止维护，无兼容当前 torch 的构建", "代码", "将该编译部分设为可选依赖"],
        ["8", "导入期强制加载未安装的组件", "代码", "复用 ABI 匹配的既有构建"],
        ["9", "新版默认启用自定义模型未实现的注意力机制", "代码", "固定回原实现"],
        ["10", "生成接口参数被重复传递", "代码", "在入口处剥离重复参数"],
    ], widths=[0.9, 6.4, 2.6, 7.5], font=8.5)
    para(doc, "**验收结果**：修复后，此前连续失败的那一页一次通过，"
              "产出 Markdown、HTML 表格、LaTeX 公式以及版面/模型/中间结果全套文件；"
              "面向官方评测器的格式转换脚本同步验证通过。", line=1.5, space_before=4)

    heading(doc, "4.3 本人在环境环节的角色", 2)
    bullet(doc, "确定对照基线的必要性（论文的核心对比对象就是 MinerU，不能引用论文数字，必须自己跑）；")
    bullet(doc, "确认诊断方向（要求给出可验证的根因证据，而非「再试一次」）；")
    bullet(doc, "验收标准设定（单页跑通 + 产出物完整 + 格式转换可用）。")

    # ============ 五、MinerU 基线
    heading(doc, "五、对照基线 MinerU 的执行情况（支撑性工作）", 1)
    para(doc, "论文的核心论点之一是与 MinerU 对比，因此必须独立跑出 MinerU 的结果，"
              "而不能引用论文中的数字（那是论文作者在其环境下所得）。", line=1.5)
    table(doc, [
        ["项目", "状态"],
        ["环境修复", "完成（见第四节）"],
        ["单页冒烟验证", "通过"],
        ["120 页正式跑批", f"完成 {MINERU_DONE}/{TOTAL} 页，零失败"],
        ["剩余页面", f"{TOTAL - MINERU_DONE} 页未处理：算力不足、实例中断"],
        ["官方评测", "仅有中间态结果（21 页），不能作为结论"],
    ], widths=[4.6, 12.8], font=9)
    note(doc, "需要说明的是：中断发生在 81 页完成之后，且这 81 页**零失败**，说明推理流程本身是通的；"
              "中断原因是算力与实例可用性，不是方法或代码问题。"
              "由于 MinerU 的中途产物随实例丢失，本地无法补算，评测亦无法完成。"
              "因此本汇报不对 MinerU 作任何对比结论。")

    # ============ 六、结果
    heading(doc, "六、复现结果（MonkeyOCR 原版 3B）", 1)
    heading(doc, "6.1 总体指标", 2)
    para(doc, "评测范围：OmniDocBench v1.0 的 120 页分层子集，118 页取得有效评分"
              "（8 页因上游检测为空，按官方口径计为缺失）。", line=1.5)
    table(doc, [
        ["指标", "结果", "含义"],
        ["文本块 Edit_dist ↓", f"{m['text_block_edit_dist'][0]:.4f}", "识别文本与标准答案的差异，越小越准"],
        ["公式 Edit_dist ↓", f"{m['display_formula_edit_dist'][0]:.4f}", "公式识别错误率，相对弱项"],
        ["表格 TEDS ↑", f"{m['table_TEDS'][0]:.4f}", "表格还原相似度，约八成"],
        ["表格 TEDS（仅结构）↑", f"{m['table_TEDS_structure_only'][0]:.4f}", "表格行列骨架的准确度"],
        ["表格 Edit_dist ↓", f"{m['table_edit_dist'][0]:.4f}", "表格内容层面的编辑距离"],
        ["阅读顺序 Edit_dist ↓", f"{m['reading_order_edit_dist'][0]:.4f}", "阅读顺序的正确程度"],
    ], widths=[4.4, 3.0, 10.0], font=9)
    para(doc, f"跑批实测：{len(log)} 页，成功 {len(ok)}，异常 {len(err)}，"
              f"中位耗时 {med:.1f} 秒/页（LMDeploy 后端，单张 4090）。", line=1.5, space_before=4)

    heading(doc, "6.2 与论文的关系", 2)
    para(doc, "论文在**全量 981 页**上评测，且**分英文/中文两组**报告；"
              "本实验是 **120 页子集、中英合并**口径。因此**数值不可直接对比**，"
              "可比的是趋势与相对关系：文本块最强、表格约八成、公式相对弱——与论文的结论方向一致。", line=1.5)

    # ============ 七、验证论文论点
    heading(doc, "七、对论文核心论点的实验验证", 1)
    para(doc, "论文的立论基础是「流水线式方法存在误差传播「。本实验用裁剪消融直接检验这一论点。", line=1.5)
    table(doc, [
        ["档位", "平均区域编辑距离", "改善", "持平", "退化"],
        ["原始框", f"{am['original']:.4f}", "—", "—", "—"],
        ["外扩 2%", f"{am['expand_2pct']:.4f}", t2["improved"], t2["unchanged"], t2["degraded"]],
        ["外扩 5%", f"{am['expand_5pct']:.4f}", t5["improved"], t5["unchanged"], t5["degraded"]],
    ], widths=[3.2, 4.6, 3.0, 3.0, 3.2], font=9.5)
    para(doc, f"**结论**：外扩 5% 使平均区域编辑距离由 {am['original']:.4f} 降至 {am['expand_5pct']:.4f}"
              f"（相对改善 {imp * 100:.1f}%），50 例中 {t5['improved']} 例改善、{t5['degraded']} 例退化。"
              "这说明**相当一部分错误确实来自裁剪过紧**（切边、切到相邻栏），而不是识别模型不会认——"
              "论文关于误差传播的论点成立，且本实验给出了量化证据。", line=1.5)
    para(doc, "同时，退化案例说明扩框并非普适收益（可能框到了相邻内容），"
              "因此实践上应按版式自适应，而不是无脑放大。", line=1.5)

    # ============ 八、新发现
    heading(doc, "八、复现过程中的新发现（论文未提及）", 1)
    para(doc, "排查失败页时发现一个非常整齐的现象：", line=1.5)
    note(doc, f"MonkeyOCR 的 {len(err)} 个失败页 **100% 集中在笔记（note）类单栏页面**，"
              f"错误类型统一为 IndexError——不是「认错了字」，而是**整页没有任何输出**。", color=WARN)
    para(doc, "继续排查，原因是：SRR 的第一阶段（结构检测）如果**没有检测到任何有效区域**，"
              "识别阶段就会收到一个空列表并直接报错退出，导致整页无输出。而笔记类页面恰好稀疏、留白多，"
              "容易触发这种情况。", line=1.5)
    para(doc, "**量化其影响**（文本块编辑距离的敏感性分析）：", line=1.5, space_before=4)
    table(doc, [
        ["统计口径", "文本块 Edit_dist", "覆盖页数"],
        ["官方提交口径（失败页计缺失）", "0.2022", "118 页"],
        ["剔除整页无产出的页面", "0.1442", "差值 +0.058"],
    ], widths=[6.6, 5.0, 5.8], font=9.5)
    para(doc, "**这个发现的意义**：整页失败单独贡献了约 **0.058** 的差距，"
              "**大于任何「识别质量」层面的差异**；而它的修复成本极低——"
              "只需在检测结果为空时降级为整页识别，而不是报错退出。", line=1.5)
    para(doc, "值得注意的是，这与论文表 3 中的一个现象呼应：MinerU 在笔记类上的编辑距离高达 0.984"
              "（几乎全错）。也就是说，**即使换用论文提出的改进范式，第一阶段（检测）依然会失效**，"
              "只是失效形式从「误差传播」变成了「整页丢失」。这一点论文没有讨论。", line=1.5)

    # ============ 九、偏差声明
    heading(doc, "九、需要声明的偏差（诚信说明）", 1)
    table(doc, [
        ["#", "偏差", "理由", "影响"],
        ["1", "评测子集为 120 页，非论文全量 981 页", "算力与计费限制", "数值不可与论文直接对比，趋势可比"],
        ["2", "指标为中英合并口径，论文分 EN/ZH 报告", "子集规模不足以再分组", "同上"],
        ["3", "未启用 CDM 公式指标", "依赖未安装", "公式仅以 Edit_dist 比较"],
        ["4", "MinerU 用 torch 2.5.1，官方要求 ≤2.3.1", "匹配容器 CUDA 环境，并使两基线共享同一 torch",
         "客观声明；严格复刻需回退版本"],
        ["5", "存在 3 处代码级兼容性补丁", "消除依赖不兼容（第四节）", "不改变推理算法，改动前后文件均留存"],
        ["6", "MinerU 评测不完整", "算力不足、实例中断", "已在全文标注，未用于任何结论"],
        ["7", "环境构建主要由 AI 编程代理完成", "如实说明分工", "属工程支撑，不计入论文复现贡献"],
    ], widths=[0.9, 4.6, 4.6, 7.3], font=8.5)

    # ============ 十、下一步
    heading(doc, "十、下一步计划", 1)
    bullet(doc, "补齐 MinerU 剩余 39 页推理与全量评测（约 2 小时），完成论文所声称的对比验证。", head="优先级 1：")
    bullet(doc, "把「检测为空导致整页丢失」的发现做成改进：为检测环节增加兜底逻辑。"
                "按敏感性分析，该改动可使文本块指标由 0.2022 改善至约 0.1442。", head="优先级 2：")
    bullet(doc, "裁剪策略由固定比例改为按版式自适应（当前外扩 5% 有 7 例退化）。", head="优先级 3：")
    bullet(doc, "如需要 CDM 公式指标，安装依赖后重算。", head="可选：")

    # ============ 附录 A 邮件
    doc.add_page_break()
    heading(doc, "附录 A：可直接发送的邮件正文", 1)
    para(doc, "（以下内容可直接复制进邮件，附件建议附本文件）", color=MUTED, size=9.5, space_after=10)
    for text, bold in [
        ("尊敬的老师：", True),
        ("您好。附件是本阶段 MonkeyOCR 论文复现的汇报，现将要点简述如下。", False),
        ("一、工作分工说明", True),
        ("论文复现的核心工作由我主导完成；实验环境构建（依赖解析、隔离修复、兼容性排查）"
         "主要由 AI 编程代理 Codex 与 DSH 完成，我负责提出目标、确认诊断结论与验收结果。"
         "这部分属工程支撑，不构成论文复现的学术贡献，特此说明。", False),
        ("二、复现的核心工作", True),
        ("我按六步推进：读懂论文方法并转成可执行规格；固定复现对象（代码提交 b5e94d3a、原版 3B 权重、"
         "LMDeploy 后端），避免版本漂移；设计 120 页确定性分层评测子集（覆盖 9 类文档、3 种语言、"
         "5 类版式）；实现统一的「单页 PDF→单页 Markdown"推理流程；调用 OmniDocBench 官方评测代码；"
         "最后用裁剪消融实验验证论文的核心论点。", False),
        ("三、主要结果", True),
        ("在 OmniDocBench v1.0 的 120 页分层子集上，118 页取得有效评分：文本块编辑距离 0.2022、"
         "表格 TEDS 0.8081、表格仅结构 TEDS 0.8696、阅读顺序编辑距离 0.2363、公式编辑距离 0.4136。"
         "跑批 120 页、成功 112 页，中位耗时约 4.7 秒/页（单张 4090）。"
         "需要说明的是，论文为全量 981 页且分中英文报告，本实验为 120 页子集、中英合并口径，"
         "因此数值不可直接对比，但趋势一致。", False),
        ("四、对论文论点的验证与新发现", True),
        ("论文的核心论点是流水线式方法存在误差传播。我设计裁剪消融实验验证：对 50 个疑似错裁区域"
         "按原始框、外扩 2%、外扩 5% 各识别一次（共 150 次），平均区域编辑距离由 0.6064 降至 0.5741，"
         "50 例中 33 例改善——说明部分错误确实来自裁剪过紧，论文论点成立。", False),
        ("此外有一个论文未提及的发现：MonkeyOCR 的 8 个失败页全部集中在笔记类单栏页面，"
         "错误统一为上游检测为空导致整页无输出。剔除这些页面后，文本块编辑距离由 0.2022 降至 0.1442，"
         "差值约 0.058，大于任何识别质量层面的差异，而修复成本很低。"
         "这与论文表 3 中 MinerU 在笔记类上 0.984 的异常值相呼应，说明即使采用论文提出的范式，"
         "第一阶段的检测环节仍会失效。", False),
        ("五、未完成部分", True),
        ("作为对照基线的 MinerU，环境修复与单页验证已完成，120 页跑批完成 81 页（零失败）后"
         "因算力不足、实例中断而停止，中途产物随实例丢失，因此其评测不完整，"
         "本汇报未据此对 MinerU 作任何对比结论。补齐预计约 2 小时。", False),
        ("六、下一步", True),
        ("计划优先补齐 MinerU 的全量评测，完成论文所声称的对比验证；"
         "其次针对检测环节补充兜底逻辑，改进裁剪策略。", False),
        ("如需任何原始数据（逐页日志、官方评分文件、脚本与依赖版本清单），我可以随时提供。顺颂时祺。", False),
    ]:
        para(doc, text, size=10.5, bold=bold, line=1.5, space_after=5 if not bold else 8)

    # ============ 附录 B 产物
    doc.add_page_break()
    heading(doc, "附录 B：产物与可核查性", 1)
    table(doc, [
        ["类别", "内容"],
        ["论文翻译", "MonkeyOCR 论文全文中文翻译（含缩写表、核心数字速查、阅读注意事项）"],
        ["正式报告", "技术报告（含环境修复全过程、结果、失败归因、偏差声明）"],
        ["汇报材料", "幻灯片（9 页）与逐页讲解稿"],
        ["实验数据", "120 页预测结果、逐页运行日志（耗时/状态）、OmniDocBench 官方评分文件（总体+逐页）"],
        ["消融实验", "50 例 × 3 档的样本图与模型响应，共 150 份"],
        ["脚本", "环境重建、单页验证、跑批（含断点续跑与原子锁）、格式适配、双基线评测、"
                 "对比表与报告生成"],
        ["版本清单", "三个环境的完整依赖版本（精确到补丁号）"],
    ], widths=[3.4, 14.0], font=9)
    para(doc, "以上材料均已整理归档，并同步至代码托管仓库，便于核查与后续接手。", line=1.5, space_before=6)

    out = DEL / "给导师的汇报_MonkeyOCR论文复现_v2.docx"
    doc.save(str(out))
    return out


def main() -> None:
    p = build()
    print(f"written: {p.name}  ({p.stat().st_size} bytes)")
    d = Document(str(p))
    print("段落:", len(d.paragraphs), " 表格:", len(d.tables))
    print("章节:")
    for para_ in d.paragraphs:
        if para_.runs and para_.runs[0].font.size and para_.runs[0].font.size.pt >= 13:
            print("   ", para_.text[:60])


if __name__ == "__main__":
    main()
