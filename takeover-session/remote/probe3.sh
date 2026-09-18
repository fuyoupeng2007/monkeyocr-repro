#!/bin/bash
echo "===== .pth files in mineru093_runtime site-packages ====="
ls -la /root/autodl-tmp/conda_envs/mineru093_runtime/lib/python3.10/site-packages/*.pth 2>/dev/null
for f in /root/autodl-tmp/conda_envs/mineru093_runtime/lib/python3.10/site-packages/*.pth; do
  echo "--- $f"; cat "$f"
done
echo
echo "===== .pth files in monkeyocr site-packages ====="
for f in /root/autodl-tmp/conda_envs/monkeyocr/lib/python3.10/site-packages/*.pth; do
  echo "--- $f"; cat "$f"
done
echo
echo "===== sys.path of mineru093_runtime python ====="
/root/autodl-tmp/conda_envs/mineru093_runtime/bin/python -c "import sys;[print(p) for p in sys.path]" 2>&1 | grep -v FutureWarning | grep -v pynvml
echo
echo "===== conda env var files ====="
for e in mineru093_runtime mineru093 monkeyocr omnidocbench; do
  echo "--- $e/etc/conda/activate.d"; ls /root/autodl-tmp/conda_envs/$e/etc/conda/activate.d/ 2>/dev/null && grep -r "" /root/autodl-tmp/conda_envs/$e/etc/conda/activate.d/ 2>/dev/null | head -10
  echo "--- $e/conda-meta/state"; head -c 400 /root/autodl-tmp/conda_envs/$e/conda-meta/state 2>/dev/null; echo
done
echo
echo "===== magic-pdf entrypoint ====="
head -12 /root/autodl-tmp/conda_envs/mineru093_runtime/bin/magic-pdf
echo
echo "===== does runtime env have its own transformers/click? ====="
ls -d /root/autodl-tmp/conda_envs/mineru093_runtime/lib/python3.10/site-packages/transformers* /root/autodl-tmp/conda_envs/mineru093_runtime/lib/python3.10/site-packages/click* 2>&1
echo
echo "===== pip list (runtime) key pkgs ====="
/root/autodl-tmp/conda_envs/mineru093_runtime/bin/pip list 2>/dev/null | grep -Ei 'transformers|click|torch|magic|struct|modelscope|paddle|accelerate' 
echo
echo "===== pip list (monkeyocr) key pkgs ====="
/root/autodl-tmp/conda_envs/monkeyocr/bin/pip list 2>/dev/null | grep -Ei 'transformers|click|torch|magic|struct|modelscope|paddle|accelerate'
