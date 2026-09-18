#!/bin/bash
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
echo "=== why did pytz/pyparsing/protobuf fail? direct attempt ==="
$PY -m pip install --no-deps pytz 2>&1 | tail -6
echo "---"
$PY -m pip install --no-deps pyparsing 2>&1 | tail -6
echo "---"
$PY -m pip install --no-deps protobuf 2>&1 | tail -6
echo
echo "=== log head of round 2 ==="
head -30 /root/autodl-tmp/monkeyocr-repro/outputs/env_deps_loop2.log
