#!/bin/bash
# measure torch wheel download progress twice to estimate rate
D=$(ls -d /tmp/pip-* 2>/dev/null | head -20)
echo "=== pip temp dirs ==="
du -sh $D 2>/dev/null | tail -5
echo "=== largest tmp files ==="
find /tmp -maxdepth 2 -type f -size +10M -printf '%s %p\n' 2>/dev/null | sort -rn | head -5
sleep 20
echo "=== after 20s ==="
find /tmp -maxdepth 2 -type f -size +10M -printf '%s %p\n' 2>/dev/null | sort -rn | head -5
echo "=== cache ==="
du -sh /root/.cache/pip 2>/dev/null
