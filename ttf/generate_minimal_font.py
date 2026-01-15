#!/usr/bin/env python3
"""
Generate minimal valid TTF font using fonttools
This creates a properly structured TTF with a single zero-width glyph
"""

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
import os


def create_minimal_ttf():
    """Create a minimal valid TTF font with fonttools"""
    
    # Create a new font object (this will create some default tables)
    font = TTFont()
    
    # Set glyph order (required: .notdef is first)
    font.setGlyphOrder([".notdef", "zeroWidthGlyph"])
    
    # --- Create glyf table ---
    font['glyf'] = font.newTable('glyf')
    glyf_table = font['glyf']
    
    # 1. .notdef glyph (required)
    notdef_glyph = Glyph()
    notdef_glyph.name = ".notdef"
    notdef_glyph.numberOfContours = 0  # Empty glyph (simple)
    notdef_glyph.xMin = 0
    notdef_glyph.yMin = 0
    notdef_glyph.xMax = 0
    notdef_glyph.yMax = 0
    glyf_table.glyphs[".notdef"] = notdef_glyph
    
    # 2. Zero width glyph
    zw_glyph = Glyph()
    zw_glyph.name = "zeroWidthGlyph"
    zw_glyph.numberOfContours = 0  # Empty glyph (simple)
    zw_glyph.xMin = 0
    zw_glyph.yMin = 0
    zw_glyph.xMax = 0
    zw_glyph.yMax = 0
    glyf_table.glyphs["zeroWidthGlyph"] = zw_glyph
    
    # --- Create hmtx table (horizontal metrics) ---
    font['hmtx'] = font.newTable('hmtx')
    hmtx_table = font['hmtx']
    hmtx_table.metrics[".notdef"] = (0, 0)  # width, leftSideBearing
    hmtx_table.metrics["zeroWidthGlyph"] = (0, 0)
    
    # --- Create maxp table ---
    font['maxp'] = font.newTable('maxp')
    maxp_table = font['maxp']
    maxp_table.version = 0x00010000
    maxp_table.numGlyphs = 2
    
    # --- Create head table ---
    font['head'] = font.newTable('head')
    head_table = font['head']
    head_table.version = 0x00010000
    head_table.unitsPerEm = 1000
    head_table.xMin = 0
    head_table.yMin = 0
    head_table.xMax = 0
    head_table.yMax = 0
    head_table.fontDirectionHint = 2
    head_table.indexToLocFormat = 0
    head_table.glyphDataFormat = 0
    
    # --- Create hhea table ---
    font['hhea'] = font.newTable('hhea')
    hhea_table = font['hhea']
    hhea_table.version = 0x00010000
    hhea_table.ascent = 800
    hhea_table.descent = -200
    hhea_table.lineGap = 0
    hhea_table.advanceWidthMax = 0
    hhea_table.minLeftSideBearing = 0
    hhea_table.minRightSideBearing = 0
    hhea_table.xMaxExtent = 0
    hhea_table.caretSlopeRise = 1
    hhea_table.caretSlopeRun = 0
    hhea_table.caretOffset = 0
    hhea_table.metricDataFormat = 0
    hhea_table.numberOfHMetrics = 2
    
    # --- Create cmap table ---
    font['cmap'] = font.newTable('cmap')
    cmap_table = font['cmap']
    
    # Remove any existing subtables
    cmap_table.tables.clear()
    
    # Create and add a new cmap subtable
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    subtable = CmapSubtable.newSubtable(4)  # Format 4 (segment mapping)
    subtable.platformID = 3  # Windows
    subtable.platEncID = 1   # Unicode BMP
    subtable.language = 0
    subtable.cmap = {0x0000: 1}  # Default mapping
    
    cmap_table.tables.append(subtable)
    
    # --- Create name table ---
    font['name'] = font.newTable('name')
    name_table = font['name']
    
    # Add minimal naming info
    name_records = [
        (1, 0, 0, 0x0409, "ZeroWidthFont"),    # Family name
        (2, 0, 0, 0x0409, "Regular"),         # Subfamily name
        (4, 0, 0, 0x0409, "ZeroWidthFont Regular"),  # Full name
        (5, 0, 0, 0x0409, "Version 1.0"),     # Version
    ]
    
    for name_id, platform_id, plat_enc_id, lang_id, value in name_records:
        name_table.addName(value, name_id, platform_id, plat_enc_id, lang_id)
    
    # --- Create post table ---
    font['post'] = font.newTable('post')
    post_table = font['post']
    post_table.formatType = 2.0
    post_table.extraNames = []
    post_table.mapping = {}
    
    # --- Create OS/2 table ---
    font['OS/2'] = font.newTable('OS/2')
    os2_table = font['OS/2']
    os2_table.version = 4
    os2_table.xAvgCharWidth = 0
    os2_table.usWeightClass = 400
    os2_table.usWidthClass = 5
    os2_table.fsType = 0
    os2_table.ySubscriptXSize = 600
    os2_table.ySubscriptYSize = 600
    os2_table.ySubscriptXOffset = 0
    os2_table.ySubscriptYOffset = 0
    os2_table.ySuperscriptXSize = 600
    os2_table.ySuperscriptYSize = 600
    os2_table.ySuperscriptXOffset = 0
    os2_table.ySuperscriptYOffset = 0
    os2_table.yStrikeoutSize = 50
    os2_table.yStrikeoutPosition = 300
    os2_table.sFamilyClass = 0x0000
    os2_table.panose = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    os2_table.ulUnicodeRange1 = 0x00000000
    os2_table.ulUnicodeRange2 = 0x00000000
    os2_table.ulUnicodeRange3 = 0x00000000
    os2_table.ulUnicodeRange4 = 0x00000000
    os2_table.achVendID = "NONE"
    os2_table.fsSelection = 0x0040
    os2_table.usFirstCharIndex = 0x0000
    os2_table.usLastCharIndex = 0x0000
    os2_table.sTypoAscender = 800
    os2_table.sTypoDescender = -200
    os2_table.sTypoLineGap = 0
    os2_table.usWinAscent = 800
    os2_table.usWinDescent = 200
    os2_table.ulCodePageRange1 = 0x00000000
    os2_table.ulCodePageRange2 = 0x00000000
    
    # --- Create loca table ---
    font['loca'] = font.newTable('loca')
    
    # Fonttools will automatically compute loca offsets when saving
    
    # Save the font
    output_path = 'base_font.ttf'
    font.save(output_path)
    
    print(f"Successfully generated {output_path}")
    print(f"Font contains {maxp_table.numGlyphs} glyphs")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    
    return output_path


if __name__ == "__main__":
    create_minimal_ttf()