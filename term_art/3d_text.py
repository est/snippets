import math
import time
import sys
import os

# Ensure you have run: pip install pyobjc-framework-Quartz
try:
    from Quartz import (
        CTFontCreateWithName, 
        CTFontGetGlyphsForCharacters,
        CTFontCreatePathForGlyph, 
        CGPathGetPathBoundingBox,
        CGPathContainsPoint, 
        CGPointMake
    )
except ImportError:
    print("Error: pyobjc-framework-Quartz not found.")
    print("Run: pip install pyobjc-framework-Quartz")
    sys.exit(1)

def get_3d_points(text, font_name="Arial-BoldMT", size=20):
    # CoreText Font Reference
    font = CTFontCreateWithName(font_name, size, None)
    
    points = []
    x_offset = 0
    
    for char in text:
        # Get Glyph ID
        success, glyphs = CTFontGetGlyphsForCharacters(font, char, None, 1)
        if not success:
            x_offset += size * 0.5
            continue
            
        # Get Glyph Vector Path
        path = CTFontCreatePathForGlyph(font, glyphs[0], None)
        
        if path:
            bbox = CGPathGetPathBoundingBox(path)
            res = 1.2  # Sampling density
            for ix in range(int(bbox.size.width * res)):
                for iy in range(int(bbox.size.height * res)):
                    px = bbox.origin.x + ix/res
                    py = bbox.origin.y + iy/res
                    # Check if pixel is inside the vector shape
                    if CGPathContainsPoint(path, None, CGPointMake(px, py), False):
                        # Extrude 5 layers deep for 3D effect
                        for z in range(5):
                            points.append([px + x_offset, py, z - 2.5])
            x_offset += bbox.size.width + 4
        else:
            x_offset += size * 0.5

    # Center the point cloud
    if points:
        for i in range(2):
            mid = (min(p[i] for p in points) + max(p[i] for p in points)) / 2
            for p in points: p[i] -= mid
            
    return points

def run_3d_terminal(text):
    points = get_3d_points(text)
    if not points: return

    ax, ay, az = 0, 0, 0
    # Hide cursor, Clear screen
    sys.stdout.write("\033[?25l\033[2J")
    
    try:
        while True:
            cols, rows = os.get_terminal_size()
            # Braille grid is 2x4 per cell
            bw, bh = cols * 2, (rows - 1) * 4
            grid = [0] * (bw * bh)
            
            # Precompute rotation trigonometry
            cx, sx = math.cos(ax), math.sin(ax)
            cy, sy = math.cos(ay), math.sin(ay)
            cz, sz = math.cos(az), math.sin(az)

            for x_p, y_p, z_p in points:
                # 3D Rotation Matrix Calculation
                y, z = y_p*cx - z_p*sx, y_p*sx + z_p*cx
                x, z = x_p*cy + z_p*sy, -x_p*sy + z_p*cy
                x, y = x*cz - y*sz, x*sz + y*cz

                # Perspective Projection + Terminal Aspect Correction
                dist = 80
                scale = 75 / (z + dist)
                px = int(bw / 2 + x * scale * 2.6)
                py = int(bh / 2 - y * scale)

                if 0 <= px < bw and 0 <= py < bh:
                    grid[py * bw + px] = 1

            # Convert bit-grid to Braille (U+2800 range)
            # Using \033[H (Cursor Home) to overwrite frame and eliminate flicker
            output = ["\033[H"]
            for y in range(0, bh, 4):
                line = []
                for x in range(0, bw, 2):
                    code = 0
                    # Braille dot weights
                    # 1   8
                    # 2  16
                    # 4  32
                    # 64 128
                    dots = [(0,0,1),(1,0,2),(2,0,4),(0,1,8),(1,1,16),(2,1,32),(3,0,64),(3,1,128)]
                    for dy, dx, bit in dots:
                        if grid[(y + dy) * bw + (x + dx)]:
                            code |= bit
                    line.append(chr(0x2800 + code))
                output.append("".join(line))
            
            sys.stdout.write("\n".join(output))
            sys.stdout.flush()

            ax += 0.04; ay += 0.07; az += 0.02
            time.sleep(0.015)

    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\n") # Restore cursor

if __name__ == "__main__":
    user_input = input("Enter Text: ") or "20th CENTURY FOX"
    run_3d_terminal(user_input)