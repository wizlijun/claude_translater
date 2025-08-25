#!/usr/bin/env python3
"""
HTML to DOCX converter using Calibre
Provides timeout protection and better error handling than pandoc-based solution
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
import signal

def timeout_handler(signum, frame):
    """Handle timeout signal"""
    raise TimeoutError("Conversion timed out")

def find_calibre_convert():
    """Find ebook-convert command from Calibre installation"""
    possible_paths = [
        "/Applications/calibre.app/Contents/MacOS/ebook-convert",
        "/usr/bin/ebook-convert", 
        "/usr/local/bin/ebook-convert",
        "ebook-convert"  # If in PATH
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ Found Calibre ebook-convert: {path}")
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    return None

def extract_html_metadata(html_file):
    """Extract title and author from HTML file"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        else:
            # Try h1 tag
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
            if h1_match:
                title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            else:
                title = os.path.splitext(os.path.basename(html_file))[0]
        
        # Extract author
        author_match = re.search(r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        if author_match:
            author = author_match.group(1).strip()
        else:
            author = "Unknown Author"
        
        return title, author
        
    except Exception as e:
        print(f"Warning: Could not extract metadata: {e}")
        return os.path.splitext(os.path.basename(html_file))[0], "Unknown Author"

def convert_html_to_docx_calibre(html_file, docx_file, timeout=600):
    """Convert HTML to DOCX using Calibre with timeout protection"""
    
    calibre_path = find_calibre_convert()
    if not calibre_path:
        raise RuntimeError("Calibre ebook-convert not found. Please install Calibre.")
    
    # Extract metadata
    title, author = extract_html_metadata(html_file)
    
    print(f"Converting HTML to DOCX using Calibre...")
    print(f"Title: {title}")
    print(f"Author: {author}")
    
    # Prepare Calibre command
    cmd = [
        calibre_path,
        html_file,
        docx_file,
        "--title", title,
        "--authors", author,
        "--language", "zh-CN",
        "--book-producer", "Claude Translator",
        "--preserve-cover-aspect-ratio",
        "--smarten-punctuation",
        "--disable-font-rescaling"
    ]
    
    try:
        # Set up timeout signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        print(f"Starting conversion (timeout: {timeout}s)...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        # Cancel timeout
        signal.alarm(0)
        
        if result.returncode == 0:
            if os.path.exists(docx_file):
                file_size = os.path.getsize(docx_file)
                print(f"✓ DOCX conversion successful: {docx_file} ({file_size} bytes)")
                return True
            else:
                print("✗ DOCX file was not created")
                return False
        else:
            print(f"✗ Calibre conversion failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Conversion timed out after {timeout} seconds")
        return False
    except TimeoutError:
        print(f"✗ Conversion timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"✗ Conversion error: {e}")
        return False
    finally:
        # Ensure timeout is cancelled
        signal.alarm(0)

def prepare_html_for_conversion(input_html, temp_dir):
    """Prepare HTML file for conversion with font styling"""
    
    # Create working copy
    work_html = os.path.join(temp_dir, "work.html")
    shutil.copy2(input_html, work_html)
    
    try:
        with open(work_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add font styling CSS
        font_css = """
<style>
body {
    font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif;
    font-size: 12pt;
    line-height: 1.6;
    text-decoration: none;
}
h1, h2, h3, h4, h5, h6 {
    font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif;
    font-weight: bold;
    text-decoration: none;
}
p {
    font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif;
    text-decoration: none;
}
a {
    text-decoration: none;
    color: inherit;
}
* {
    text-decoration: none !important;
}
</style>
"""
        
        # Insert CSS after <head> tag
        import re
        if re.search(r'<head[^>]*>', content, re.IGNORECASE):
            content = re.sub(r'(<head[^>]*>)', r'\1\n' + font_css, content, flags=re.IGNORECASE)
        else:
            # If no head tag, add one
            if '<html' in content.lower():
                content = re.sub(r'(<html[^>]*>)', r'\1\n<head>\n' + font_css + '\n</head>', content, flags=re.IGNORECASE)
            else:
                content = '<head>\n' + font_css + '\n</head>\n' + content
        
        # Remove underline attributes and clean up links
        content = re.sub(r'text-decoration\s*:\s*underline\s*;?', '', content, flags=re.IGNORECASE)
        content = re.sub(r'style\s*=\s*["\'][^"\']*text-decoration\s*:\s*underline[^"\']*["\']', '', content, flags=re.IGNORECASE)
        
        # Convert links to plain text while preserving content
        content = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', content, flags=re.IGNORECASE | re.DOTALL)
        
        with open(work_html, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ Added font styling and removed underlines from HTML")
        return work_html
        
    except Exception as e:
        print(f"Warning: Could not add font styling: {e}")
        return work_html

def copy_images_if_needed(html_file, temp_dir):
    """Copy images directory if it exists alongside HTML"""
    html_dir = os.path.dirname(html_file)
    images_dirs = ['media', 'images', 'image', 'pics']
    
    for img_dir_name in images_dirs:
        img_dir = os.path.join(html_dir, img_dir_name)
        if os.path.exists(img_dir):
            target_dir = os.path.join(temp_dir, img_dir_name)
            shutil.copytree(img_dir, target_dir, dirs_exist_ok=True)
            image_count = len([f for f in os.listdir(target_dir) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg'))])
            print(f"✓ Copied {image_count} images from {img_dir_name}/")
            return image_count
    
    print("ℹ No images directory found")
    return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert HTML to DOCX using Calibre')
    parser.add_argument('input_html', help='Input HTML file')
    parser.add_argument('output_docx', nargs='?', help='Output DOCX file (optional)')
    parser.add_argument('-t', '--timeout', type=int, default=600, 
                       help='Conversion timeout in seconds (default: 600)')
    
    args = parser.parse_args()
    
    input_html = args.input_html
    # Ensure output_docx is in the same directory as input_html
    if args.output_docx:
        output_docx = args.output_docx
    else:
        # Place output in the same directory as input HTML
        input_dir = os.path.dirname(os.path.abspath(input_html))
        base_name = os.path.splitext(os.path.basename(input_html))[0]
        output_docx = os.path.join(input_dir, base_name + '.docx')
    
    # Check input file
    if not os.path.exists(input_html):
        print(f"Error: Input file not found: {input_html}")
        sys.exit(1)
    
    print("=== HTML to DOCX Conversion (Calibre) ===")
    print(f"Input: {input_html}")
    print(f"Output: {output_docx}")
    print(f"Timeout: {args.timeout} seconds")
    print()
    
    try:
        # Create temp directory in the same directory as input HTML
        input_dir = os.path.dirname(os.path.abspath(input_html))
        base_name = os.path.splitext(os.path.basename(input_html))[0]
        temp_dir = os.path.join(input_dir, f"{base_name}_conversion_temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        print(f"Working directory: {temp_dir}")
        
        # Copy images if needed
        image_count = copy_images_if_needed(input_html, temp_dir)
        
        # Prepare HTML with styling
        work_html = prepare_html_for_conversion(input_html, temp_dir)
        
        # Convert to DOCX
        if convert_html_to_docx_calibre(work_html, output_docx, args.timeout):
            print("\n" + "="*50)
            print("✅ Conversion completed successfully!")
            print(f"📁 File: {output_docx}")
            
            if os.path.exists(output_docx):
                file_size = os.path.getsize(output_docx)
                print(f"💾 Size: {file_size:,} bytes")
            print(f"🖼️  Images: {image_count} files")
            print("🔤 Font: 仿宋体 (FangSong)")
        else:
            print("\n❌ Conversion failed!")
            sys.exit(1)
                
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()