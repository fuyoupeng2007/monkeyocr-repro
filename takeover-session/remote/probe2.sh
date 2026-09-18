#!/bin/bash
# probe env leakage + last lines of struct log
echo "===== PYTHONPATH / env ====="
env | grep -Ei 'python|conda|mineru|magic' | sort
echo
echo "===== ~/.bashrc relevant ====="
grep -nEi 'PYTHONPATH|conda|mineru|alias' /root/.bashrc | head -30
echo
echo "===== mineru093_runtime python path check ====="
/root/autodl-tmp/conda_envs/mineru093_runtime/bin/python -c "import sys,click,transformers;print('exe',sys.executable);print('click',click.__file__);print('transformers',transformers.__version__,transformers.__file__)" 2>&1 | tail -20
echo
echo "===== which conda envs exist ====="
ls -1 /root/autodl-tmp/conda_envs/
echo
echo "===== outputs/mineru_smoke_struct tree ====="
find /root/autodl-tmp/monkeyocr-repro/outputs/mineru_smoke_struct -type f -printf '%10s %p\n'
echo
echo "===== struct log first 40 ====="
head -40 /root/autodl-tmp/monkeyocr-repro/outputs/mineru_smoke_struct.log
