#!/usr/bin/env /Users/lambdaq/miniconda3/envs/py3/bin/python
"""
3D Rotating Text Renderer for macOS Terminal
Renders 3D rotating text similar to the "20th Century Fox" logo style.
"""

import sys
import time
import math
import argparse
import signal
from typing import List, Tuple, Optional


from AppKit import NSFont, NSBezierPath, NSString
from Quartz import (
    CGPathApply,
    kCGPathElementMoveToPoint, kCGPathElementAddLineToPoint, 
    kCGPathElementAddQuadCurveToPoint, kCGPathElementAddCurveToPoint, 
    kCGPathElementCloseSubpath
)
import CoreText
import objc


# Terminal control codes
CLEAR_SCREEN = "\033[2J"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
RESET_CURSOR = "\033[H"
ANSI_RESET = "\033[0m"

# Unicode block characters for sub-pixel rendering (8 levels)
BLOCKS = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
# Alternative: half blocks for finer control
HALF_BLOCKS = [" ", "▀", "▄", "█"]

# Global state for cleanup
running = True
terminal_size = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    running = False
    cleanup_terminal()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def cleanup_terminal():
    """Restore terminal state"""
    sys.stdout.write(SHOW_CURSOR)
    sys.stdout.write(RESET_CURSOR)
    sys.stdout.flush()


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal dimensions - uses conservative 80x24 by default"""
    # Use conservative dimensions (80x24) to avoid newline issues and ensure stable rendering
    return 80, 24


class Point3D:
    """3D point with transformation support"""
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
    
    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __mul__(self, scalar):
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def rotate_x(self, angle: float) -> 'Point3D':
        """Rotate around X axis"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Point3D(
            self.x,
            self.y * cos_a - self.z * sin_a,
            self.y * sin_a + self.z * cos_a
        )
    
    def rotate_y(self, angle: float) -> 'Point3D':
        """Rotate around Y axis"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Point3D(
            self.x * cos_a + self.z * sin_a,
            self.y,
            -self.x * sin_a + self.z * cos_a
        )
    
    def rotate_z(self, angle: float) -> 'Point3D':
        """Rotate around Z axis"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Point3D(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a,
            self.z
        )
    
    def rotate(self, angle_x: float, angle_y: float, angle_z: float) -> 'Point3D':
        """Apply all rotations (order: X, Y, Z)"""
        p = self.rotate_x(angle_x)
        p = p.rotate_y(angle_y)
        p = p.rotate_z(angle_z)
        return p


def get_font(font_name: str, size: float) -> Optional[object]:
    """Get NSFont from font name"""
    try:
        # Try to create font with name
        font = NSFont.fontWithName_size_(font_name, size)
        if font is None:
            # Fallback to system default
            font = NSFont.systemFontOfSize_(size)
        return font
    except Exception:
        # Fallback to system default
        try:
            font = NSFont.systemFontOfSize_(size)
            return font
        except:
            return None


class PathExtractor:
    """Helper class to extract points from CGPath"""
    def __init__(self):
        self.points = []
        self.current_point = None
    
    def callback(self, info, element):
        """Callback for CGPathApply to extract path points"""
        try:
            element_type = element.type
            
            if element_type == kCGPathElementMoveToPoint:
                if element.points:
                    pt = element.points[0]
                    self.current_point = (float(pt.x), float(pt.y))
                    self.points.append(self.current_point)
            elif element_type == kCGPathElementAddLineToPoint:
                if element.points:
                    pt = element.points[0]
                    self.current_point = (float(pt.x), float(pt.y))
                    self.points.append(self.current_point)
            elif element_type == kCGPathElementAddQuadCurveToPoint:
                # Approximate quadratic curve with line segments
                if self.current_point and element.points and len(element.points) >= 2:
                    p0 = self.current_point
                    p1 = (float(element.points[0].x), float(element.points[0].y))
                    p2 = (float(element.points[1].x), float(element.points[1].y))
                    # Sample curve
                    for t in range(1, 11):
                        t_val = t / 10.0
                        x = (1-t_val)**2 * p0[0] + 2*(1-t_val)*t_val * p1[0] + t_val**2 * p2[0]
                        y = (1-t_val)**2 * p0[1] + 2*(1-t_val)*t_val * p1[1] + t_val**2 * p2[1]
                        self.current_point = (x, y)
                        self.points.append(self.current_point)
            elif element_type == kCGPathElementAddCurveToPoint:
                # Approximate cubic curve with line segments
                if self.current_point and element.points and len(element.points) >= 3:
                    p0 = self.current_point
                    p1 = (float(element.points[0].x), float(element.points[0].y))
                    p2 = (float(element.points[1].x), float(element.points[1].y))
                    p3 = (float(element.points[2].x), float(element.points[2].y))
                    # Sample curve
                    for t in range(1, 11):
                        t_val = t / 10.0
                        x = (1-t_val)**3 * p0[0] + 3*(1-t_val)**2*t_val * p1[0] + 3*(1-t_val)*t_val**2 * p2[0] + t_val**3 * p3[0]
                        y = (1-t_val)**3 * p0[1] + 3*(1-t_val)**2*t_val * p1[1] + 3*(1-t_val)*t_val**2 * p2[1] + t_val**3 * p3[1]
                        self.current_point = (x, y)
                        self.points.append(self.current_point)
            elif element_type == kCGPathElementCloseSubpath:
                # Close path - connect back to first point if different
                if self.points and len(self.points) > 0:
                    first = self.points[0]
                    if self.current_point and self.current_point != first:
                        self.points.append(first)
                        self.current_point = first
        except Exception:
            pass


def get_glyph_outline(font: object, char: str, size: float, font_name: str = None) -> List[Tuple[float, float]]:
    """Extract glyph outline points from font using CoreText"""
    try:
        # Use provided font_name, or extract from NSFont
        if not font_name:
            try:
                # Try to get PostScript name (most reliable for CoreText)
                font_name = font.fontName()
                if not font_name:
                    font_name = font.familyName()
            except:
                pass
        
        if not font_name:
            font_name = "Helvetica"
        
        # Create CoreText font with the same size (use font name string directly)
        ct_font = CoreText.CTFontCreateWithName(font_name, size, None)
        if ct_font is None:
            # Try with family name if PostScript name failed
            try:
                family_name = font.familyName()
                if family_name:
                    ct_font = CoreText.CTFontCreateWithName(family_name, size, None)
            except:
                pass
        
        if ct_font is None:
            return []
        
        # Get glyph for character using CoreText (matches 3d_text.py pattern)
        # Pass the character string directly - CoreText handles the conversion
        success, glyphs = CoreText.CTFontGetGlyphsForCharacters(ct_font, char, None, 1)
        if not success:
            return []
        
        # glyphs is a tuple/array - get first element
        # Note: glyph 0 can be valid, so we only check if glyphs exists and has elements
        if not glyphs or len(glyphs) == 0:
            return []
        
        glyph_id = glyphs[0]
        
        # Create path for glyph
        cg_path = CoreText.CTFontCreatePathForGlyph(ct_font, glyph_id, None)
        if cg_path is None:
            return []
        
        # Extract path points
        extractor = PathExtractor()
        
        # Apply path extraction
        def path_callback(info, element):
            extractor.callback(info, element)
        
        CGPathApply(cg_path, None, path_callback)
        
        return extractor.points if extractor.points else []
    except Exception as e:
        # Return empty on error - uncomment for debugging
        # print(f"Error in get_glyph_outline for '{char}': {e}")
        return []


def extrude_2d_to_3d(points_2d: List[Tuple[float, float]], depth: float) -> List[List[Point3D]]:
    """Convert 2D outline to 3D mesh with extrusion"""
    if not points_2d:
        return []
    
    # Normalize points to center around origin
    if len(points_2d) == 0:
        return []
    
    # Find bounding box
    min_x = min(p[0] for p in points_2d)
    max_x = max(p[0] for p in points_2d)
    min_y = min(p[1] for p in points_2d)
    max_y = max(p[1] for p in points_2d)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # Normalize and scale
    width = max_x - min_x
    height = max_y - min_y
    scale = 1.0 / max(width, height) if max(width, height) > 0 else 1.0
    
    normalized_points = [
        ((p[0] - center_x) * scale, (p[1] - center_y) * scale)
        for p in points_2d
    ]
    
    # Create front face (z = 0)
    front_face = [Point3D(p[0], p[1], 0) for p in normalized_points]
    
    # Create back face (z = -depth)
    back_face = [Point3D(p[0], p[1], -depth) for p in normalized_points]
    
    # Create side faces connecting front and back
    mesh = []
    
    # Add front face
    mesh.append(front_face)
    
    # Add back face (reversed for proper winding)
    mesh.append(list(reversed(back_face)))
    
    # Add side faces
    for i in range(len(normalized_points)):
        next_i = (i + 1) % len(normalized_points)
        side_face = [
            front_face[i],
            front_face[next_i],
            back_face[next_i],
            back_face[i]
        ]
        mesh.append(side_face)
    
    return mesh


def project_3d_to_2d(point: Point3D, aspect_ratio: float, distance: float = 5.0) -> Tuple[float, float]:
    """Project 3D point to 2D with perspective and aspect ratio compensation"""
    # Simple perspective projection
    if point.z + distance <= 0:
        return (0, 0)  # Behind camera
    
    factor = distance / (distance + point.z)
    x = point.x * factor
    y = point.y * factor * aspect_ratio  # Compensate for terminal cell aspect ratio
    
    return (x, y)


def rasterize_glyph_outline(points: List[Tuple[float, float]], width: int, height: int, 
                           scale: float = 1.0) -> List[List[float]]:
    """Rasterize glyph outline to high-resolution bitmap for sub-pixel rendering"""
    # Create high-res buffer (sub-pixel resolution)
    sub_width = width * 2  # 2x for sub-pixel sampling
    sub_height = height * 2
    
    buffer = [[0.0 for _ in range(sub_width)] for _ in range(sub_height)]
    
    if not points:
        return buffer
    
    # Find bounding box
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    # Scale and center
    glyph_width = max_x - min_x
    glyph_height = max_y - min_y
    if glyph_width == 0 or glyph_height == 0:
        return buffer
    
    scale_x = (sub_width * 0.8) / glyph_width * scale
    scale_y = (sub_height * 0.8) / glyph_height * scale
    scale_factor = min(scale_x, scale_y)
    
    offset_x = sub_width / 2 - (min_x + max_x) / 2 * scale_factor
    offset_y = sub_height / 2 - (min_y + max_y) / 2 * scale_factor
    
    # Simple point-in-polygon for filling (scanline approach)
    # For now, use edge detection - mark edges
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        
        x1 = int(p1[0] * scale_factor + offset_x)
        y1 = int(p1[1] * scale_factor + offset_y)
        x2 = int(p2[0] * scale_factor + offset_x)
        y2 = int(p2[1] * scale_factor + offset_y)
        
        # Draw line
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            if 0 <= x < sub_width and 0 <= y < sub_height:
                buffer[y][x] = 1.0
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    # Fill interior using scanline
    for y in range(sub_height):
        inside = False
        for x in range(sub_width):
            if buffer[y][x] > 0.5:
                inside = not inside
            if inside:
                buffer[y][x] = 1.0
    
    return buffer


class DepthBuffer:
    """Depth buffer for 3D rendering"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.depth = [[-float('inf') for _ in range(width)] for _ in range(height)]
        self.color = [[" " for _ in range(width)] for _ in range(height)]
    
    def test_and_set(self, x: int, y: int, z: float, char: str):
        """Test depth and set pixel if closer"""
        if 0 <= x < self.width and 0 <= y < self.height:
            if z > self.depth[y][x]:
                self.depth[y][x] = z
                self.color[y][x] = char
                return True
        return False
    
    def clear(self):
        """Clear depth buffer"""
        for y in range(self.height):
            for x in range(self.width):
                self.depth[y][x] = -float('inf')
                self.color[y][x] = " "


def render_mesh_to_buffer(mesh: List[List[Point3D]], buffer: DepthBuffer, 
                          angle_x: float, angle_y: float, angle_z: float,
                          term_width: int, term_height: int, aspect_ratio: float):
    """Render 3D mesh to depth buffer"""
    # Character set for depth shading (9 levels)
    depth_chars = ["█", "▇", "▆", "▅", "▄", "▃", "▂", "▁", " "]
    
    for face in mesh:
        if len(face) < 3:
            continue
        
        # Transform all points
        transformed = [p.rotate(angle_x, angle_y, angle_z) for p in face]
        
        # Cull back faces (simple: check if face normal points away)
        # Calculate face normal (cross product of two edges)
        if len(transformed) >= 3:
            v1 = Point3D(
                transformed[1].x - transformed[0].x,
                transformed[1].y - transformed[0].y,
                transformed[1].z - transformed[0].z
            )
            v2 = Point3D(
                transformed[2].x - transformed[0].x,
                transformed[2].y - transformed[0].y,
                transformed[2].z - transformed[0].z
            )
            # Normal = v1 × v2
            normal_z = v1.x * v2.y - v1.y * v2.x
            # If normal points away from camera (negative z), skip
            if normal_z < 0:
                continue
        
        # Project to 2D
        projected = []
        for p in transformed:
            proj = project_3d_to_2d(p, aspect_ratio)
            if proj[0] == 0 and proj[1] == 0 and p.z <= -5.0:
                # Point is behind camera, skip
                continue
            projected.append(proj)
        
        if len(projected) < 3:
            continue
        
        # Calculate average depth for shading
        avg_z = sum(p.z for p in transformed) / len(transformed)
        
        # Choose character based on depth (normalize to -2 to 2 range)
        depth_range = 4.0  # -2 to 2
        normalized_z = (avg_z + 2.0) / depth_range  # 0 to 1
        depth_index = int(normalized_z * 8)  # 0 to 8
        depth_index = max(0, min(8, depth_index))
        char = depth_chars[depth_index]
        
        # Convert to screen coordinates
        # Map from [-1, 1] to [0, term_width/height]
        points_2d = []
        for p in projected:
            x = int((p[0] + 1.0) * term_width / 2.0)
            y = int((p[1] + 1.0) * term_height / 2.0)
            points_2d.append((x, y))
        
        # Draw edges
        for i in range(len(points_2d)):
            p1 = points_2d[i]
            p2 = points_2d[(i + 1) % len(points_2d)]
            draw_line(buffer, p1[0], p1[1], p2[0], p2[1], avg_z, char)
        
        # Fill polygon
        fill_polygon(buffer, points_2d, avg_z, char)


def draw_line(buffer: DepthBuffer, x1: int, y1: int, x2: int, y2: int, z: float, char: str):
    """Draw line in depth buffer using Bresenham's algorithm"""
    # Clamp coordinates to buffer bounds
    x1 = max(0, min(buffer.width - 1, x1))
    y1 = max(0, min(buffer.height - 1, y1))
    x2 = max(0, min(buffer.width - 1, x2))
    y2 = max(0, min(buffer.height - 1, y2))
    
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    x, y = x1, y1
    while True:
        buffer.test_and_set(x, y, z, char)
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def fill_polygon(buffer: DepthBuffer, points: List[Tuple[int, int]], z: float, char: str):
    """Fill polygon using scanline algorithm"""
    if len(points) < 3:
        return
    
    # Clamp points to buffer bounds
    clamped_points = [
        (max(0, min(buffer.width - 1, p[0])), max(0, min(buffer.height - 1, p[1])))
        for p in points
    ]
    
    min_y = max(0, min(p[1] for p in clamped_points))
    max_y = min(buffer.height - 1, max(p[1] for p in clamped_points))
    
    if min_y > max_y:
        return
    
    for y in range(min_y, max_y + 1):
        intersections = []
        for i in range(len(clamped_points)):
            p1 = clamped_points[i]
            p2 = clamped_points[(i + 1) % len(clamped_points)]
            
            # Handle edge cases for horizontal lines
            if p1[1] == p2[1]:
                if p1[1] == y:
                    # Horizontal edge - add both endpoints
                    intersections.extend([p1[0], p2[0]])
                continue
            
            # Check if scanline intersects this edge
            if (p1[1] <= y < p2[1]) or (p2[1] <= y < p1[1]):
                x = int(p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]))
                intersections.append(x)
        
        if not intersections:
            continue
        
        # Remove duplicates and sort
        intersections = sorted(set(intersections))
        
        # Fill between pairs of intersections
        for i in range(0, len(intersections) - 1, 2):
            start_x = max(0, min(buffer.width - 1, intersections[i]))
            end_x = max(0, min(buffer.width - 1, intersections[i + 1] if i + 1 < len(intersections) else intersections[i]))
            for x in range(start_x, end_x + 1):
                buffer.test_and_set(x, y, z, char)


def render_frame_to_string(buffer: DepthBuffer) -> str:
    """Convert depth buffer to terminal output string"""
    lines = []
    for y in range(buffer.height):
        line = "".join(buffer.color[y])
        lines.append(line)
    # Join without trailing newline to prevent scrolling
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="3D Rotating Text Renderer for macOS Terminal")
    parser.add_argument("--text", type=str, default="3D TEXT", help="Text to display")
    parser.add_argument("--font", type=str, default="Helvetica", help="Font name")
    parser.add_argument("--speed", type=float, default=1.0, help="Rotation speed multiplier")
    parser.add_argument("--depth", type=float, default=0.5, help="Extrusion depth")
    parser.add_argument("--size", type=float, default=100.0, help="Font size")
    parser.add_argument("--width", type=int, default=80, help="Terminal width (default: 80)")
    parser.add_argument("--height", type=int, default=24, help="Terminal height (default: 24)")
    parser.add_argument("--fixed-size", action="store_true", help="Use fixed dimensions instead of terminal size")
    
    args = parser.parse_args()
    
    # Initialize terminal
    global terminal_size
    if args.fixed_size:
        # Use fixed conservative dimensions
        term_width, term_height = args.width, args.height
        terminal_size = (term_width, term_height)
    else:
        terminal_size = get_terminal_size()
        term_width, term_height = terminal_size
    
    # Terminal aspect ratio (typically 2:1 height:width)
    aspect_ratio = 2.0
    
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write(CLEAR_SCREEN)
    sys.stdout.flush()
    
    # Load font
    font = get_font(args.font, args.size)
    if font is None:
        print("Error: Could not load font")
        cleanup_terminal()
        sys.exit(1)
    
    # Generate glyph outlines and create 3D meshes
    meshes = []
    char_spacing = 1.2
    current_x = 0.0
    
    for char in args.text:
        if char == " ":
            current_x += char_spacing * 0.5
            continue
        
        points_2d = get_glyph_outline(font, char, args.size, args.font)
        if points_2d:
            # Offset for character spacing
            offset_points = [(p[0] + current_x, p[1]) for p in points_2d]
            mesh = extrude_2d_to_3d(offset_points, args.depth)
            if mesh:
                meshes.append(mesh)
        
        # Advance position
        if points_2d:
            min_x = min(p[0] for p in points_2d)
            max_x = max(p[0] for p in points_2d)
            current_x += (max_x - min_x) * char_spacing
    
    if not meshes:
        print("Error: Could not generate text meshes")
        cleanup_terminal()
        sys.exit(1)
    
    # Animation loop
    angle_x = 0.0
    angle_y = 0.0
    angle_z = 0.0
    
    frame_time = 1.0 / 30.0  # 30 FPS
    rotation_speed = 0.02 * args.speed
    
    try:
        frame_count = 0
        while running:
            start_time = time.time()
            
            # Create depth buffer
            buffer = DepthBuffer(term_width, term_height)
            
            # Render all character meshes
            for mesh in meshes:
                try:
                    render_mesh_to_buffer(mesh, buffer, angle_x, angle_y, angle_z,
                                        term_width, term_height, aspect_ratio)
                except Exception:
                    # Skip problematic meshes
                    continue
            
            # Convert to string and render
            output = render_frame_to_string(buffer)
            
            # Anti-flicker: position cursor and output
            # Output exactly term_height lines without trailing newline to prevent scrolling
            sys.stdout.write(RESET_CURSOR)
            lines = output.split('\n')
            # Ensure we output exactly term_height lines
            for i in range(term_height):
                if i < len(lines):
                    sys.stdout.write(lines[i])
                else:
                    # Fill with empty lines if needed
                    sys.stdout.write('')
                # Clear to end of line
                sys.stdout.write('\033[K')
                # Add newline except for the last line to prevent scrolling
                if i < term_height - 1:
                    sys.stdout.write('\n')
            sys.stdout.flush()
            
            # Update angles (wrap to prevent overflow)
            angle_x = (angle_x + rotation_speed) % (2 * math.pi)
            angle_y = (angle_y + rotation_speed * 1.1) % (2 * math.pi)
            angle_z = (angle_z + rotation_speed * 0.9) % (2 * math.pi)
            
            # Frame rate control
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Check terminal size change (every 30 frames to avoid overhead)
            frame_count += 1
            if frame_count % 30 == 0:
                new_size = get_terminal_size()
                if new_size != terminal_size:
                    terminal_size = new_size
                    term_width, term_height = terminal_size
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Print error and cleanup
        cleanup_terminal()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cleanup_terminal()


if __name__ == "__main__":
    main()
