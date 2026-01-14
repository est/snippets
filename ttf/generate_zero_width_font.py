from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Identity

def main():
    # 创建一个新的 TrueType 字体对象
    font = TTFont()

    # 1. 设置字体的基本信息
    font.setGlyphOrder([".notdef", "zeroWidthGlyph"])
    
    # 2. 添加 'glyf' 表（字形表）
    glyph_table = font['glyf']
    
    # 定义 .notdef 字形（默认字形，空的）
    pen = TTGlyphPen(".notdef")
    glyph_table.glyphs[".notdef"] = pen.glyph()
    
    # 定义 zeroWidthGlyph（空的零宽度字形）
    pen = TTGlyphPen("zeroWidthGlyph")
    glyph_table.glyphs["zeroWidthGlyph"] = pen.glyph()
    
    # 3. 添加 'hmtx' 表（水平度量表）
    hmtx_table = font['hmtx']
    hmtx_table.metrics = {
        ".notdef": (0, 0),       # 宽度为 0，左旁距为 0
        "zeroWidthGlyph": (0, 0)
    }
    
    # 4. 添加 'cmap' 表（字符映射表）
    cmap_table = font['cmap']
    # 使用平台 3（Windows）和编码 1（Unicode）的表
    cmap_table.tables = []
    # 确保我们只有一个表
    for table in cmap_table.tables:
        cmap_table.tables.remove(table)
        
    # 添加新的 cmap 表
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    cmap = CmapSubtable.newSubtable(4)  # 使用格式 4 的 cmap 表（最常见）
    cmap.platformID = 3
    cmap.platEncID = 1
    cmap.language = 0
    cmap.cmap = {0x2603: "zeroWidthGlyph"}  # 将雪人字符 U+2603 映射到零宽度字形
    cmap_table.tables.append(cmap)
    
    # 5. 添加 'head' 表（字体头表）
    head_table = font['head']
    head_table.unitsPerEm = 1000
    head_table.xMin = 0
    head_table.yMin = 0
    head_table.xMax = 0
    head_table.yMax = 0
    head_table.macStyle = 0
    head_table.lowestRecPPEM = 1
    head_table.fontDirectionHint = 2
    head_table.indexToLocFormat = 0  # 短偏移量格式
    head_table.glyphDataFormat = 0
    
    # 6. 添加 'hhea' 表（水平表头表）
    hhea_table = font['hhea']
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
    hhea_table.numberOfHMetrics = 2  # 与字形数量相同
    
    # 7. 添加 'maxp' 表（最大轮廓表）
    maxp_table = font['maxp']
    maxp_table.version = 0x10000  # 1.0 版本
    maxp_table.numGlyphs = 2
    maxp_table.maxPoints = 0
    maxp_table.maxContours = 0
    maxp_table.maxCompositePoints = 0
    maxp_table.maxCompositeContours = 0
    maxp_table.maxZones = 1
    maxp_table.maxTwilightPoints = 0
    maxp_table.maxStorage = 0
    maxp_table.maxFunctionDefs = 0
    maxp_table.maxInstructionDefs = 0
    maxp_table.maxStackElements = 0
    maxp_table.maxSizeOfInstructions = 0
    maxp_table.maxComponentElements = 0
    maxp_table.maxComponentDepth = 0
    
    # 8. 添加 'name' 表（字体名称表）
    name_table = font['name']
    name_table.addName("ZeroWidthFont", platformID=3, platEncID=1, langID=0x409, nameID=1)  # 字体名称
    name_table.addName("ZeroWidthFont", platformID=3, platEncID=1, langID=0x409, nameID=4)  # 完整名称
    name_table.addName("1.0", platformID=3, platEncID=1, langID=0x409, nameID=5)  # 版本
    
    # 9. 添加 'post' 表（PostScript表）
    post_table = font['post']
    post_table.formatType = 2.0
    post_table.italicAngle = 0
    post_table.underlinePosition = -100
    post_table.underlineThickness = 50
    post_table.isFixedPitch = 0
    
    # 10. 添加 'OS/2' 表（操作系统/2 表）
    os2_table = font['OS/2']
    os2_table.version = 1
    os2_table.xAvgCharWidth = 0
    os2_table.usWeightClass = 400
    os2_table.usWidthClass = 5
    os2_table.fsType = 0
    os2_table.ySubscriptXSize = 600
    os2_table.ySubscriptYSize = 600
    os2_table.ySubscriptXOffset = 0
    os2_table.ySubscriptYOffset = 100
    os2_table.ySuperscriptXSize = 600
    os2_table.ySuperscriptYSize = 600
    os2_table.ySuperscriptXOffset = 0
    os2_table.ySuperscriptYOffset = 300
    os2_table.yStrikeoutSize = 50
    os2_table.yStrikeoutPosition = 250
    os2_table.sFamilyClass = 0
    os2_table.panose = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    os2_table.ulUnicodeRange1 = 0x00000001
    os2_table.ulUnicodeRange2 = 0
    os2_table.ulUnicodeRange3 = 0
    os2_table.ulUnicodeRange4 = 0
    os2_table.achVendID = "TEST"
    os2_table.fsSelection = 0
    os2_table.usFirstCharIndex = 0x2603
    os2_table.usLastCharIndex = 0x2603
    os2_table.sTypoAscender = 800
    os2_table.sTypoDescender = -200
    os2_table.sTypoLineGap = 0
    os2_table.usWinAscent = 800
    os2_table.usWinDescent = 200
    os2_table.usBreakChar = 0x20
    os2_table.usMaxContex = 2
    
    # 保存字体到文件
    output_path = "zero_width_font.ttf"
    font.save(output_path)
    print(f"Successfully generated {output_path}")
    
    # 验证生成的字体
    print("\nVerifying the generated font...")
    try:
        test_font = TTFont(output_path)
        print("Font verification successful!")
        
        # 检查字符映射
        if hasattr(test_font, 'getBestCmap'):
            cmap = test_font.getBestCmap()
            print("Character map entries:", cmap)
            
            if 0x2603 in cmap:
                print("✓ Snowman character (U+2603) is mapped to glyph:", cmap[0x2603])
                
                # 检查该字形的宽度
                if hasattr(test_font, 'getGlyphSet'):
                    glyph_set = test_font.getGlyphSet()
                    if cmap[0x2603] in glyph_set:
                        glyph = glyph_set[cmap[0x2603]]
                        if hasattr(glyph, 'width'):
                            print("✓ Glyph width:", glyph.width)
                            
                            if glyph.width == 0:
                                print("✓ Glyph is zero-width")
                            else:
                                print("⚠ Glyph is not zero-width")
                        else:
                            print("⚠ Cannot get glyph width")
                    else:
                        print("⚠ Glyph not found in glyph set")
            else:
                print("⚠ Snowman character not found in character map")
        else:
            print("⚠ Cannot get character map")
    except Exception as e:
        print(f"Font verification failed: {e}")

if __name__ == "__main__":
    main()
