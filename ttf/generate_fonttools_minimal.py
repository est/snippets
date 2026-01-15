#!/usr/bin/env python3
"""
Simple script to generate a minimal valid TTF font using fonttools
This approach builds a font by copying and modifying existing tables
"""

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables._g_l_y_f import Glyph
import os


def create_minimal_font():
    """Create a minimal valid TTF font using fonttools"""
    
    print("Attempting to create minimal TTF font using fonttools...")
    
    try:
        # The easiest way is to take an existing minimal font and modify it
        # Let's create a font with minimal required tables
        
        # Start with a new font
        font = TTFont()
        
        # Add glyph order
        font.setGlyphOrder([".notdef"])
        
        # Create glyf table
        from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
        glyf = table__g_l_y_f()
        glyf.glyphs = {}
        
        # Create .notdef glyph (required by all fonts)
        notdef_glyph = Glyph()
        notdef_glyph.name = ".notdef"
        notdef_glyph.numberOfContours = 0
        notdef_glyph.xMin = 0
        notdef_glyph.yMin = 0
        notdef_glyph.xMax = 0
        notdef_glyph.yMax = 0
        glyf.glyphs[".notdef"] = notdef_glyph
        
        font['glyf'] = glyf
        
        # Create hmtx table
        from fontTools.ttLib.tables._h_m_t_x import table__h_m_t_x
        hmtx = table__h_m_t_x()
        hmtx.metrics = {".notdef": (0, 0)}
        font['hmtx'] = hmtx
        
        # Create maxp table
        from fontTools.ttLib.tables._m_a_x_p import table__m_a_x_p
        maxp = table__m_a_x_p()
        maxp.numGlyphs = 1
        font['maxp'] = maxp
        
        # Create head table
        from fontTools.ttLib.tables._h_e_a_d import table__h_e_a_d
        head = table__h_e_a_d()
        head.unitsPerEm = 1000
        head.xMin = 0
        head.yMin = 0
        head.xMax = 0
        head.yMax = 0
        head.indexToLocFormat = 0
        font['head'] = head
        
        # Create hhea table
        from fontTools.ttLib.tables._h_h_e_a import table__h_h_e_a
        hhea = table__h_h_e_a()
        hhea.ascent = 800
        hhea.descent = -200
        hhea.numberOfHMetrics = 1
        font['hhea'] = hhea
        
        # Create cmap table
        from fontTools.ttLib.tables._c_m_a_p import table__c_m_a_p, CmapSubtable
        cmap = table__c_m_a_p()
        subtable = CmapSubtable.newSubtable(4)
        subtable.platformID = 3
        subtable.platEncID = 1
        subtable.language = 0
        subtable.cmap = {0x0000: 0}
        cmap.tables = [subtable]
        font['cmap'] = cmap
        
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
        
        # Create vertical metrics tables
        font['vmtx'] = table__h_m_t_x()
        from fontTools.ttLib.tables._v_h_e_a import table__v_h_e_a
        font['vhea'] = table__v_h_e_a()
        
        # Save the font
        output_path = 'base_font.ttf'
        font.save(output_path)
        
        print(f"Successfully generated {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
        
        return output_path
        
    except Exception as e:
        print(f"Error creating font: {e}")
        import traceback
        print(traceback.format_exc())
        
        return None


def verify_font(file_path):
    """Verify that the generated font is valid"""
    try:
        font = TTFont(file_path)
        
        # Check basic font structure
        print("\nFont verification:")
        print(f"Number of glyphs: {font['maxp'].numGlyphs}")
        print(f"Font family: {font['name'].getName(1, 0, 0).string.decode('utf-16be') if font['name'].getName(1, 0, 0) else 'Unknown'}")
        print(f"Units per em: {font['head'].unitsPerEm}")
        
        # Check cmap
        if 'cmap' in font:
            print(f"Number of cmap subtables: {len(font['cmap'].tables)}")
            if font['cmap'].tables:
                subtable = font['cmap'].tables[0]
                print(f"cmap format: {subtable.format}")
                print(f"Number of character mappings: {len(subtable.cmap)}")
        
        print(f"\nFont is valid")
        return True
        
    except Exception as e:
        print(f"Error verifying font: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    font_path = create_minimal_font()
    
    if font_path and os.path.exists(font_path):
        verify_font(font_path)
    else:
        print("Failed to create valid font")
