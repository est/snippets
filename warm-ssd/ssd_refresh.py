#!/usr/bin/env python3
"""
ssd_refresh.py — read and rewrite all files in a folder (to refresh cold SSD data)

Usage:
    python ssd_refresh.py "C:\\path\\to\\folder" [--chunk 32] [--dry-run]
"""

import os, sys, time, pathlib
import argparse

def refresh_file(path, chunk_size=32 * 1024 * 1024, dry_run=False):
    try:
        size = os.path.getsize(path)
        if size == 0:
            return "empty"

        with open(path, "r+b") as f:  # read/write binary mode
            offset = 0
            t0 = time.monotonic()
            while offset < size:
                t1 = time.monotonic()
                buf = f.read(min(chunk_size, size - offset))
                cbuf = len(buf)
                t2 = time.monotonic()
                if t2 - t1 < 0.2:  # too fast
                    offset += cbuf
                    continue
                else:
                    print(f'  {cbuf/1024:.2f}KB in {t2-t1:.2f}s {offset/1024/1024:.2f}MiB/{size/1024/1024:.2f}MiB')
                if not buf:
                    break
                if not dry_run:
                    f.seek(-cbuf, os.SEEK_CUR)
                    offset += f.write(buf)
                else:
                    offset += cbuf
            f.flush()
            os.fsync(f.fileno())  # posix:O_DIRECT win:FILE_FLAG_NO_BUFFERING
            dur = time.monotonic() - t0
            mb = size / 1024 / 1024
            return f"{mb:.1f} MiB, {dur:.2f}s, {(mb/dur):.1f} MB/s"

    except PermissionError:
        return "permission denied"
    except OSError as e:
        return f"error: {e.strerror}"
    except Exception as e:
        return f"error: {e}"

def main():
    p = argparse.ArgumentParser(description="Refresh all files in a directory (rewrite to SSD).")
    p.add_argument("path", type=pathlib.Path, help="Directory path to scan")
    p.add_argument("--chunk", type=int, default=32, help="Chunk size in MiB (default 32)")
    p.add_argument("--dry-run", action="store_true", help="Only read, do not rewrite")
    args = p.parse_args()

    chunk_size = args.chunk * 1024 * 1024

    if not args.path.exists():
        print(f"❌ {args.path} does not exist")
        sys.exit(1)
    if args.path.is_file():
        targets = [args.path]
    else:
        targets = [p for p in args.path.rglob("*") if p.is_file()]
    
    print(f"📂 Scanning: {args.path}")
    print(f"Chunk size: {args.chunk} MiB  |  Dry run: {args.dry_run}")
    print("-" * 60)

    total_files = 0
    total_bytes = 0
    for f in targets:
        total_files += 1
        print(f"[{total_files}] Refreshing {f} ... ", end="", flush=True)
        info = refresh_file(f, chunk_size, args.dry_run)
        print(info)
        if "MiB" in info:
            try:
                total_bytes += os.path.getsize(f)
            except OSError:
                pass

    print("-" * 60)
    print(f"✅ Done. {total_files} files processed, {total_bytes/1024/1024:.1f} MiB total.")

if __name__ == "__main__":
    main()
