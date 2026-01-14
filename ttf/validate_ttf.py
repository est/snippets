#!/usr/bin/env python3

import subprocess
import os
import tempfile

def validate_ttf(ttf_path):
    try:
        result = subprocess.run(['ttx', ttf_path], capture_output=True, text=True)
        if result.returncode == 0:
            print("TTF file is valid")
            return True
        else:
            print("TTF file validation failed:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("ttx command not found. Please install fonttools.")
        return False
    except Exception as e:
        print(f"Error validating TTF file: {e}")
        return False

def create_ttf_from_html():
    # 这是对 HTML 中 JavaScript 代码的 Python 重实现
    def u16(v):
        return [(v >> 8) & 255, v & 255]

    def u32(v):
        return [(v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255]

    def checksum(data):
        sum_val = 0
        for i in range(0, len(data), 4):
            byte1 = data[i] if i < len(data) else 0
            byte2 = data[i+1] if i+1 < len(data) else 0
            byte3 = data[i+2] if i+2 < len(data) else 0
            byte4 = data[i+3] if i+3 < len(data) else 0
            sum_val = (sum_val + (byte1 << 24 | byte2 << 16 | byte3 << 8 | byte4)) & 0xffffffff
        return sum_val

    def pad4(arr):
        while len(arr) % 4:
            arr.append(0)

    tables = []

    # glyf: empty glyph with zero dimensions
    glyf = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    pad4(glyf)
    tables.append({"tag": "glyf", "data": glyf, "checksum": 0})

    # loca: glyph offsets
    tables.append({"tag": "loca", "data": [0, 0], "checksum": 0})

    # hmtx: horizontal metrics
    tables.append({"tag": "hmtx", "data": [0, 0, 0, 0], "checksum": 0})

    # maxp: maximum profile
    tables.append({"tag": "maxp", "data": [
        0, 1, 0, 0,  # tableVersion 1.0
        0, 1,  # numGlyphs
        0, 0, 0, 0,  # maxPoints, maxContours
        0, 0, 0, 0,  # maxCompositePoints, maxCompositeContours
        0, 0, 0, 0,  # maxZones, maxTwilightPoints
        0, 0, 0, 0,  # maxStorage, maxFunctionDefs
        0, 0, 0, 0,  # maxInstructionDefs, maxStackElements
        0, 0, 0, 0,  # maxSizeOfInstructions, maxComponentElements
        0, 0         # maxComponentDepth
    ], "checksum": 0})

    # head: font header
    tables.append({"tag": "head", "data": [0, 1, 0, 0, 0, 0, 0, 0, 0x5F, 0x0F, 0x3C, 0xF5, 0, 0, 0x03, 0xE8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0x38, 0xFF, 0x38, 0x04, 0xB0, 0x04, 0xB0, 0, 0, 0, 0xA, 0, 2, 0, 0], "checksum": 0})

    # hhea: horizontal header
    tables.append({"tag": "hhea", "data": [0, 1, 0, 0, 0xFF, 0x38, 0xFF, 0x38, 0, 0, 0x03, 0xE8, 0xFF, 0x38, 0xFF, 0x38, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1], "checksum": 0})

    # cmap: character mapping
    tables.append({"tag": "cmap", "data": [0, 0, 0, 1, 0, 3, 0, 1, 0, 0, 0, 12, 0, 0, 0, 4, 0, 32, 0, 0, 0, 2, 0, 2, 0, 1, 0, 0, 0x26, 0x03, 0x26, 0x03, 0, 0, 0x26, 0x03, 0, 0], "checksum": 0})

    # name: font naming
    tables.append({"tag": "name", "data": [0, 0, 0, 0], "checksum": 0})

    # post: PostScript info
    tables.append({"tag": "post", "data": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "checksum": 0})

    # OS/2 table
    tables.append({"tag": "OS/2", "data": [0, 4, 0, 0, 0x03, 0xE8, 0, 5, 0, 0, 0x03, 0xE8, 0x03, 0xE8, 0, 0, 0x04, 0xB0, 0x04, 0xB0, 0, 0, 0, 0xC8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x04, 0x09, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0x04, 0xB0, 0, 0xC8], "checksum": 0})

    # Ensure all tables are properly padded
    for t in tables:
        pad4(t["data"])

    # Sort tables alphabetically by tag (required by TTF spec)
    sorted_tables = sorted(tables, key=lambda x: x["tag"])

    # Calculate table offsets and lengths
    offset = 12 + len(sorted_tables) * 16
    for t in sorted_tables:
        t["offset"] = offset
        t["length"] = len(t["data"])
        t["checksum"] = checksum(t["data"])
        offset += t["length"]

    # Calculate checkSumAdjustment
    head_table = next(t for t in sorted_tables if t["tag"] == "head")
    total_checksum = sum(t["checksum"] for t in sorted_tables) & 0xffffffff
    check_sum_adjustment = (0xB1B0AFBA - total_checksum) & 0xffffffff
    head_table["data"][4:8] = u32(check_sum_adjustment)
    head_table["checksum"] = checksum(head_table["data"])

    # Build the TTF file
    out = []
    out.extend(u32(0x00010000))

    # Calculate search parameters for table directory
    num_tables = len(sorted_tables)
    power_of_2 = 0
    while (1 << (power_of_2 + 1)) <= num_tables:
        power_of_2 += 1
    search_range = (1 << power_of_2) * 16
    entry_selector = power_of_2
    range_shift = num_tables * 16 - search_range

    out.extend(u16(num_tables))
    out.extend(u16(search_range))
    out.extend(u16(entry_selector))
    out.extend(u16(range_shift))

    # Write table records
    for t in sorted_tables:
        tag_bytes = []
        for i in range(4):
            tag_bytes.append(ord(t["tag"][i]) if i < len(t["tag"]) else 0)
        out.extend(tag_bytes)
        out.extend(u32(t["checksum"]))
        out.extend(u32(t["offset"]))
        out.extend(u32(t["length"]))

    # Write table data
    for t in sorted_tables:
        out.extend(t["data"])

    # Write to temporary file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test_font.ttf")
    with open(temp_path, "wb") as f:
        f.write(bytearray(out))
    
    return temp_path

def main():
    ttf_path = create_ttf_from_html()
    
    print(f"Created temporary TTF file: {ttf_path}")
    
    if validate_ttf(ttf_path):
        print("The generated TTF file is valid and should be accepted by browsers")
    else:
        print("The generated TTF file is invalid")
    
    # Clean up
    try:
        import shutil
        shutil.rmtree(os.path.dirname(ttf_path))
    except:
        pass

if __name__ == "__main__":
    main()
