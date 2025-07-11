#!/usr/bin/env python3
"""
Step 2: Split original file into markdown by pages/chapters
Supports PDF, DOCX, and EPUB formats
"""

import os
import sys
from pathlib import Path
import re
import io
import json
import subprocess
from bs4 import BeautifulSoup
import shutil
import glob


def load_config(temp_dir):
    """Load configuration from config.txt in temp directory"""
    config_path = os.path.join(temp_dir, 'config.txt')
    config = {}
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config


def convert_to_pdf_calibre(input_file, output_file):
    """Convert EPUB/DOCX to PDF using Calibre's ebook-convert"""
    # Check if ebook-convert is available
    ebook_convert_paths = [
        'ebook-convert',  # In PATH
        '/Applications/calibre.app/Contents/MacOS/ebook-convert',  # macOS
        '/usr/bin/ebook-convert',  # Linux
        '/usr/local/bin/ebook-convert'  # Linux alternative
    ]
    
    ebook_convert_cmd = None
    for path in ebook_convert_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ebook_convert_cmd = path
                break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    if ebook_convert_cmd is None:
        raise Exception("ebook-convert not found. Please install Calibre:\n"
                       "  macOS: brew install --cask calibre\n"
                       "  Linux: sudo apt-get install calibre\n"
                       "  Windows: Download from https://calibre-ebook.com/download")
    
    # Get absolute paths
    input_abs = os.path.abspath(input_file)
    output_abs = os.path.abspath(output_file)
    
    # ebook-convert command
    cmd = [
        ebook_convert_cmd,
        input_abs,
        output_abs
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        
        if not os.path.exists(output_file):
            raise Exception("ebook-convert conversion failed - output file not created")
            
    except subprocess.TimeoutExpired:
        raise Exception("ebook-convert conversion timed out")
    except subprocess.CalledProcessError as e:
        raise Exception(f"ebook-convert conversion failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"ebook-convert error: {str(e)}")


def convert_to_pdf_libreoffice(input_file, output_file):
    """Convert DOCX/EPUB to PDF using LibreOffice (fallback)"""
    libreoffice_paths = [
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macOS
        '/usr/bin/libreoffice',  # Linux
        '/usr/local/bin/libreoffice',  # Linux alternative
        'libreoffice',  # In PATH
        'soffice'  # Alternative name
    ]
    
    libreoffice_cmd = None
    for path in libreoffice_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                libreoffice_cmd = path
                break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    if libreoffice_cmd is None:
        raise Exception("LibreOffice not found. Please install LibreOffice.")
    
    # Get absolute paths
    input_abs = os.path.abspath(input_file)
    output_dir = os.path.dirname(os.path.abspath(output_file))
    
    # LibreOffice command for conversion to PDF
    cmd = [
        libreoffice_cmd,
        '--headless',  # Run without GUI
        '--convert-to', 'pdf',  # Convert to PDF
        '--outdir', output_dir,  # Output directory
        input_abs  # Input file
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        
        # LibreOffice creates PDF with same name as input but .pdf extension
        input_name = os.path.splitext(os.path.basename(input_file))[0]
        generated_pdf = os.path.join(output_dir, f"{input_name}.pdf")
        
        # Rename to desired output name if different
        if generated_pdf != output_file:
            if os.path.exists(generated_pdf):
                os.rename(generated_pdf, output_file)
            else:
                raise Exception(f"LibreOffice conversion succeeded but output file not found: {generated_pdf}")
        
        if not os.path.exists(output_file):
            raise Exception("LibreOffice conversion failed - output file not created")
            
    except subprocess.TimeoutExpired:
        raise Exception("LibreOffice conversion timed out")
    except subprocess.CalledProcessError as e:
        raise Exception(f"LibreOffice conversion failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"LibreOffice conversion error: {str(e)}")


def pdf_to_html_with_pdftohtml(pdf_file, temp_dir):
    """Convert PDF to HTML using pdftohtml with default parameters"""
    print("working...")
    
    # Copy input file to temp directory as input.pdf (only if not already there)
    input_pdf = os.path.join(temp_dir, 'input.pdf')
    if os.path.abspath(pdf_file) != os.path.abspath(input_pdf):
        shutil.copy2(pdf_file, input_pdf)
        print(f"  Copied input file to: {input_pdf}")
    else:
        print(f"  Using existing input file: {input_pdf}")
    
    # Change to temp directory so output files are created there
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Use pdftohtml with -noframes and output as 'output'
        cmd = ['pdftohtml', '-noframes', 'input.pdf', 'output']
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Successfully converted PDF to HTML using pdftohtml")
        return 'output'  # Return base name as 'output'
    except FileNotFoundError:
        raise Exception("pdftohtml not found. Please install poppler-utils:\n"
                       "  macOS: brew install poppler\n"
                       "  Linux: sudo apt-get install poppler-utils\n"
                       "  Windows: Download from https://poppler.freedesktop.org/")
    except subprocess.CalledProcessError as e:
        raise Exception(f"pdftohtml conversion failed: {e.stderr}")
    finally:
        # Always change back to original directory
        os.chdir(original_cwd)


def organize_html_images(temp_dir, base_name):
    """Organize images from HTML conversion into media directory"""
    print("working...")
    
    media_dir = os.path.join(temp_dir, 'media')
    os.makedirs(media_dir, exist_ok=True)
    
    # pdftohtml creates images with pattern: output-001.png, output-002.png, etc.
    image_files = []
    
    # Get all image files and sort them for consistent naming
    all_files = []
    for file in os.listdir(temp_dir):
        if file.startswith(base_name) and file.endswith(('.png', '.jpg', '.jpeg')):
            all_files.append(file)
    
    # Sort files to ensure consistent ordering
    all_files.sort()
    
    for file in all_files:
        src_path = os.path.join(temp_dir, file)
        
        # Get file extension
        _, ext = os.path.splitext(file)
        
        # Replace prefix: output-1_1.jpg -> image-1_1.jpg
        new_filename = file.replace(base_name, 'image')
        dst_path = os.path.join(media_dir, new_filename)
        
        shutil.move(src_path, dst_path)
        image_files.append((file, new_filename))  # Store mapping for reference updates
        print(f"  Moved and renamed: {file} -> {new_filename}")
    
    return image_files


def split_html_by_pages(temp_dir, base_name, image_mapping=None):
    """Split HTML files by page markers into individual page HTML files"""
    print("working...")
    
    # pdftohtml with -noframes generates a single HTML file (e.g., output.html)
    # Look for the main content file
    main_html_file = None
    for file in os.listdir(temp_dir):
        if file.startswith(base_name) and file.endswith('.html'):
            if file == f'{base_name}.html':
                # This is the main HTML file
                main_html_file = file
                break
    
    if not main_html_file:
        # If no direct match, look for the largest HTML file
        html_files = [f for f in os.listdir(temp_dir) if f.startswith(base_name) and f.endswith('.html')]
        if html_files:
            main_html_file = max(html_files, key=lambda f: os.path.getsize(os.path.join(temp_dir, f)))
    
    if not main_html_file:
        raise Exception(f"No main HTML file found with base name: {base_name}")
    
    html_path = os.path.join(temp_dir, main_html_file)
    
    # Read the HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find page anchors (e.g., <a name="1"></a>)
    page_anchors = soup.find_all('a', {'name': True})
    
    if not page_anchors:
        # If no anchors found, treat the whole file as one page
        print("  No page anchors found, treating as single page")
        page_html_name = "page0001.html"
        page_html_path = os.path.join(temp_dir, page_html_name)
        
        # Fix image paths and write file
        fixed_content = fix_image_paths_in_html(content, base_name, image_mapping)
        with open(page_html_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"  Created: {page_html_name}")
        return [page_html_name]
    
    # Split by page anchors
    page_files = []
    for i, anchor in enumerate(page_anchors):
        page_num = int(anchor.get('name', '0'))
        page_html_name = f"page{page_num:04d}.html"
        page_html_path = os.path.join(temp_dir, page_html_name)
        
        # Extract content from this anchor to the next
        if i + 1 < len(page_anchors):
            next_anchor = page_anchors[i + 1]
            page_content = extract_content_between_anchors(anchor, next_anchor)
        else:
            # Last page - extract from anchor to end
            page_content = extract_content_from_anchor_to_end(anchor)
        
        # Create a complete HTML page
        page_html = create_complete_html_page(page_content, base_name, image_mapping)
        
        # Write page HTML file
        with open(page_html_path, 'w', encoding='utf-8') as f:
            f.write(page_html)
        
        page_files.append(page_html_name)
        print(f"  Created: {page_html_name}")
    
    # Keep original HTML files (don't delete them)
    print(f"  Preserved original HTML file: {main_html_file}")
    
    return page_files


def extract_content_between_anchors(start_anchor, end_anchor):
    """Extract HTML content between two anchors"""
    content = []
    current = start_anchor
    
    while current and current != end_anchor:
        if current.name:
            content.append(str(current))
        current = current.next_sibling
    
    return ''.join(content)


def extract_content_from_anchor_to_end(anchor):
    """Extract HTML content from anchor to end of document"""
    content = []
    current = anchor
    
    while current:
        if current.name:
            content.append(str(current))
        current = current.next_sibling
    
    return ''.join(content)


def create_complete_html_page(page_content, base_name, image_mapping=None):
    """Create a complete HTML page from page content"""
    # Fix image paths in the content
    fixed_content = fix_image_paths_in_html(page_content, base_name, image_mapping)
    
    # Create complete HTML page
    html_template = f'''<!DOCTYPE html>
<html>
<head>
<title>Page</title>
<meta charset="utf-8">
</head>
<body>
{fixed_content}
</body>
</html>'''
    
    return html_template


def fix_image_paths_in_html(content, base_name, image_mapping=None):
    """Fix image paths in HTML to point to media directory with new image names"""
    if image_mapping is None:
        # Fallback: just point to media directory with original names
        content = re.sub(r'src="([^"]*' + re.escape(base_name) + r'-\d+\.(png|jpg|jpeg))"', 
                         r'src="media/\1"', content)
    else:
        # Use image mapping to update to new filenames
        for old_filename, new_filename in image_mapping:
            old_pattern = re.escape(old_filename)
            content = re.sub(f'src="{old_pattern}"', f'src="media/{new_filename}"', content)
    
    return content


def convert_html_to_md_with_pandoc(temp_dir, page_files):
    """Convert HTML files to Markdown using pandoc"""
    print("working...")
    
    md_files = []
    for page_html in page_files:
        page_num = page_html.replace('page', '').replace('.html', '')
        md_filename = f"page{page_num}.md"
        
        html_path = os.path.join(temp_dir, page_html)
        md_path = os.path.join(temp_dir, md_filename)
        
        cmd = [
            'pandoc',
            html_path,
            '-f', 'html',
            '-t', 'markdown',
            '-o', md_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            md_files.append(md_filename)
            print(f"  Converted: {page_html} -> {md_filename}")
            
            # Keep HTML file (don't remove it)
            
        except FileNotFoundError:
            raise Exception("Pandoc not found. Please install pandoc:\n"
                           "  macOS: brew install pandoc\n"
                           "  Linux: sudo apt-get install pandoc\n"
                           "  Windows: Download from https://pandoc.org/installing.html")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Pandoc HTML to Markdown conversion failed: {e.stderr}")
    
    return md_files


def convert_html_to_md_direct(html_path, md_path):
    """Convert HTML file to Markdown using pandoc"""
    print("working...")
    
    cmd = [
        'pandoc',
        html_path,
        '-f', 'html',
        '-t', 'markdown',
        '-o', md_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Successfully converted HTML to Markdown")
    except FileNotFoundError:
        raise Exception("Pandoc not found. Please install pandoc:\n"
                       "  macOS: brew install pandoc\n"
                       "  Linux: sudo apt-get install pandoc\n"
                       "  Windows: Download from https://pandoc.org/installing.html")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Pandoc HTML to Markdown conversion failed: {e.stderr}")


def count_characters(text):
    """Count characters in text, considering Chinese characters as 2 units and English as 1 unit"""
    char_count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # Chinese characters
            char_count += 2
        elif char.isalpha():  # English letters
            char_count += 1
        # Skip whitespace, punctuation, and other characters for more accurate count
    return char_count


def estimate_combined_char_count(text):
    """Estimate total character count for Chinese + English mixed content"""
    # Remove markdown formatting for more accurate count
    import re
    # Remove markdown links, images, code blocks, etc.
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Remove images
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)   # Remove links
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Remove code blocks
    text = re.sub(r'`.*?`', '', text)  # Remove inline code
    text = re.sub(r'#+\s*', '', text)  # Remove headers
    text = re.sub(r'[*_]{1,2}(.*?)[*_]{1,2}', r'\1', text)  # Remove bold/italic
    
    return count_characters(text)


def split_md_by_separator_with_merge(md_path, temp_dir, target_min_chars=3000, target_max_chars=5000):
    """Split markdown file by separators and merge consecutive pages to reach target character count"""
    print("working...")
    print(f"Target character range: {target_min_chars:,} - {target_max_chars:,} characters")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by lines containing '----------'
    sections = re.split(r'^.*----------.*$', content, flags=re.MULTILINE)
    
    # Remove empty sections
    sections = [section.strip() for section in sections if section.strip()]
    
    print(f"Found {len(sections)} initial sections")
    
    # Merge sections based on character count
    merged_sections = []
    current_merged = ""
    current_char_count = 0
    
    for i, section in enumerate(sections):
        section_char_count = estimate_combined_char_count(section)
        print(f"  Section {i+1}: {section_char_count:,} characters")
        
        # If current section alone exceeds max, save it separately
        if section_char_count > target_max_chars:
            # Save current merged content if any
            if current_merged:
                merged_sections.append(current_merged)
                print(f"    -> Saved merged section: {current_char_count:,} characters")
                current_merged = ""
                current_char_count = 0
            
            # Save this large section separately
            merged_sections.append(section)
            print(f"    -> Saved large section separately: {section_char_count:,} characters")
            continue
        
        # Check if adding this section would exceed target_max_chars
        potential_count = current_char_count + section_char_count
        
        if current_merged and potential_count > target_max_chars:
            # Save current merged content
            merged_sections.append(current_merged)
            print(f"    -> Saved merged section: {current_char_count:,} characters")
            
            # Start new merged section with current section
            current_merged = section
            current_char_count = section_char_count
        else:
            # Add section to current merged content
            if current_merged:
                current_merged += "\n\n" + section
            else:
                current_merged = section
            current_char_count = potential_count
            print(f"    -> Added to merged section, total: {current_char_count:,} characters")
    
    # Don't forget the last merged section
    if current_merged:
        merged_sections.append(current_merged)
        print(f"    -> Saved final merged section: {current_char_count:,} characters")
    
    print(f"Created {len(merged_sections)} merged sections")
    
    # Save merged sections to files
    md_files = []
    for i, section in enumerate(merged_sections, 1):
        char_count = estimate_combined_char_count(section)
        page_filename = f"page{i:04d}.md"
        page_path = os.path.join(temp_dir, page_filename)
        
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(section)
        
        md_files.append(page_filename)
        print(f"  Created: {page_filename} ({char_count:,} characters)")
        
        # Warn if outside target range
        if char_count < target_min_chars:
            print(f"    ⚠️  Below target minimum ({target_min_chars:,} chars)")
        elif char_count > target_max_chars:
            print(f"    ⚠️  Above target maximum ({target_max_chars:,} chars)")
    
    return md_files


def fix_image_paths_in_md_files(temp_dir, md_files, image_mapping):
    """Fix image paths and names in split MD files"""
    print("working...")
    
    for md_file in md_files:
        md_path = os.path.join(temp_dir, md_file)
        
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix image paths using the mapping
        if image_mapping:
            for old_filename, new_filename in image_mapping:
                # Replace references to old image names with new ones in media directory
                old_pattern = re.escape(old_filename)
                content = re.sub(r'!\[([^\]]*)\]\(' + old_pattern + r'\)', f'![\\1](media/{new_filename})', content)
                content = re.sub(r'!\[([^\]]*)\]\(\./' + old_pattern + r'\)', f'![\\1](media/{new_filename})', content)
        
        # Also fix any remaining image references that might use the old base name
        content = re.sub(r'!\[([^\]]*)\]\(output-([^)]+)\)', r'![\1](media/image-\2)', content)
        content = re.sub(r'!\[([^\]]*)\]\(\./output-([^)]+)\)', r'![\1](media/image-\2)', content)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Fixed image paths in: {md_file}")


def split_pdf_to_md(input_file, temp_dir):
    """Split PDF file into markdown files"""
    print(f"Processing PDF file: {input_file}")
    
    try:
        # Step 1: Convert PDF to HTML using pdftohtml
        base_name = pdf_to_html_with_pdftohtml(input_file, temp_dir)
        
        # Step 2: Organize images into media directory and get mapping
        image_mapping = organize_html_images(temp_dir, base_name)
        
        # Step 3: Convert output.html to output.md using pandoc
        output_html = os.path.join(temp_dir, f"{base_name}.html")
        output_md = os.path.join(temp_dir, "output.md")
        convert_html_to_md_direct(output_html, output_md)
        
        # Step 4: Split output.md by "----------" lines
        md_files = split_md_by_separator_with_merge(output_md, temp_dir)
        
        # Step 5: Fix image paths and names in split MD files
        fix_image_paths_in_md_files(temp_dir, md_files, image_mapping)
        
        print(f"✓ PDF processing complete: {len(md_files)} pages created")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)


def split_docx_to_md(input_file, temp_dir):
    """Split DOCX file into markdown files"""
    print(f"Processing DOCX file: {input_file}")
    
    try:
        # Copy input file to temp directory as input.docx
        input_docx = os.path.join(temp_dir, 'input.docx')
        shutil.copy2(input_file, input_docx)
        print(f"  Copied input file to: {input_docx}")
        
        # Step 1: Convert DOCX to PDF using LibreOffice
        temp_pdf = os.path.join(temp_dir, 'input.pdf')
        print("Converting DOCX to PDF...")
        convert_to_pdf_libreoffice(input_docx, temp_pdf)
        print("✓ Successfully converted DOCX to PDF")
        
        # Step 2: Process the PDF using the same workflow
        base_name = pdf_to_html_with_pdftohtml(temp_pdf, temp_dir)
        
        # Step 3: Organize images into media directory and get mapping
        image_mapping = organize_html_images(temp_dir, base_name)
        
        # Step 4: Convert output.html to output.md using pandoc
        output_html = os.path.join(temp_dir, f"{base_name}.html")
        output_md = os.path.join(temp_dir, "output.md")
        convert_html_to_md_direct(output_html, output_md)
        
        # Step 5: Split output.md by "----------" lines
        md_files = split_md_by_separator_with_merge(output_md, temp_dir)
        
        # Step 6: Fix image paths and names in split MD files
        fix_image_paths_in_md_files(temp_dir, md_files, image_mapping)
        
        print(f"✓ DOCX processing complete: {len(md_files)} pages created")
        
    except Exception as e:
        print(f"Error processing DOCX: {e}")
        sys.exit(1)


def split_epub_to_md(input_file, temp_dir):
    """Split EPUB file into markdown files"""
    print(f"Processing EPUB file: {input_file}")
    
    try:
        # Copy input file to temp directory as input.epub
        input_epub = os.path.join(temp_dir, 'input.epub')
        shutil.copy2(input_file, input_epub)
        print(f"  Copied input file to: {input_epub}")
        
        # Step 1: Convert EPUB to PDF using Calibre (preferred) or LibreOffice (fallback)
        temp_pdf = os.path.join(temp_dir, 'input.pdf')
        print("Converting EPUB to PDF...")
        
        # Try Calibre first
        try:
            convert_to_pdf_calibre(input_epub, temp_pdf)
            print("✓ Successfully converted EPUB to PDF using Calibre")
        except Exception as e:
            print(f"Calibre conversion failed: {e}")
            print("Falling back to LibreOffice...")
            try:
                convert_to_pdf_libreoffice(input_epub, temp_pdf)
                print("✓ Successfully converted EPUB to PDF using LibreOffice")
            except Exception as e2:
                raise Exception(f"Both Calibre and LibreOffice conversion failed:\nCalibre: {e}\nLibreOffice: {e2}")
        
        # Step 2: Process the PDF using the same workflow
        base_name = pdf_to_html_with_pdftohtml(temp_pdf, temp_dir)
        
        # Step 3: Organize images into media directory and get mapping
        image_mapping = organize_html_images(temp_dir, base_name)
        
        # Step 4: Convert output.html to output.md using pandoc
        output_html = os.path.join(temp_dir, f"{base_name}.html")
        output_md = os.path.join(temp_dir, "output.md")
        convert_html_to_md_direct(output_html, output_md)
        
        # Step 5: Split output.md by "----------" lines
        md_files = split_md_by_separator_with_merge(output_md, temp_dir)
        
        # Step 6: Fix image paths and names in split MD files
        fix_image_paths_in_md_files(temp_dir, md_files, image_mapping)
        
        print(f"✓ EPUB processing complete: {len(md_files)} pages created")
        
    except Exception as e:
        print(f"Error processing EPUB: {e}")
        sys.exit(1)


def main():
    """Main function"""
    print("=== Book Translation Tool - Step 2: Split to Markdown ===")
    
    # Find temp directory
    temp_dirs = [d for d in os.listdir('.') if d.endswith('_temp')]
    if not temp_dirs:
        print("Error: No temp directory found. Run 01_prepare_env.py first.")
        sys.exit(1)
    
    # Use the most recently modified temp directory (likely the current one)
    temp_dir = max(temp_dirs, key=lambda d: os.path.getmtime(d))
    print(f"Using temp directory: {temp_dir}")
    
    # Load configuration
    config = load_config(temp_dir)
    
    input_file = config['input_file']
    file_ext = config['file_extension']
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Check if input.md already exists - skip conversion if it does
    input_md = os.path.join(temp_dir, 'input.md')
    if os.path.exists(input_md):
        print(f"✓ Skipping file conversion - input.md already exists")
        # Check if page files exist
        page_files = glob.glob(os.path.join(temp_dir, 'page*.md'))
        existing_pages = [f for f in page_files if not os.path.basename(f).startswith('output_')]
        if existing_pages:
            print(f"✓ Found {len(existing_pages)} existing page files, skipping split as well")
        else:
            print("✓ Splitting existing input.md into pages...")
            split_md_by_separator_with_merge(input_md, temp_dir)
        print("\n=== Step 2 Complete ===")
        print("Next step: Run 03_translate_md.py")
        return
    
    # Split based on file type
    if file_ext == '.pdf':
        split_pdf_to_md(input_file, temp_dir)
    elif file_ext == '.docx':
        split_docx_to_md(input_file, temp_dir)
    elif file_ext == '.epub':
        split_epub_to_md(input_file, temp_dir)
    else:
        print(f"Error: Unsupported file format: {file_ext}")
        sys.exit(1)
    
    print("\n=== Step 2 Complete ===")
    print("Next step: Run 03_translate_md.py")

if __name__ == "__main__":
    main()