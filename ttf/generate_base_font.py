#!/usr/bin/env python3
"""
Generate the minimal valid TTF font with zero-width characters
用于生成最精简的基础 TTF 字体，然后在 JavaScript 中修改 cmap 表
"""

import struct
import os


def u16(v):
    return struct.pack('>H', v)


def u32(v):
    return struct.pack('>I', v)


def pad4(data):
    """Pad data to 4-byte boundary with zeros"""
    pad_length = (4 - len(data) % 4) % 4
    return data + b'\x00' * pad_length


def calculate_checksum(data):
    """Calculate TTF checksum for data"""
    sum_val = 0
    # Pad to 4-byte boundary if necessary
    padded_data = pad4(data)
    
    for i in range(0, len(padded_data), 4):
        chunk = padded_data[i:i+4]
        # Handle possible shorter chunks at end
        if len(chunk) < 4:
            chunk = chunk.ljust(4, b'\x00')
        sum_val += struct.unpack('>I', chunk)[0]
        sum_val &= 0xffffffff  # Keep as 32-bit unsigned
    
    return sum_val


def create_base_ttf():
    """Create the minimal valid TTF file"""
    tables = []
    
    # 1. glyf - single empty glyph (10 bytes)
    glyf_data = (
        b'\x00\x00' +   # numberOfContours (0 for empty glyph)
        b'\x00\x00' +   # xMin
        b'\x00\x00' +   # yMin
        b'\x00\x00' +   # xMax
        b'\x00\x00'     # yMax
    )
    tables.append({'tag': 'glyf', 'data': pad4(glyf_data)})
    
    # 2. loca - glyph location table (2 bytes per glyph, 2 glyphs max)
    tables.append({'tag': 'loca', 'data': pad4(b'\x00\x00\x00\x00')})
    
    # 3. hmtx - horizontal metrics
    tables.append({'tag': 'hmtx', 'data': pad4(b'\x00\x00\x00\x00')})
    
    # 4. maxp - maximum profile
    maxp_data = (
        u32(0x00010000) +  # version 1.0
        u16(1) +           # numGlyphs
        u16(0) + u16(0) +  # maxPoints, maxContours
        u16(0) + u16(0) +  # maxCompositePoints, maxCompositeContours
        u16(0) + u16(0) +  # maxZones, maxTwilightPoints
        u16(0) + u16(0) +  # maxStorage, maxFunctionDefs
        u16(0) + u16(0) +  # maxInstructionDefs, maxStackElements
        u16(0) + u16(0) +  # maxSizeOfInstructions, maxComponentElements
        u16(0)             # maxComponentDepth
    )
    tables.append({'tag': 'maxp', 'data': pad4(maxp_data)})
    
    # 5. head - font header (36 bytes)
    head_data = (
        u32(0x00010000) +          # version 1.0
        u32(0) +                   # checkSumAdjustment (will be calculated)
        u32(0x5F0F3CF5) +          # magicNumber
        u16(0) +                   # flags
        u16(1000) +                # unitsPerEm
        u32(0) + u32(0) +          # created, modified (placeholder)
        u16(0xFC70) + u16(0xFC70) +    # xMin, yMin (-200 in 16-bit unsigned)
        u16(1200) + u16(1200) +    # xMax, yMax
        u16(0) + u16(10) +         # macStyle, lowestRecPPEM
        u16(2) + u16(0) + u16(0)   # fontDirectionHint, indexToLocFormat, glyphDataFormat
    )
    tables.append({'tag': 'head', 'data': pad4(head_data)})
    
    # 6. hhea - horizontal header (36 bytes)
    hhea_data = (
        u32(0x00010000) +          # version 1.0
        u16(0xFC70) + u16(0xFC70) +    # ascent, descent (-200 in 16-bit unsigned)
        u16(0) +                   # lineGap
        u16(1000) +                # advanceWidthMax
        u16(0xFC70) + u16(0xFC70) +    # minLeftSideBearing, minRightSideBearing (-200 in 16-bit unsigned)
        u16(0) +                   # xMaxExtent
        u16(1) +                   # caretSlopeRise
        u16(0) +                   # caretSlopeRun
        u32(0) +                   # caretOffset
        u16(0) + u16(1)            # metricDataFormat, numberOfHMetrics
    )
    tables.append({'tag': 'hhea', 'data': pad4(hhea_data)})
    
    # 7. cmap - character to glyph mapping (format 4)
    cmap_data = (
        b'\x00\x00' + b'\x00\x01' +  # version, number of tables
        b'\x00\x03' + b'\x00\x01' + b'\x00\x00' + b'\x00\x0C' +  # platformID, platformSpecificID, offset
        u16(4) + u16(44) + u16(0) +  # format, length, language
        u16(1) + u16(8) + u16(0) + u16(0) +  # nGroups, searchRange, entrySelector, rangeShift
        u16(0) + u16(0) + u16(0)  # startCharCode, endCharCode, glyphID (will be modified in JS)
    )
    tables.append({'tag': 'cmap', 'data': pad4(cmap_data)})
    
    # 8. name - font naming
    tables.append({'tag': 'name', 'data': pad4(b'\x00\x00\x00\x00\x00\x00')})
    
    # 9. post - PostScript info (32 bytes)
    post_data = (
        u32(0x00010000) +          # version 1.0
        u32(0) +                   # italicAngle
        u16(0) + u16(0) +          # underlinePosition, underlineThickness
        u32(0) +                   # isFixedPitch
        u32(0) + u32(0) +          # minMemType42, maxMemType42
        u32(0) + u32(0)            # minMemType1, maxMemType1
    )
    tables.append({'tag': 'post', 'data': pad4(post_data)})
    
    # 10. OS/2 table
    os2_data = (
        u16(0x0004) + b'\x00\x00' +
        u16(1000) + u16(5) + u16(0) +
        u16(1000) + u16(1000) + u16(0) + u16(0) +
        u16(1200) + u16(1200) + u16(0) + u16(0) +
        u16(200) + u16(0) + u16(0) +
        b'\x00' * 8 +
        u32(0) + u32(0) + u32(0) + u32(0) +
        u16(0x0409) + u16(0) +
        u16(65535) + u16(0) +
        u16(0) + u16(0) + u16(0) +
        u16(1200) + u16(200) +
        b'\x00' * 18  # 补全到最小长度
    )
    tables.append({'tag': 'OS/2', 'data': pad4(os2_data)})
    
    # Sort tables alphabetically by tag
    sorted_tables = sorted(tables, key=lambda x: x['tag'])
    
    # Calculate offsets and lengths
    offset = 12 + len(sorted_tables) * 16
    for table in sorted_tables:
        table['offset'] = offset
        table['length'] = len(table['data'])
        table['checksum'] = calculate_checksum(table['data'])
        offset += table['length']
    
    # Calculate checkSumAdjustment
    head_table = next(t for t in sorted_tables if t['tag'] == 'head')
    total_checksum = sum(t['checksum'] for t in sorted_tables) & 0xffffffff
    check_sum_adjustment = (0xB1B0AFBA - total_checksum) & 0xffffffff
    
    # Update head table's checkSumAdjustment
    head_data = bytearray(head_table['data'])
    struct.pack_into('>I', head_data, 4, check_sum_adjustment)
    head_table['data'] = bytes(head_data)
    head_table['checksum'] = calculate_checksum(head_table['data'])
    
    # Build the TTF file
    out = bytearray()
    
    # SFNT version and directory header
    out.extend(u32(0x00010000))
    
    # Calculate search parameters
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
    for table in sorted_tables:
        tag_bytes = table['tag'].ljust(4, '\x00').encode('ascii')
        out.extend(tag_bytes)
        out.extend(u32(table['checksum']))
        out.extend(u32(table['offset']))
        out.extend(u32(table['length']))
    
    # Write table data
    for table in sorted_tables:
        out.extend(table['data'])
    
    return bytes(out)


if __name__ == "__main__":
    # Generate and save the base font
    font_data = create_base_ttf()
    output_path = "base_font.ttf"
    
    with open(output_path, 'wb') as f:
        f.write(font_data)
    
    print(f"Successfully generated base font: {output_path}")
    print(f"File size: {len(font_data)} bytes")
