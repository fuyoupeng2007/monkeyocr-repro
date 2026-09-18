#!/bin/bash
cd /root/autodl-tmp/monkeyocr-repro/outputs || exit 1
for f in mineru_smoke_final3 mineru_smoke_final4 mineru_smoke_final5; do
  echo "########## $f.log  (last 25) ##########"
  tail -25 "$f.log"
  echo
done
echo "########## mineru_smoke_final6.log (head 70) ##########"
head -70 mineru_smoke_final6.log
