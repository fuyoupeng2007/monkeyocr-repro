#!/bin/bash
# Generic detached launcher: run a remote script with setsid, log to outputs/.
# usage: launch.sh <script-path-relative-to-project> <logfile-name>
cd /root/autodl-tmp/monkeyocr-repro || exit 1
mkdir -p outputs
SCRIPT="$1"
LOG="outputs/$2"
: > "$LOG"
setsid nohup bash "$SCRIPT" > "$LOG" 2>&1 < /dev/null &
echo "launched script=$SCRIPT pid=$! log=$LOG"
