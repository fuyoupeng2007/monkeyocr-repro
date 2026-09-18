"""Verify the pushed repo: file count, no key material, expected top-level layout."""
import json
import subprocess
import sys

REPO = "fuyoupeng2007/monkeyocr-repro"


def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print("gh failed:", r.stderr[:300])
        sys.exit(1)
    return r.stdout


tree = json.loads(gh(["api", f"repos/{REPO}/git/trees/main?recursive=1"]))
blobs = [t for t in tree["tree"] if t.get("type") == "blob"]
print("远端文件数 :", len(blobs))
print("总大小     :", round(sum(t.get("size", 0) for t in blobs) / 1024 / 1024, 2), "MB")
print("被截断     :", tree.get("truncated"))

danger = [
    t["path"] for t in blobs
    if any(k in t["path"].lower() for k in
           ("monkeyocr_autodl", "/ssh/", ".pem", "id_rsa", "id_ed25519", ".key", "known_hosts", "authorized_keys"))
]
print("密钥类文件 :", len(danger), danger[:10] if danger else "(无)")

tops = sorted({t["path"].split("/")[0] for t in blobs})
print("顶层条目   :", tops)

meta = json.loads(gh(["api", f"repos/{REPO}"]))
print("可见性     :", meta["visibility"], "| 默认分支:", meta["default_branch"])
print("仓库地址   :", meta["html_url"])
print("推送时间   :", meta["pushed_at"])
