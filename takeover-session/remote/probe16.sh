#!/bin/bash
echo "=== all /tmp files > 5M sorted by mtime (newest first) ==="
find /tmp -maxdepth 2 -type f -size +5M -printf '%T@ %TH:%TM:%TS %10s %p\n' 2>/dev/null | sort -rn | head -8
echo
echo "=== twice, 20s apart, to see growth ==="
find /tmp -maxdepth 2 -type f -size +100M -printf '%s %p\n' 2>/dev/null | sort -rn | head -4
sleep 20
echo "--- after 20s ---"
find /tmp -maxdepth 2 -type f -size +100M -printf '%s %p\n' 2>/dev/null | sort -rn | head -4
echo
echo "=== open sockets of pip (download activity) ==="
PID=$(pgrep -f 'pip install --index-url' | head -1)
echo "pip pid=$PID"
if [ -n "$PID" ]; then
  ls -l /proc/$PID/fd 2>/dev/null | grep -c . 
  grep -E 'State|Bytes' /proc/$PID/net/tcp 2>/dev/null | head -2
  timeout 3 strace -f -p $PID -e trace=network -c 2>&1 | tail -5
fi
