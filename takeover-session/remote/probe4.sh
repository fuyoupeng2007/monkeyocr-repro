#!/bin/bash
echo "===== which python under runtime bin ====="
ls -la /root/autodl-tmp/conda_envs/mineru093_runtime/bin/python*
echo
echo "===== prefix / base_prefix / paths ====="
/root/autodl-tmp/conda_envs/mineru093_runtime/bin/python - <<'PY' 2>&1 | grep -v FutureWarning | grep -v pynvml
import sys, os
print("exe        =", sys.executable)
print("prefix     =", sys.prefix)
print("base_prefix=", sys.base_prefix)
print("exec_prefix=", sys.exec_prefix)
print("PYTHONHOME =", os.environ.get("PYTHONHOME"))
print("PYTHONPATH =", os.environ.get("PYTHONPATH"))
print("ENV VARS   =", {k:v for k,v in os.environ.items() if k.startswith("PYTHON") or k.startswith("CONDA")})
try:
    import magic_pdf, click, transformers
    print("magic_pdf  =", magic_pdf.__file__)
    print("click      =", click.__file__)
    print("transformers=", transformers.__file__)
except Exception as e:
    print("import err", e)
PY
echo
echo "===== runtime env dirs ====="
ls -la /root/autodl-tmp/conda_envs/mineru093_runtime/
echo "--- lib:"; ls /root/autodl-tmp/conda_envs/mineru093_runtime/lib/ 2>&1
echo "--- lib/python3.10 first 20:"; ls /root/autodl-tmp/conda_envs/mineru093_runtime/lib/python3.10/ 2>&1 | head -20
echo "--- bin count:"; ls /root/autodl-tmp/conda_envs/mineru093_runtime/bin/ | wc -l
echo "--- stdlib os.py present?"; ls -la /root/autodl-tmp/conda_envs/mineru093_runtime/lib/python3.10/os.py 2>&1
echo
echo "===== monkeyocr env dirs (for comparison) ====="
ls -la /root/autodl-tmp/conda_envs/monkeyocr/ | head -25
echo
echo "===== pip show location from runtime ====="
/root/autodl-tmp/conda_envs/mineru093_runtime/bin/pip -V
echo
echo "===== du of each env ====="
du -sh /root/autodl-tmp/conda_envs/* 2>/dev/null
echo
echo "===== disk ====="
df -h /root/autodl-tmp /root
