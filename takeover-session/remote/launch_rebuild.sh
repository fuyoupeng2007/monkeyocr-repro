#!/bin/bash
# Detached launcher, meant to be invoked by its absolute path so that a single
# ssh command line has no cwd/redirect ambiguity.
cd /root/autodl-tmp/monkeyocr-repro || exit 1
mkdir -p outputs
LOG=outputs/env_rebuild_v2_nohup.log
: > "$LOG"
setsid nohup bash scripts/rebuild_mineru_env_v2.sh > "$LOG" 2>&1 < /dev/null &
echo "launched pid=$! log=$LOG"
