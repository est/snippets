#!/usr/bin/env python3
import os
import tempfile
import base64
import shutil
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.misc.transform import Identity

def create_simple_zero_width_font():
    # Create a new font
    font = TTFont()
    
    # Set glyph order
    font.setGlyphOrder(['.notdef', 'zeroWidthGlyph'])
    
    # Create necessary tables
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
    
    from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
    font['loca'] = table__l_o_c_a()
    
    from fontTools.ttLib.tables._c_m_a_p import table__c_m_a_p
    font['cmap'] = table__c_m_a_p()
    
    from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e
    font['name'] = table__n_a_m_e()
    
    from fontTools.ttLib.tables._p_o_s_t import table__p_o_s_t
    font['post'] = table__p_o_s_t()
    
    from fontTools.ttLib.tables._o_s_2 import table__o_s_2
    font['OS/2'] = table__o_s_2()
    
    # Create glyphs
    glyf = font['glyf']
    glyf.glyphs = {}
    
    # .notdef glyph
    pen = TTGlyphPen(None)
    glyf.glyphs['.notdef'] = pen.glyph()
    
    # zeroWidthGlyph
    pen = TTGlyphPen(None)
    glyf.glyphs['zeroWidthGlyph'] = pen.glyph()
    
    # Create cmap table
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    newTable = CmapSubtable.newSubtable(4)
    newTable.cmap[0x2603] = 'zeroWidthGlyph'
    newTable.platformID = 0
    newTable.platEncID = 3
    newTable.language = 0
    font['cmap'].tables.append(newTable)
    
    # Set name table
    name = font['name']
    name.addName('ZeroWidthFont', 0, 0, 0, 0x409)
    name.addName('ZeroWidthFont', 1, 0, 0, 0x409)
    name.addName('ZeroWidthFont', 2, 0, 0, 0x409)
    name.addName('ZeroWidthFont', 3, 0, 0, 0x409)
    
    # Set post table
    post = font['post']
    post.formatType = 3
    
    # Set OS/2 table
    os2 = font['OS/2']
    os2.version = 0x0004
    os2.xAvgCharWidth = 0
    os2.usWeightClass = 400
    os2.usWidthClass = 5
    os2.fsType = 0
    os2.sFamilyClass = 0
    os2.panose = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    os2.achVendID = 'XXXX'
    os2.fsSelection = 0
    os2.usFirstCharIndex = 0x2603
    os2.usLastCharIndex = 0x2603
    os2.sTypoAscender = 800
    os2.sTypoDescender = -200
    os2.sTypoLineGap = 0
    os2.usWinAscent = 800
    os2.usWinDescent = 200
    
    # Write the font to file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "zero_width_font.ttf")
    font.save(temp_path)
    
    print(f"Generated TTF file at: {temp_path}")
    
    return temp_path

def validate_font(ttf_path):
    try:
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
    ttf_path = create_simple_zero_width_font()
    
    if validate_font(ttf_path):
        # Read the generated TTF file and create a data URL for HTML
        with open(ttf_path, 'rb') as f:
            base64_encoded = base64.b64encode(f.read()).decode('utf-8')
            data_url = f"data:font/ttf;base64,{base64_encoded}"
            print("\nData URL for HTML:")
            print(data_url)
        
        # Copy the file to the current directory
        try:
            dest_path = os.path.join(os.getcwd(), "zero_width_font.ttf")
            shutil.copy(ttf_path, dest_path)
            print(f"\nFont file saved to: {dest_path}")
        except Exception as e:
            print(f"Error copying file: {e}")
    
    # Cleanup
    try:
        shutil.rmtree(os.path.dirname(ttf_path))
    except:
        pass
