#!/usr/bin/env python3
"""
HTML Publisher using Calibre
Unified script to convert HTML to DOCX, EPUB, and PDF formats
Usage: calibre_html_publish.py input.html -o output.docx/epub/pdf
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
import signal
import re

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
    images_dirs = ['images', 'media', 'image', 'pics']
    
    total_image_count = 0
    
    # Copy all image directories found
    for img_dir_name in images_dirs:
        img_dir = os.path.join(html_dir, img_dir_name)
        if os.path.exists(img_dir):
            target_dir = os.path.join(temp_dir, img_dir_name)
            try:
                shutil.copytree(img_dir, target_dir, dirs_exist_ok=True)
                image_count = len([f for f in os.listdir(target_dir) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp'))])
                print(f"✓ Copied {image_count} images from {img_dir_name}/")
                total_image_count += image_count
            except Exception as e:
                print(f"Warning: Could not copy {img_dir_name}/: {e}")
    
    # Also copy any loose image files in the HTML directory
    try:
        for file in os.listdir(html_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp')):
                src_file = os.path.join(html_dir, file)
                dst_file = os.path.join(temp_dir, file)
                shutil.copy2(src_file, dst_file)
                total_image_count += 1
                print(f"✓ Copied loose image file: {file}")
    except Exception as e:
        print(f"Warning: Could not copy loose image files: {e}")
    
    if total_image_count == 0:
        print("ℹ No images found")
    else:
        print(f"✓ Total images copied: {total_image_count}")
    
    return total_image_count

def get_output_format(output_file):
    """Determine output format from file extension"""
    ext = os.path.splitext(output_file)[1].lower()
    format_map = {
        '.docx': 'docx',
        '.epub': 'epub',
        '.pdf': 'pdf'
    }
    return format_map.get(ext)

def convert_html_with_calibre(html_file, output_file, format_type, timeout=600):
    """Convert HTML to specified format using Calibre with timeout protection"""
    
    calibre_path = find_calibre_convert()
    if not calibre_path:
        raise RuntimeError("Calibre ebook-convert not found. Please install Calibre.")
    
    # Extract metadata
    title, author = extract_html_metadata(html_file)
    
    print(f"Converting HTML to {format_type.upper()} using Calibre...")
    print(f"Title: {title}")
    print(f"Author: {author}")
    
    # Prepare Calibre command
    cmd = [
        calibre_path,
        html_file,
        output_file,
        "--title", title,
        "--authors", author,
        "--language", "zh-CN",
        "--book-producer", "Claude Translator",
        "--preserve-cover-aspect-ratio",
        "--smarten-punctuation"
    ]
    
    # Add format-specific options
    if format_type == 'docx':
        cmd.extend([
            "--disable-font-rescaling"
        ])
    elif format_type == 'epub':
        cmd.extend([
            "--epub-version", "3"
        ])
    elif format_type == 'pdf':
        cmd.extend([
            "--pdf-page-numbers",
            "--pdf-serif-family", "FangSong",
            "--pdf-sans-family", "FangSong",
            "--pdf-mono-family", "FangSong",
            "--pdf-default-font-size", "12",
            "--pdf-mono-font-size", "12"
        ])
    
    try:
        # Set up timeout signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        print(f"Starting conversion (timeout: {timeout}s)...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        # Cancel timeout
        signal.alarm(0)
        
        if result.returncode == 0:
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✓ {format_type.upper()} conversion successful: {output_file} ({file_size} bytes)")
                return True
            else:
                print(f"✗ {format_type.upper()} file was not created")
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert HTML to DOCX/EPUB/PDF using Calibre')
    parser.add_argument('input_html', help='Input HTML file')
    parser.add_argument('-o', '--output', required=True, help='Output file (.docx, .epub, or .pdf)')
    parser.add_argument('-t', '--timeout', type=int, default=600, 
                       help='Conversion timeout in seconds (default: 600)')
    
    args = parser.parse_args()
    
    input_html = args.input_html
    output_file = args.output
    
    # Check input file
    if not os.path.exists(input_html):
        print(f"Error: Input file not found: {input_html}")
        sys.exit(1)
    
    # Determine output format
    format_type = get_output_format(output_file)
    if not format_type:
        print(f"Error: Unsupported output format. Use .docx, .epub, or .pdf")
        sys.exit(1)
    
    # Always use the exact output path provided - 07_generate_formats.py already handles base_temp logic
    final_output = os.path.abspath(output_file)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(final_output)
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== HTML Publisher (Calibre) ===")
    print(f"Input: {input_html}")
    print(f"Output: {final_output}")
    print(f"Format: {format_type.upper()}")
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
        
        # Convert to specified format
        if convert_html_with_calibre(work_html, final_output, format_type, args.timeout):
            print("\n" + "="*50)
            print(f"✅ Conversion completed successfully!")
            print(f"📁 File: {final_output}")
            
            # Copy images directory to the final output directory if they exist in temp
            image_count = 0
            if os.path.exists(temp_dir):
                output_dir = os.path.dirname(final_output)
                images_dirs = ['images', 'media', 'image', 'pics']
                
                for img_dir_name in images_dirs:
                    temp_img_dir = os.path.join(temp_dir, img_dir_name)
                    if os.path.exists(temp_img_dir):
                        target_img_dir = os.path.join(output_dir, img_dir_name)
                        try:
                            if os.path.exists(target_img_dir):
                                shutil.rmtree(target_img_dir)
                            shutil.copytree(temp_img_dir, target_img_dir)
                            img_count = len([f for f in os.listdir(target_img_dir) 
                                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp'))])
                            print(f"✓ Copied {img_count} images from {img_dir_name}/ directory to output location")
                            image_count += img_count
                        except Exception as e:
                            print(f"Warning: Could not copy {img_dir_name}/ to output: {e}")
                
                # Also copy loose image files
                try:
                    for file in os.listdir(temp_dir):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp')):
                            src_file = os.path.join(temp_dir, file)
                            dst_file = os.path.join(output_dir, file)
                            shutil.copy2(src_file, dst_file)
                            image_count += 1
                            print(f"✓ Copied loose image file: {file}")
                except Exception as e:
                    print(f"Warning: Could not copy loose images to output: {e}")
            
            if os.path.exists(final_output):
                file_size = os.path.getsize(final_output)
                print(f"💾 Size: {file_size:,} bytes")
            print(f"🖼️  Images: {image_count} files")
            print("🔤 Font: 仿宋体 (FangSong)")
        else:
            print(f"\n❌ Conversion to {format_type.upper()} failed!")
            sys.exit(1)
        
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")
                
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()