#!/usr/bin/env python3
import os
import tempfile
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen

def generate_proper_ttf():
    # Create a new empty font
    font = TTFont()

    # Add necessary tables
    font.setGlyphOrder(['.notdef', 'zeroWidthGlyph'])

    # Create and add required tables
    from fontTools.ttLib.tables._h_e_a_d import table__h_e_a_d
    font['head'] = table__h_e_a_d()
    head = font['head']
    head.magicNumber = 0x5F0F3CF5
    head.unitsPerEm = 1000
    head.fontDirectionHint = 2
    head.indexToLocFormat = 0
    head.glyphDataFormat = 0
    head.xMin = -10
    head.yMin = -10
    head.xMax = 10
    head.yMax = 10

    from fontTools.ttLib.tables._h_h_e_a import table__h_h_e_a
    font['hhea'] = table__h_h_e_a()
    hhea = font['hhea']
    hhea.ascent = 800
    hhea.descent = -200
    hhea.lineGap = 0
    hhea.advanceWidthMax = 0
    hhea.minLeftSideBearing = 0
    hhea.minRightSideBearing = 0
    hhea.xMaxExtent = 0
    hhea.caretSlopeRise = 1
    hhea.caretSlopeRun = 0
    hhea.caretOffset = 0
    hhea.metricDataFormat = 0
    hhea.numberOfHMetrics = 2

    from fontTools.ttLib.tables._m_a_x_p import table__m_a_x_p
    font['maxp'] = table__m_a_x_p()
    maxp = font['maxp']
    maxp.version = 0x00010000
    maxp.numGlyphs = 2

    from fontTools.ttLib.tables._h_m_t_x import table__h_m_t_x
    font['hmtx'] = table__h_m_t_x()
    hmtx = font['hmtx']
    hmtx.metrics = {
        '.notdef': (0, 0),
        'zeroWidthGlyph': (0, 0)
    }

    from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
    font['glyf'] = table__g_l_y_f()
    glyf = font['glyf']
    pen = TTGlyphPen(None)
    # Create .notdef glyph (empty glyph)
    glyf['.notdef'] = pen.glyph()
    
    # Create zero width glyph (empty glyph)
    pen = TTGlyphPen(None)
    glyf['zeroWidthGlyph'] = pen.glyph()

    from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
    font['loca'] = table__l_o_c_a()

    # cmap table - mapping U+2603 (snowman) to zeroWidthGlyph
    cmap = font['cmap']
    cmapTables = cmap.tables

    # Create a new cmap table (format 4)
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

    newTable = None
    for table in cmapTables:
        if table.format == 4:
            newTable = table
            break
    
    if newTable is None:
        newTable = CmapSubtable.newSubtable(4)
        cmapTables.append(newTable)

    newTable.cmap[0x2603] = 'zeroWidthGlyph'
    newTable.platformID = 0
    newTable.platEncID = 3
    newTable.language = 0

    # name table
    name = font['name']
    name.addName('ZeroWidthFont', 0, 0, 0, 0x409)
    name.addName('ZeroWidthFont', 1, 0, 0, 0x409)
    name.addName('ZeroWidthFont', 2, 0, 0, 0x409)
    name.addName('ZeroWidthFont', 3, 0, 0, 0x409)

    # post table
    post = font['post']
    post.formatType = 3

    # OS/2 table
    os2 = font['OS/2']
    os2.version = 0x0004
    os2.xAvgCharWidth = 0
    os2.usWeightClass = 400
    os2.usWidthClass = 5
    os2.fsType = 0
    os2.ySubscriptXSize = 0
    os2.ySubscriptYSize = 0
    os2.ySubscriptXOffset = 0
    os2.ySubscriptYOffset = 0
    os2.ySuperscriptXSize = 0
    os2.ySuperscriptYSize = 0
    os2.ySuperscriptXOffset = 0
    os2.ySuperscriptYOffset = 0
    os2.yStrikeoutSize = 0
    os2.yStrikeoutPosition = 0
    os2.sFamilyClass = 0
    os2.panose = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    os2.ulUnicodeRange1 = 0
    os2.ulUnicodeRange2 = 0
    os2.ulUnicodeRange3 = 0
    os2.ulUnicodeRange4 = 0
    os2.achVendID = 'XXXX'
    os2.fsSelection = 0
    os2.usFirstCharIndex = 0x2603
    os2.usLastCharIndex = 0x2603
    os2.sTypoAscender = 800
    os2.sTypoDescender = -200
    os2.sTypoLineGap = 0
    os2.usWinAscent = 800
    os2.usWinDescent = 200
    os2.ulCodePageRange1 = 0
    os2.ulCodePageRange2 = 0
    os2.sxHeight = 0
    os2.sCapHeight = 0

    # Write the font to file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "proper_font.ttf")
    font.save(temp_path)
    
    print(f"Generated proper TTF file at: {temp_path}")
    
    # Validate the generated font
    validate_ttf(temp_path)
    
    return temp_path

def validate_ttf(ttf_path):
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(ttf_path)
        print("Font validated successfully")
        print(f"Number of glyphs: {font['maxp'].numGlyphs}")
        print(f"Glyph order: {font.getGlyphOrder()}")
        print(f"Character map:")
        for table in font['cmap'].tables:
            if table.format == 4:
                for code, glyph in table.cmap.items():
                    print(f"  U+{code:04X}: {glyph}")
        return True
    except Exception as e:
        print(f"Error validating font: {e}")
        return False

if __name__ == "__main__":
    ttf_path = generate_proper_ttf()
    
    # Read the generated TTF file and create a data URL for HTML
    with open(ttf_path, 'rb') as f:
        import base64
        base64_encoded = base64.b64encode(f.read()).decode('utf-8')
        data_url = f"data:font/ttf;base64,{base64_encoded}"
        print("\nData URL for HTML:")
        print(data_url)
    
    # Cleanup
    try:
        import shutil
        shutil.rmtree(os.path.dirname(ttf_path))
    except:
        pass
