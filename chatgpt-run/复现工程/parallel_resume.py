from __future__ import annotations

import argparse
import concurrent.futures
import os
import time
import urllib.request
import zipfile
from pathlib import Path


def remote_size(url: str) -> int:
    request = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_range = response.headers.get("Content-Range", "")
        if response.status != 206 or "/" not in content_range:
            raise RuntimeError(f"服务器不支持分段下载：status={response.status}, range={content_range}")
        return int(content_range.rsplit("/", 1)[1])


def download_range(url: str, destination: Path, start: int, end: int) -> tuple[int, int]:
    position = start
    attempts = 0
    descriptor = os.open(destination, os.O_WRONLY)
    try:
        while position <= end:
            try:
                request = urllib.request.Request(url, headers={"Range": f"bytes={position}-{end}"})
                with urllib.request.urlopen(request, timeout=120) as response:
                    if response.status != 206:
                        raise RuntimeError(f"range响应异常：{response.status}")
                    while position <= end:
                        block = response.read(min(1024 * 1024, end - position + 1))
                        if not block:
                            break
                        os.pwrite(descriptor, block, position)
                        position += len(block)
                if position <= end:
                    raise RuntimeError("连接提前结束")
            except Exception:
                attempts += 1
                if attempts >= 6:
                    raise
                time.sleep(min(2**attempts, 15))
        return start, end
    finally:
        os.close(descriptor)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    total = remote_size(args.url)
    existing = args.destination.stat().st_size if args.destination.exists() else 0
    if existing > total:
        raise RuntimeError(f"本地文件大于远端文件：{existing}>{total}")
    if existing == total:
        print(f"文件大小已完整：{total} bytes")
    else:
        with args.destination.open("ab") as stream:
            stream.truncate(total)
        remaining = total - existing
        workers = min(args.workers, max(1, remaining))
        chunk = (remaining + workers - 1) // workers
        ranges = []
        for index in range(workers):
            start = existing + index * chunk
            if start >= total:
                break
            ranges.append((start, min(total - 1, start + chunk - 1)))
        print(f"总大小={total}，已保存={existing}，并行分段={len(ranges)}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(ranges)) as pool:
            futures = [pool.submit(download_range, args.url, args.destination, start, end) for start, end in ranges]
            for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                start, end = future.result()
                print(f"完成分段 {completed}/{len(ranges)}：{start}-{end}", flush=True)

    if args.destination.stat().st_size != total:
        raise RuntimeError("下载后文件大小不正确")
    with zipfile.ZipFile(args.destination) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise RuntimeError(f"wheel压缩校验失败：{corrupt}")
    print(f"下载及wheel完整性校验通过：{args.destination}")


if __name__ == "__main__":
    main()

