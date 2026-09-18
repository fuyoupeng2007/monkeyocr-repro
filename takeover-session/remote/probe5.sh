#!/bin/bash
R=/root/autodl-tmp/conda_envs/mineru093_runtime
M=/root/autodl-tmp/conda_envs/monkeyocr
echo "===== pyvenv.cfg ====="; cat $R/pyvenv.cfg
echo
echo "===== packages present in runtime venv ====="
ls -1 $R/lib/python3.10/site-packages/ | sed 's/\(.*\)/\1/' | grep -v '\.dist-info$' | grep -v '\.egg-info$' | grep -v '__pycache__' | sort | tr '\n' ' '
echo; echo
echo "===== packages present ONLY in monkeyocr (i.e. leaking in) ====="
comm -13 <(ls -1 $R/lib/python3.10/site-packages/ | tr 'A-Z' 'a-z' | sort -u) <(ls -1 $M/lib/python3.10/site-packages/ | tr 'A-Z' 'a-z' | sort -u) | grep -v '\.dist-info$' | grep -v '\.egg-info$' | tr '\n' ' '
echo; echo
echo "===== conda pkgs cache ====="
du -sh /root/miniconda3/pkgs 2>/dev/null; ls /root/miniconda3/pkgs 2>/dev/null | grep -iE '^python-3.10|^pip-|^setuptools|^wheel' | head
echo "--- conda envs registered:"; /root/miniconda3/bin/conda env list 2>&1
echo
echo "===== pip cache ====="
du -sh /root/.cache/pip 2>/dev/null
echo
echo "===== mineru093 env (23M) content ====="
find /root/autodl-tmp/conda_envs/mineru093 -maxdepth 3 | head -30
echo
echo "===== install logs: how runtime was built (head) ====="
head -40 /root/autodl-tmp/monkeyocr-repro/outputs/mineru093_install.log
echo "..."
grep -nE 'python -m venv|conda create|Virtualenv|virtualenv|--system-site-packages|site-packages' /root/autodl-tmp/monkeyocr-repro/outputs/mineru093_install.log | head -20
echo
echo "===== full_deps install log ====="
cat /root/autodl-tmp/monkeyocr-repro/outputs/mineru093_full_deps_install.log
