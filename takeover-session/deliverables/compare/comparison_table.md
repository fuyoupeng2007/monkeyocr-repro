## 4.1 Overall metrics (OmniDocBench v1.0, same 120-page subset)

| metric | MonkeyOCR-3B | MinerU-0.9.3 | change (MinerU vs MonkeyOCR) |
|---|---|---|---|
| text_block_edit_dist | 0.2022 | 0.2054 | -1.6% |
| display_formula_edit_dist | 0.4136 | 0.3853 | +6.8% |
| table_TEDS | 0.8081 | 0.6020 | -25.5% |
| table_TEDS_structure_only | 0.8696 | 0.6633 | -23.7% |
| table_edit_dist | 0.2041 | 0.2797 | -37.0% |
| reading_order_edit_dist | 0.2363 | 0.2424 | -2.6% |

### text by language (Edit_dist)

| group | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| text_language: text_en_ch_mixed | 0.8266 | 1.0000 |
| text_language: text_english | 0.1179 | 0.2046 |
| text_language: text_simplified_chinese | 0.1822 | 0.1227 |

### text by background (Edit_dist)

| group | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| text_background: multi_colored | 0.3884 | 0.2596 |
| text_background: single_colored | 0.0176 | 0.0704 |
| text_background: white | 0.1873 | 0.1817 |

### text by rotate (Edit_dist)

| group | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| text_rotate: horizontal | 0.3295 | 0.5000 |
| text_rotate: normal | 0.1981 | 0.1836 |
| text_rotate: rotate270 | 0.2758 | - |

### table by language (TEDS)

| group | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| language: table_en | 0.7418 | 0.5865 |
| language: table_en_ch_mixed | 0.9220 | - |
| language: table_simplified_chinese | 0.8424 | 0.6175 |

### table by line style (TEDS)

| group | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| line: fewer_line | 0.8535 | 0.5495 |
| line: full_line | 0.7860 | 0.6128 |
| line: less_line | 0.7653 | 0.6481 |
| line: wireless_line | 0.8342 | - |

### table with span (TEDS)

| group | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| with_span: False | 0.7895 | 0.5999 |
| with_span: True | 0.8743 | 0.6148 |

### formula by type (Edit_dist)

| group | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| formula_type: handwriting | 1.0000 | - |
| formula_type: print | 0.4295 | 0.4739 |

### by data source: text_block

| source | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| PPT2PDF | 0.1277 | 0.5158 |
| academic_literature | 0.0061 | 0.0255 |
| book | 0.1642 | 0.2387 |
| colorful_textbook | 0.1025 | 0.2268 |
| exam_paper | 0.1166 | 0.1161 |
| magazine | 0.2177 | 0.0036 |
| newspaper | 0.0593 | 0.0465 |
| note | 0.9968 | 0.9968 |
| research_report | 0.0365 | 0.2342 |

### by data source: display_formula

| source | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| PPT2PDF | 0.4654 | 0.8913 |
| academic_literature | 0.2514 | 0.1542 |
| book | 0.5138 | 0.4642 |
| colorful_textbook | 0.5464 | 0.2628 |
| exam_paper | 0.3361 | 0.3844 |
| note | 1.0000 | - |

### by data source: reading_order

| source | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| PPT2PDF | 0.1206 | 0.3333 |
| academic_literature | 0.1932 | 0.3000 |
| book | 0.1786 | 0.2920 |
| colorful_textbook | 0.1184 | 0.1250 |
| exam_paper | 0.1631 | 0.1294 |
| magazine | 0.1555 | 0.2500 |
| newspaper | 0.1616 | 0.1224 |
| note | 0.9779 | 0.9600 |
| research_report | 0.0490 | 0.0000 |

### by data source: table

| source | MonkeyOCR-3B | MinerU-0.9.3 |
|---|---|---|
| PPT2PDF | 0.9314 | 0.5769 |
| academic_literature | 0.7680 | 0.5538 |
| book | 0.9436 | 0.9016 |
| colorful_textbook | 0.9131 | 0.9812 |
| exam_paper | 0.8300 | 0.4091 |
| magazine | 0.7306 | 0.7185 |
| newspaper | 0.8191 | 0.7904 |
| note | 0.0000 | 0.0000 |
| research_report | 0.8690 | 0.4053 |

### worst regressions vs MonkeyOCR (text_block edit distance)

| page | MonkeyOCR-3B | MinerU-0.9.3 | delta |
|---|---|---|---|
| eastmoney_62b4149b1612ce28d20f26cd5c5b2e18f80b26fca6e4452e090376a2fe72eae3.pdf_0.jpg | 0.3235 | 0.2342 | -0.0893 |
| newspaper_01f020903d7bc4b3fc69f500f41eb77e_1.jpg | 0.1458 | 0.0679 | -0.0779 |
| jiaocaineedrop_jiaocai_needrop_en_999.jpg | 0.1498 | 0.1359 | -0.0139 |
| docstructbench_llm-raw-scihub-o.O-ceat.200600410.pdf_5.jpg | 0.0000 | 0.0000 | +0.0000 |
| notes_f7f010b78016aeebd76e56d9283eb67f_49.jpg | 0.9968 | 0.9968 | +0.0000 |
| jiaocaineedrop_chap02.pdf_16.jpg | 0.0033 | 0.0036 | +0.0003 |
| docstructbench_llm-raw-scihub-o.O-s00128-008-9367-z.pdf_4.jpg | 0.0045 | 0.0079 | +0.0035 |
| jiaocaineedrop_jiaocai_needrop_en_2211.jpg | 0.0330 | 0.0373 | +0.0043 |
| jiaocai_71434495.pdf_0.jpg | 0.0246 | 0.0291 | +0.0045 |
| yanbaopptmerge_yanbaoPPT_2460.jpg | 0.8519 | 0.8686 | +0.0168 |
