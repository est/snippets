#!/usr/bin/env python3
import os
import sys
import zipfile
import argparse
from pathlib import Path

def extract_zip(src_zip, dest_dir, overwrite=False, password=None):
    src_zip = Path(src_zip)
    dest_dir = Path(dest_dir)

    if not src_zip.exists():
        print(f"❌ Source ZIP not found: {src_zip}")
        sys.exit(1)

    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Opening ZIP: {src_zip}")
    with zipfile.ZipFile(src_zip, 'r') as zf:
        if password:
            zf.setpassword(password.encode())

        members = zf.infolist()
        total = len(members)

        for i, member in enumerate(members, 1):
            target_path = dest_dir / member.filename

            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue

            if target_path.exists() and not overwrite:
                print(f"[{i}/{total}] ✅ Skipping existing: {member.filename}")
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[{i}/{total}] Extracting: {member.filename}")

            try:
                with zf.open(member) as src, open(target_path, 'wb') as dst:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        dst.write(chunk)
            except RuntimeError as e:
                print(f"❌ Failed to extract {member.filename}: {e}")
                continue

    print("✅ Extraction complete!")

def main():
    parser = argparse.ArgumentParser(
        description="Extract large .zip from SMB to SMB (macOS friendly, supports password)"
    )
    parser.add_argument("src_zip", help="Path to source .zip file")
    parser.add_argument("dest_dir", help="Destination directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("-p", "--password", help="Password for encrypted ZIP (ZipCrypto only)")

    args = parser.parse_args()
    extract_zip(args.src_zip, args.dest_dir, args.overwrite, args.password)

if __name__ == "__main__":
    main()
