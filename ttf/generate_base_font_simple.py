#!/usr/bin/env python3
"""
Simple script to generate minimal valid TTF font using fonttools
This creates a properly structured TTF with a single zero-width glyph
"""

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables._g_l_y_f import Glyph
import os


def create_minimal_ttf():
    """Create a minimal valid TTF font with fonttools using a different approach"""
    
    # Create a new font by copying minimal existing structure
    # We'll create a font with minimal required tables
    font = TTFont()
    
    # Set glyph order
    font.setGlyphOrder([".notdef", "zeroWidthGlyph"])
    
    # Create glyf table
    from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
    font['glyf'] = table__g_l_y_f()
    font['glyf'].glyphs = {}
    
    # Create .notdef glyph
    notdef_glyph = Glyph()
    notdef_glyph.name = ".notdef"
    notdef_glyph.numberOfContours = 0
    notdef_glyph.xMin = 0
    notdef_glyph.yMin = 0
    notdef_glyph.xMax = 0
    notdef_glyph.yMax = 0
    font['glyf'].glyphs[".notdef"] = notdef_glyph
    
    # Create zero width glyph
    zw_glyph = Glyph()
    zw_glyph.name = "zeroWidthGlyph"
    zw_glyph.numberOfContours = 0
    zw_glyph.xMin = 0
    zw_glyph.yMin = 0
    zw_glyph.xMax = 0
    zw_glyph.yMax = 0
    font['glyf'].glyphs["zeroWidthGlyph"] = zw_glyph
    
    # Create hmtx table
    from fontTools.ttLib.tables._h_m_t_x import table__h_m_t_x
    font['hmtx'] = table__h_m_t_x()
    font['hmtx'].metrics = {
        ".notdef": (0, 0),
        "zeroWidthGlyph": (0, 0)
    }
    
    # Create maxp table
    from fontTools.ttLib.tables._m_a_x_p import table__m_a_x_p
    font['maxp'] = table__m_a_x_p()
    font['maxp'].numGlyphs = 2
    
    # Create head table
    from fontTools.ttLib.tables._h_e_a_d import table__h_e_a_d
    font['head'] = table__h_e_a_d()
    font['head'].unitsPerEm = 1000
    font['head'].xMin = 0
    font['head'].yMin = 0
    font['head'].xMax = 0
    font['head'].yMax = 0
    
    # Create hhea table
    from fontTools.ttLib.tables._h_h_e_a_a import table__h_h_e_a_a
    font['hhea'] = table__h_h_e_a_a()
    font['hhea'].ascent = 800
    font['hhea'].descent = -200
    font['hhea'].numberOfHMetrics = 2
    
    # Create cmap table
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    font['cmap'] = font.getTableData('cmap') if hasattr(font, 'getTableData') else None
    if font['cmap'] is None:
        from fontTools.ttLib.tables._c_m_a_p import table__c_m_a_p
        font['cmap'] = table__c_m_a_p()
        font['cmap'].tables = []
    
    # Create cmap subtable (Windows Unicode BMP)
    subtable = CmapSubtable.newSubtable(4)
    subtable.platformID = 3
    subtable.platEncID = 1
    subtable.language = 0
    subtable.cmap = {0x0000: 1}
    font['cmap'].tables.append(subtable)
    
    # Create name table
    from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e
    font['name'] = table__n_a_m_e()
    
    # Create post table
    from fontTools.ttLib.tables._p_o_s_t import table__p_o_s_t
    font['post'] = table__p_o_s_t()
    
    # Create OS/2 table
    from fontTools.ttLib.tables._o_s_2 import table__o_s_2
    font['OS/2'] = table__o_s_2()
    
    # Create loca table
    from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
    font['loca'] = table__l_o_c_a()
    
    # Create horizontal and vertical metrics
    font['vmtx'] = table__h_m_t_x()
    font['vhea'] = table__h_h_e_a_a()
    
    # Save the font
    output_path = 'base_font.ttf'
    
    try:
        font.save(output_path)
        print(f"Successfully generated {output_path}")
        print(f"Font size: {os.path.getsize(output_path)} bytes")
    except Exception as e:
        print(f"Error saving font: {e}")
        import traceback
        print(traceback.format_exc())
    
    return output_path


if __name__ == "__main__":
    # Try to create the font
    create_minimal_ttf()
    
    # Verify if file was created and check its size
    if os.path.exists('base_font.ttf'):
        print(f"\nFile created successfully")
        print(f"Size: {os.path.getsize('base_font.ttf')} bytes")
    else:
        print(f"\nFailed to create file")
