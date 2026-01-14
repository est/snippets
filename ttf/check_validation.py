#!/usr/bin/env python3
import os
import tempfile
import subprocess
import sys
from validate_ttf import create_ttf_from_html, get_fonttools_path

def main():
    html_file = '/Users/me/edev/snippets/ttf/index.html'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ttf_path = os.path.join(tmpdir, "test_font.ttf")
        
        try:
            # Extract TTF file from HTML
            success = create_ttf_from_html(html_file, ttf_path)
            if not success:
                print("Failed to extract TTF file from HTML")
                return False
                
            print(f"Successfully extracted TTF file: {ttf_path}")
            print(f"File size: {os.path.getsize(ttf_path)} bytes")
            
            print("\nChecking TTF file structure:")
            with open(ttf_path, 'rb') as f:
                data = f.read()
                
            print(f"First 20 bytes: {data[:20].hex()}")
            print(f"Number of tables: {data[4] << 8 | data[5]}")
            
            # Look for maxp table offset
            print("\nTable records:")
            num_tables = data[4] << 8 | data[5]
            offset = 12
            for i in range(num_tables):
                tag = data[offset:offset+4]
                offset += 4
                checksum = int.from_bytes(data[offset:offset+4], 'big')
                offset += 4
                table_offset = int.from_bytes(data[offset:offset+4], 'big')
                offset += 4
                table_length = int.from_bytes(data[offset:offset+4], 'big')
                offset += 4
                print(f"{tag.decode(errors='replace')}: offset={table_offset}, length={table_length}")
                
                # Check if it's maxp table and print its content
                if tag == b'maxp':
                    print(f"  Maxp table: {data[table_offset:table_offset+table_length].hex()}")
                    print(f"  Table length: {table_length}")
                    
            return True
        except Exception as e:
            print(f"Error checking TTF file: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

if __name__ == "__main__":
    main()
