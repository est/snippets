#!/usr/bin/env python3
import os
import tempfile
import base64
import shutil

def create_minimal_zero_width_font():
    # This is a minimal valid TTF font with zero width glyph for U+2603
    ttf_bytes = bytes([
        # SFNT Header
        0x00, 0x01, 0x00, 0x00,  # Version 1.0
        0x00, 0x0a,              # Number of tables (10)
        0x00, 0x08,              # Search range (2^3 * 16)
        0x00, 0x03,              # Entry selector (log2(8))
        0x00, 0x04,              # Range shift
        
        # Table directory entries
        # cmap table
        0x63, 0x6D, 0x61, 0x70,  # 'cmap'
        0x00, 0x00, 0x00, 0x00,  # Checksum (will be calculated)
        0x00, 0x00, 0x00, 0x1C,  # Offset
        0x00, 0x00, 0x00, 0x30,  # Length
        
        # glyf table
        0x67, 0x6C, 0x79, 0x66,  # 'glyf'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0x4C,  # Offset
        0x00, 0x00, 0x00, 0x14,  # Length
        
        # head table
        0x68, 0x65, 0x61, 0x64,  # 'head'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0x60,  # Offset
        0x00, 0x00, 0x00, 0x24,  # Length
        
        # hhea table
        0x68, 0x68, 0x65, 0x61,  # 'hhea'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0x84,  # Offset
        0x00, 0x00, 0x00, 0x24,  # Length
        
        # hmtx table
        0x68, 0x6D, 0x74, 0x78,  # 'hmtx'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0xA8,  # Offset
        0x00, 0x00, 0x00, 0x08,  # Length
        
        # loca table
        0x6C, 0x6F, 0x63, 0x61,  # 'loca'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0xB0,  # Offset
        0x00, 0x00, 0x00, 0x04,  # Length
        
        # maxp table
        0x6D, 0x61, 0x78, 0x70,  # 'maxp'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0xB4,  # Offset
        0x00, 0x00, 0x00, 0x14,  # Length
        
        # name table
        0x6E, 0x61, 0x6D, 0x65,  # 'name'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0xC8,  # Offset
        0x00, 0x00, 0x00, 0x06,  # Length
        
        # OS/2 table
        0x4F, 0x53, 0x2F, 0x32,  # 'OS/2'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0xCE,  # Offset
        0x00, 0x00, 0x00, 0x78,  # Length
        
        # post table
        0x70, 0x6F, 0x73, 0x74,  # 'post'
        0x00, 0x00, 0x00, 0x00,  # Checksum
        0x00, 0x00, 0x00, 0x146, # Offset
        0x00, 0x00, 0x00, 0x20,  # Length
        
        # cmap table content
        0x00, 0x00, 0x00, 0x01,  # Version, number of subtables
        0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x0C,  # Platform ID, encoding, offset
        0x00, 0x04, 0x00, 0x24, 0x00, 0x00,  # Format 4, length, language
        0x00, 0x01, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00,  # 1 group, search range, entry selector, range shift
        0x26, 0x03, 0x26, 0x03, 0x00, 0x00,  # U+2603 to glyph 0
        
        # glyf table content (single empty glyph)
        0x00, 0x00,  # Number of contours (0 for empty)
        0x00, 0x00,  # xMin
        0x00, 0x00,  # yMin
        0x00, 0x00,  # xMax
        0x00, 0x00,  # yMax
        
        # head table content
        0x00, 0x01, 0x00, 0x00,  # Version
        0x00, 0x00, 0x00, 0x00,  # Checksum adjustment
        0x5F, 0x0F, 0x3C, 0xF5,  # Magic number
        0x00, 0x00,  # Flags
        0x03, 0xE8,  # Units per em (1000)
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Created
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Modified
        0xFF, 0xC8, 0xFF, 0xC8,  # xMin, yMin (-50)
        0x03, 0x20, 0x03, 0x20,  # xMax, yMax (800)
        0x00, 0x00,  # Mac style
        0x00, 0x0A,  # Lowest rec PPEM (10)
        0x00, 0x02, 0x00, 0x00, 0x00, 0x00,  # Font direction, loca format, glyph data format
        
        # hhea table content
        0x00, 0x01, 0x00, 0x00,  # Version
        0x03, 0x20, 0xFF, 0xC8,  # Ascent (800), descent (-50)
        0x00, 0x00,  # Line gap
        0x00, 0x00,  # Advance width max (0)
        0x00, 0x00, 0x00, 0x00,  # Min left/right side bearing
        0x00, 0x00,  # x max extent
        0x00, 0x01, 0x00, 0x00,  # Caret slope
        0x00, 0x00, 0x00, 0x00,  # Caret offset
        0x00, 0x00, 0x00, 0x01,  # Metric data format, number of h metrics
        
        # hmtx table content
        0x00, 0x00, 0x00, 0x00,  # Advance width 0, left side bearing 0
        0x00, 0x00, 0x00, 0x00,  # Advance width 0, left side bearing 0
        
        # loca table content
        0x00, 0x00, 0x00, 0x0A,  # Glyph 0 offset, glyph 1 offset (10 bytes)
        
        # maxp table content
        0x00, 0x01, 0x00, 0x00,  # Version 1.0
        0x00, 0x02,  # Number of glyphs (2)
        0x00, 0x00, 0x00, 0x00,  # Max points, max contours
        0x00, 0x00, 0x00, 0x00,  # Max composite points, max composite contours
        0x00, 0x00, 0x00, 0x00,  # Max zones, max twilight points
        0x00, 0x00, 0x00, 0x00,  # Max storage, max function defs
        0x00, 0x00, 0x00, 0x00,  # Max instruction defs, max stack elements
        0x00, 0x00, 0x00, 0x00,  # Max size of instructions, max component elements
        0x00, 0x00,  # Max component depth
        
        # name table content
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Version, count, string offset
        
        # OS/2 table content
        0x00, 0x04,  # Version
        0x00, 0x00,  # xAvgCharWidth
        0x01, 0x90,  # usWeightClass (400)
        0x00, 0x05,  # usWidthClass (5)
        0x00, 0x00,  # fsType
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Sub/superscript metrics
        0x00, 0x00, 0x00, 0x00,  # Strikeout metrics
        0x00, 0x00,  # sFamilyClass
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Panose
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Unicode ranges
        0x58, 0x58, 0x58, 0x58,  # achVendID (XXXX)
        0x00, 0x00,  # fsSelection
        0x26, 0x03, 0x26, 0x03,  # usFirstCharIndex, usLastCharIndex
        0x03, 0x20, 0xFF, 0xC8,  # sTypoAscender, sTypoDescender
        0x00, 0x00,  # sTypoLineGap
        0x03, 0x20, 0x00, 0x32,  # usWinAscent (800), usWinDescent (50)
        0x00, 0x00, 0x00, 0x00,  # Code page ranges
        0x00, 0x00, 0x00, 0x00,  # sxHeight, sCapHeight
        
        # post table content
        0x00, 0x01, 0x00, 0x00,  # Version 1.0
        0x00, 0x00, 0x00, 0x00,  # Italic angle
        0x00, 0x00, 0x00, 0x00,  # Underline position, thickness
        0x00, 0x00, 0x00, 0x00,  # isFixedPitch
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Min/max mem Type42
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00   # Min/max mem Type1
    ])
    
    # Calculate table checksums
    tables = [
        ('cmap', 0x1C, 0x30), ('glyf', 0x4C, 0x14), ('head', 0x60, 0x24), 
        ('hhea', 0x84, 0x24), ('hmtx', 0xA8, 0x08), ('loca', 0xB0, 0x04), 
        ('maxp', 0xB4, 0x14), ('name', 0xC8, 0x06), ('OS/2', 0xCE, 0x78), 
        ('post', 0x146, 0x20)
    ]
    
    total_checksum = 0
    for tag, offset, length in tables:
        table_data = ttf_bytes[offset:offset+length]
        # Pad to multiple of 4
        padded_length = (length + 3) & ~3
        padded_data = table_data + b'\x00' * (padded_length - length)
        
        # Calculate checksum
        checksum = 0
        for i in range(0, len(padded_data), 4):
            chunk = padded_data[i:i+4]
            while len(chunk) < 4:
                chunk += b'\x00'
            checksum += int.from_bytes(chunk, 'big')
        
        total_checksum += checksum & 0xffffffff
        
        # Update table directory checksum
        dir_offset = 12 + tables.index((tag, offset, length)) * 16 + 4
        ttf_bytes = bytearray(ttf_bytes)
        ttf_bytes[dir_offset:dir_offset+4] = (checksum & 0xffffffff).to_bytes(4, 'big')
    
    # Calculate and update head.checkSumAdjustment
    checksum_adjustment = (0xB1B0AFBA - total_checksum) & 0xffffffff
    head_dir_index = tables.index(('head', 0x60, 0x24))
    head_checksum_offset = 12 + head_dir_index * 16 + 4
    ttf_bytes[head_checksum_offset:head_checksum_offset+4] = checksum_adjustment.to_bytes(4, 'big')
    # Update head table checksum adjustment
    ttf_bytes[0x64:0x68] = checksum_adjustment.to_bytes(4, 'big')
    
    # Write to file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "minimal_zero_width_font.ttf")
    with open(temp_path, 'wb') as f:
        f.write(ttf_bytes)
    
    print(f"Generated TTF file at: {temp_path}")
    return temp_path

def validate_font(ttf_path):
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(ttf_path)
        print("Font validated successfully")
        print(f"Number of glyphs: {font['maxp'].numGlyphs}")
        print(f"Glyph order: {font.getGlyphOrder()}")
        print(f"Character map:")
        for table in font['cmap'].tables:
            print(f"  Format {table.format}, Platform {table.platformID}, Encoding {table.platEncID}")
            for code, glyph in table.cmap.items():
                print(f"    U+{code:04X}: {glyph}")
        return True
    except Exception as e:
        print(f"Error validating font: {e}")
        return False

if __name__ == "__main__":
    ttf_path = create_minimal_zero_width_font()
    
    if validate_font(ttf_path):
        # Read the generated TTF file and create a data URL for HTML
        with open(ttf_path, 'rb') as f:
            base64_encoded = base64.b64encode(f.read()).decode('utf-8')
            data_url = f"data:font/ttf;base64,{base64_encoded}"
            print("\nData URL for HTML:")
            print(data_url)
        
        # Copy the file to the current directory
        try:
            dest_path = os.path.join(os.getcwd(), "minimal_zero_width_font.ttf")
            shutil.copy(ttf_path, dest_path)
            print(f"\nFont file saved to: {dest_path}")
        except Exception as e:
            print(f"Error copying file: {e}")
    
    # Cleanup
    try:
        shutil.rmtree(os.path.dirname(ttf_path))
    except:
        pass
