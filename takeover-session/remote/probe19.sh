#!/bin/bash
ENV=/root/autodl-tmp/conda_envs/mineru093_env
echo "=== doclayout_yolo wheel contents ==="
find $ENV/lib/python3.10/site-packages/doclayout_yolo -maxdepth 1 -printf '%y %f\n' | head -20
echo
echo "=== its __init__ head ==="
head -25 $ENV/lib/python3.10/site-packages/doclayout_yolo/__init__.py 2>/dev/null
echo
echo "=== does magic_pdf use doclayout_yolo or detectron2? ==="
grep -rn "doclayout_yolo\|detectron2\|DocLayoutYOLO\|LayoutLMv3" $ENV/lib/python3.10/site-packages/magic_pdf/model/*.py | head -20
echo
echo "=== which models exist in the downloaded PDF-Extract-Kit ==="
ls /root/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/ 2>/dev/null
ls /root/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/Layout/ 2>/dev/null
find /root/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/Layout -maxdepth 2 | head -20
echo
echo "=== 破旧 venv 里 detectron2 / doclayout 装了什么（旧环境证据） ==="
ls -d /root/autodl-tmp/conda_envs/mineru093_runtime_broken/lib/python3.10/site-packages/detectron2* \
      /root/autodl-tmp/conda_envs/monkeyocr/lib/python3.10/site-packages/detectron2* \
      /root/autodl-tmp/conda_envs/monkeyocr/lib/python3.10/site-packages/doclayout_yolo* 2>&1
