#!/usr/bin/env python3
"""
Generate minimal valid TTF font using fonttools
This creates a properly structured TTF with a single zero-width glyph
"""

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
from fontTools.misc.transform import Identity

import os


def create_minimal_ttf():
    """Create a minimal valid TTF font with fonttools"""
    
    # Create a new font with necessary tables
    font = TTFont()
    
    # Add required tables
    font['glyf'] = font.getTableClass('glyf')()
    font['cmap'] = font.getTableClass('cmap')()
    font['maxp'] = font.getTableClass('maxp')()
    font['head'] = font.getTableClass('head')()
    font['hhea'] = font.getTableClass('hhea')()
    font['hmtx'] = font.getTableClass('hmtx')()
    font['name'] = font.getTableClass('name')()
    font['post'] = font.getTableClass('post')()
    font['OS/2'] = font.getTableClass('OS/2')()
    font['loca'] = font.getTableClass('loca')()
    
    # Set basic font parameters
    font.setGlyphOrder([".notdef", "zeroWidthGlyph"])
    
    # Create glyf table
    glyf_table = font['glyf']
    
    # 1. .notdef glyph (required by font specs)
    notdef_glyph = Glyph()
    notdef_glyph.name = ".notdef"
    notdef_glyph.numberOfContours = 0  # Empty glyph
    notdef_glyph.xMin = 0
    notdef_glyph.yMin = 0
    notdef_glyph.xMax = 0
    notdef_glyph.yMax = 0
    glyf_table.glyphs[".notdef"] = notdef_glyph
    
    # 2. Zero width glyph
    zw_glyph = Glyph()
    zw_glyph.name = "zeroWidthGlyph"
    zw_glyph.numberOfContours = 0  # Empty glyph
    zw_glyph.xMin = 0
    zw_glyph.yMin = 0
    zw_glyph.xMax = 0
    zw_glyph.yMax = 0
    glyf_table.glyphs["zeroWidthGlyph"] = zw_glyph
    
    # Create hmtx table (horizontal metrics)
    hmtx_table = font['hmtx']
    hmtx_table.metrics[".notdef"] = (0, 0)  # width, leftSideBearing
    hmtx_table.metrics["zeroWidthGlyph"] = (0, 0)  # zero width
    
    # Create maxp table (maximum profile)
    maxp_table = font['maxp']
    maxp_table.version = 0x00010000
    maxp_table.numGlyphs = 2
    
    # Create head table (font header)
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
    
    # Create hhea table (horizontal header)
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
    
    # Create cmap table (character to glyph mapping)
    cmap_table = font['cmap']
    
    # Remove existing cmap tables and create a new one
    for table in list(cmap_table.tables):
        cmap_table.tables.remove(table)
    
    # Create a new cmap subtable (Windows Unicode BMP)
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    subtable = CmapSubtable.newSubtable(4)  # Format 4 (segment mapping to delta)
    subtable.platformID = 3
    subtable.platEncID = 1
    subtable.language = 0
    
    # Map all characters to zero width glyph (glyph index 1)
    # We'll set to a default range, JavaScript will modify this
    subtable.cmap = {0x0000: 1}  # Default mapping
    
    cmap_table.tables.append(subtable)
    
    # Create name table
    name_table = font['name']
    
    # Add minimal font naming information
    name_records = [
        # Font Family name (English)
        (1, 0, 0, 0x0409, "ZeroWidthFont"),
        # Font Subfamily name (English)
        (2, 0, 0, 0x0409, "Regular"),
        # Unique font identifier
        (3, 0, 0, 0x0409, "1.0"),
        # Full font name
        (4, 0, 0, 0x0409, "ZeroWidthFont Regular"),
        # Version string
        (5, 0, 0, 0x0409, "Version 1.0"),
    ]
    
    for name_id, platform_id, plat_enc_id, lang_id, value in name_records:
        name_table.addName(value, name_id, platform_id, plat_enc_id, lang_id)
    
    # Create post table (PostScript)
    post_table = font['post']
    post_table.formatType = 2.0
    post_table.extraNames = []
    post_table.mapping = {}
    
    # Create OS/2 table
    os2_table = font['OS/2']
    os2_table.version = 4
    os2_table.xAvgCharWidth = 0
    os2_table.usWeightClass = 400  # Regular
    os2_table.usWidthClass = 5  # Medium
    os2_table.fsType = 0  # Installable
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
    os2_table.fsSelection = 0x0040  # Regular
    os2_table.usFirstCharIndex = 0x0000
    os2_table.usLastCharIndex = 0x0000
    os2_table.sTypoAscender = 800
    os2_table.sTypoDescender = -200
    os2_table.sTypoLineGap = 0
    os2_table.usWinAscent = 800
    os2_table.usWinDescent = 200
    os2_table.ulCodePageRange1 = 0x00000000
    os2_table.ulCodePageRange2 = 0x00000000
    
    # Create loca table (glyph location)
    loca_table = font['loca']
    
    # Calculate glyph offsets (using short offsets since we have < 65536 glyphs)
    # Fonttools will automatically calculate these based on glyf table data
    
    # Create vmtx table (vertical metrics) - optional but recommended
    if 'vmtx' not in font:
        font['vmtx'] = font.getTableClass('vmtx')()
    
    # Create vhea table (vertical header) - optional but recommended
    if 'vhea' not in font:
        font['vhea'] = font.getTableClass('vhea')()
        font['vhea'].version = 0x00010000
        font['vhea'].ascent = 800
        font['vhea'].descent = -200
        font['vhea'].lineGap = 0
        font['vhea'].advanceHeightMax = 0
        font['vhea'].minTopSideBearing = 0
        font['vhea'].minBottomSideBearing = 0
        font['vhea'].yMaxExtent = 0
        font['vhea'].caretSlopeRise = 0
        font['vhea'].caretSlopeRun = 1
        font['vhea'].caretOffset = 0
        font['vhea'].metricDataFormat = 0
        font['vhea'].numberOfVMetrics = 2
    
    # Recalculate all table checksums
    for tag in font.keys():
        table = font[tag]
        if hasattr(table, 'compile'):
            # This triggers checksum calculation
            pass
    
    # Save the font
    output_path = 'base_font.ttf'
    font.save(output_path)
    
    print(f"Successfully generated {output_path}")
    print(f"Font contains {maxp_table.numGlyphs} glyphs")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    
    return output_path


if __name__ == "__main__":
    create_minimal_ttf()
