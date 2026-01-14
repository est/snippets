#!/usr/bin/env python3

import sys
from io import BytesIO

# Copy of the current JavaScript implementation of u16 and u32
def u16(v):
    return [v >> 8, v & 255]

def u32(v):
    return [v >> 24, (v >> 16) & 255, (v >> 8) & 255, v & 255]

print("Calculating current maxp table length...")
# Current maxp table definition from index.html
maxp = [
    *u32(0x00010000),
    *u16(1),
    *u16(0), *u16(0),
    *u16(0), *u16(0),
    *u16(0), *u16(0),
    *u16(0), *u16(0),
    *u16(0), *u16(0),
    *u16(0), *u16(0),
    *u16(0)
]

print(f"Current maxp table length: {len(maxp)} bytes")
required_length = 4 + 2 + (13 * 2)  # tableVersion(4) + numGlyphs(2) + 13 fields of 2 bytes each
print(f"Required length for maxp 1.0: {required_length} bytes")

if len(maxp) < required_length:
    print(f"Need {required_length - len(maxp)} more bytes")
elif len(maxp) > required_length:
    print(f"Need to remove {len(maxp) - required_length} bytes")
else:
    print("Perfect length!")

# Create a hex dump for debugging
print("\nHex dump:")
for i in range(0, len(maxp), 8):
    row = maxp[i:i+8]
    hex_str = " ".join(f"{b:02X}" for b in row)
    print(f"{i:04X}: {hex_str}")
