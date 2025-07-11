#!/usr/bin/env python3
"""
01_convert_to_htmlz.py - Convert PDF/DOCX/EPUB to HTMLZ using Calibre
Then extract and process HTML content for translation pipeline
"""

import os
import sys
import subprocess
import zipfile
import shutil
import tempfile
import argparse
import glob

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

def convert_to_htmlz(input_file, htmlz_file, calibre_path):
    """Convert input file to HTMLZ using Calibre"""
    try:
        print(f"Converting {input_file} to HTMLZ...")
        
        # Use basic conversion first, then add options if needed
        cmd = [
            calibre_path,
            input_file,
            htmlz_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            file_size = os.path.getsize(htmlz_file)
            print(f"✓ HTMLZ conversion successful: {htmlz_file} ({file_size} bytes)")
            return True
        else:
            print(f"✗ HTMLZ conversion failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ HTMLZ conversion timed out")
        return False
    except Exception as e:
        print(f"✗ HTMLZ conversion error: {e}")
        return False

def extract_metadata_from_htmlz(extract_dir):
    """Extract metadata from metadata.opf file in HTMLZ"""
    try:
        import xml.etree.ElementTree as ET
        
        # Look for metadata.opf file
        metadata_file = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() == 'metadata.opf':
                    metadata_file = os.path.join(root, file)
                    break
            if metadata_file:
                break
        
        if not metadata_file:
            print("ℹ No metadata.opf found in HTMLZ")
            return {}
        
        print(f"✓ Found metadata file: {metadata_file}")
        
        # Parse the OPF file
        tree = ET.parse(metadata_file)
        root = tree.getroot()
        
        # Define namespaces commonly used in OPF files
        namespaces = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/'
        }
        
        metadata = {}
        
        # Extract title
        title_elem = root.find('.//dc:title', namespaces)
        if title_elem is not None and title_elem.text:
            metadata['title'] = title_elem.text.strip()
            print(f"✓ Found title: {metadata['title']}")
        
        # Extract creator/author
        creator_elem = root.find('.//dc:creator', namespaces)
        if creator_elem is not None and creator_elem.text:
            metadata['creator'] = creator_elem.text.strip()
            print(f"✓ Found creator: {metadata['creator']}")
        
        # Extract publisher (optional)
        publisher_elem = root.find('.//dc:publisher', namespaces)
        if publisher_elem is not None and publisher_elem.text:
            metadata['publisher'] = publisher_elem.text.strip()
            print(f"✓ Found publisher: {metadata['publisher']}")
        
        # Extract language (optional)
        language_elem = root.find('.//dc:language', namespaces)
        if language_elem is not None and language_elem.text:
            metadata['language'] = language_elem.text.strip()
            print(f"✓ Found language: {metadata['language']}")
        
        return metadata
        
    except Exception as e:
        print(f"⚠️ Error extracting metadata: {e}")
        return {}

def extract_htmlz(htmlz_file, temp_dir):
    """Extract HTMLZ file and return paths to HTML and images"""
    try:
        print(f"Extracting HTMLZ file: {htmlz_file}")
        
        # HTMLZ is just a ZIP file
        with zipfile.ZipFile(htmlz_file, 'r') as zip_file:
            zip_file.extractall(temp_dir)
        
        # Find the main HTML file (usually index.html)
        html_file = None
        images_dir = None
        
        for root, dirs, files in os.walk(temp_dir):
            # Look for main HTML file
            for file in files:
                if file.lower() in ['index.html', 'index.htm']:
                    html_file = os.path.join(root, file)
                    break
            
            # Look for images directory
            for dir_name in dirs:
                if dir_name.lower() in ['images', 'image', 'pics', 'pictures']:
                    images_dir = os.path.join(root, dir_name)
                    break
        
        # If no index.html found, look for any HTML file
        if not html_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.html', '.htm')):
                        html_file = os.path.join(root, file)
                        break
                if html_file:
                    break
        
        if html_file:
            print(f"✓ Found HTML file: {html_file}")
        else:
            print("✗ No HTML file found in HTMLZ")
            return None, None
        
        if images_dir and os.path.exists(images_dir):
            image_count = len([f for f in os.listdir(images_dir) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg'))])
            print(f"✓ Found images directory with {image_count} images: {images_dir}")
        else:
            print("ℹ No images directory found")
        
        return html_file, images_dir
        
    except Exception as e:
        print(f"✗ Error extracting HTMLZ: {e}")
        return None, None

def setup_temp_directory(input_file, html_file, images_dir):
    """Setup temp directory with HTML and images"""
    try:
        # Create temp directory based on input filename
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        temp_dir = f"{base_name}_temp"
        
        # Create temp directory if it doesn't exist (don't remove existing files)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Copy HTML file as input.html (skip if already exists)
        input_html = os.path.join(temp_dir, "input.html")
        if os.path.exists(input_html):
            print(f"✓ Skipping HTML copy - input.html already exists")
        else:
            shutil.copy2(html_file, input_html)
            print(f"✓ Copied HTML to: {input_html}")
        
        # Copy images directory if it exists
        if images_dir and os.path.exists(images_dir):
            target_images_dir = os.path.join(temp_dir, "images")
            if os.path.exists(target_images_dir):
                print(f"✓ Skipping images copy - images directory already exists")
            else:
                shutil.copytree(images_dir, target_images_dir)
                print(f"✓ Copied images to: {target_images_dir}")
        
        print(f"✓ Temp directory setup complete: {temp_dir}")
        return temp_dir
        
    except Exception as e:
        print(f"✗ Error setting up temp directory: {e}")
        return None

def convert_html_to_markdown(html_file, md_file):
    """Convert HTML to Markdown using pandoc"""
    try:
        import pypandoc
        
        print(f"Converting HTML to Markdown...")
        
        # Convert HTML to Markdown
        pypandoc.convert_file(
            html_file,
            'markdown',
            outputfile=md_file,
            extra_args=['--wrap=none']  # Don't wrap lines
        )
        
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up the markdown
            content = content.replace('\ufeff', '')  # Remove BOM
            content = content.replace('\u00a0', ' ')  # Replace non-breaking space
            
            # Clean up Calibre-specific markers
            content = clean_calibre_markers(content)
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Markdown conversion successful: {md_file}")
            return True
        else:
            print("✗ Markdown file was not created")
            return False
            
    except ImportError:
        print("✗ pypandoc not found. Install with: pip install pypandoc")
        return False
    except Exception as e:
        print(f"✗ HTML to Markdown conversion failed: {e}")
        return False

def clean_calibre_markers(content):
    """Clean up Calibre-specific markers from markdown content"""
    import re
    
    print("Cleaning Calibre markers...")
    
    # 1. Remove all {.calibre...} markers
    content = re.sub(r'\{\.calibre[^}]*\}', '', content)
    
    # 2. Remove lines starting with :::
    # 3. Remove lines that contain only numbers (page numbers, etc.)
    # 4. Remove lines ending with .ct} or .cn}
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip lines starting with :::
        if stripped_line.startswith(':::'):
            continue
            
        # Skip lines that contain only numbers (and optional whitespace)
        if re.match(r'^\s*\d+\s*$', line):
            continue
            
        # Skip lines ending with .ct} or .cn}
        if stripped_line.endswith('.ct}') or stripped_line.endswith('.cn}'):
            continue
            
        cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    # Clean up multiple consecutive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    print("✓ Calibre markers cleaned")
    return content

def split_markdown_by_size(md_file, temp_dir, target_size=6000):
    """Split markdown into chunks by character count (5-8k each)"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Splitting markdown into chunks (target size: {target_size} chars)...")
        
        # Split by lines first
        lines = content.split('\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            # If adding this line would exceed target size and we have content
            if current_size + line_size > target_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        # Write chunks to files
        for i, chunk in enumerate(chunks, 1):
            chunk_file = os.path.join(temp_dir, f"page{i:04d}.md")
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk)
        
        print(f"✓ Split into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks, 1):
            chunk_file = os.path.join(temp_dir, f"page{i:04d}.md")
            print(f"  page{i:04d}.md: {len(chunk)} characters")
        
        return len(chunks)
        
    except Exception as e:
        print(f"✗ Error splitting markdown: {e}")
        return 0

def create_config_file(temp_dir, input_file, input_lang, output_lang, output_file, metadata=None):
    """Create config.txt file for the pipeline"""
    try:
        config_file = os.path.join(temp_dir, "config.txt")
        
        config_content = f"""# Translation Configuration
input_file={input_file}
input_lang={input_lang}
output_lang={output_lang}
output_file={output_file}
conversion_method=calibre_htmlz
"""
        
        # Add metadata if available
        if metadata:
            config_content += f"\n# Book Metadata\n"
            if 'title' in metadata:
                config_content += f"original_title={metadata['title']}\n"
            if 'creator' in metadata:
                config_content += f"creator={metadata['creator']}\n"
            if 'publisher' in metadata:
                config_content += f"publisher={metadata['publisher']}\n"
            if 'language' in metadata:
                config_content += f"source_language={metadata['language']}\n"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✓ Created config file: {config_file}")
        if metadata:
            print(f"✓ Cached metadata: title={metadata.get('title', 'N/A')}, creator={metadata.get('creator', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating config file: {e}")
        return False

def main():
    """Main conversion function"""
    parser = argparse.ArgumentParser(description="Convert PDF/DOCX/EPUB to markdown chunks via HTMLZ")
    parser.add_argument("input_file", help="Input file (PDF, DOCX, or EPUB)")
    parser.add_argument("-l", "--ilang", default="auto", help="Input language (default: auto)")
    parser.add_argument("--olang", default="zh", help="Output language (default: zh)")
    parser.add_argument("-o", "--output", default="output.html", help="Output file (default: output.html)")
    parser.add_argument("--chunk-size", type=int, default=6000, help="Target chunk size in characters (default: 6000)")
    
    args = parser.parse_args()
    
    input_file = args.input_file
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Check file extension
    file_ext = os.path.splitext(input_file)[1].lower()
    if file_ext not in ['.pdf', '.docx', '.epub']:
        print(f"Error: Unsupported file type: {file_ext}")
        print("Supported types: .pdf, .docx, .epub")
        sys.exit(1)
    
    print("=== File Conversion via Calibre HTMLZ ===")
    print(f"Input file: {input_file}")
    print(f"File type: {file_ext}")
    print(f"Target chunk size: {args.chunk_size} characters")
    print()
    
    # Find Calibre
    calibre_path = find_calibre_convert()
    if not calibre_path:
        print("Error: Calibre ebook-convert not found")
        print("Please install Calibre: https://calibre-ebook.com/")
        sys.exit(1)
    
    # Create temporary HTMLZ file
    htmlz_file = f"{os.path.splitext(input_file)[0]}.htmlz"
    
    try:
        # Check if input.html already exists in temp directory - skip entire conversion if it does
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        temp_dir = f"{base_name}_temp"
        input_html_path = os.path.join(temp_dir, "input.html")
        
        if os.path.exists(input_html_path):
            print(f"✓ Skipping HTMLZ conversion - input.html already exists: {input_html_path}")
            file_size = os.path.getsize(input_html_path)
            print(f"✓ Found existing input.html: {file_size} bytes")
            
            # Try to read existing metadata from config if available
            metadata = {}
            config_file = os.path.join(temp_dir, "config.txt")
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                if key == 'original_title':
                                    metadata['title'] = value
                                elif key == 'creator':
                                    metadata['creator'] = value
                                elif key == 'publisher':
                                    metadata['publisher'] = value
                                elif key == 'source_language':
                                    metadata['language'] = value
                    if metadata:
                        print(f"✓ Read cached metadata: title={metadata.get('title', 'N/A')}, creator={metadata.get('creator', 'N/A')}")
                except Exception as e:
                    print(f"⚠️ Could not read metadata from config: {e}")
            
            # Still need to check/create config and handle markdown splitting
            # Step 4: Convert HTML to Markdown (skip if input.md already exists)
            input_md = os.path.join(temp_dir, "input.md")
            
            if os.path.exists(input_md):
                print(f"✓ Skipping HTML to Markdown conversion - input.md already exists")
            else:
                if not convert_html_to_markdown(input_html_path, input_md):
                    sys.exit(1)
            
            # Step 5: Split markdown into chunks (skip if page files already exist)
            page_files = glob.glob(os.path.join(temp_dir, 'page*.md'))
            if page_files:
                chunk_count = len([f for f in page_files if not os.path.basename(f).startswith('output_')])
                print(f"✓ Skipping markdown splitting - found {chunk_count} existing page files")
            else:
                chunk_count = split_markdown_by_size(input_md, temp_dir, args.chunk_size)
                if chunk_count == 0:
                    sys.exit(1)
            
            # Step 6: Create config file
            create_config_file(temp_dir, input_file, args.ilang, args.olang, args.output, metadata)
            
            print("\n" + "="*50)
            print("✓ Conversion completed successfully!")
            print(f"✓ Temp directory: {temp_dir}")
            print(f"✓ Ready for translation pipeline")
            return
        
        # Step 1: Convert to HTMLZ
        if not convert_to_htmlz(input_file, htmlz_file, calibre_path):
            sys.exit(1)
        
        # Step 2: Extract HTMLZ
        with tempfile.TemporaryDirectory() as extract_dir:
            html_file, images_dir = extract_htmlz(htmlz_file, extract_dir)
            
            if not html_file:
                sys.exit(1)
            
            # Extract metadata from HTMLZ
            metadata = extract_metadata_from_htmlz(extract_dir)
            
            # Step 3: Setup temp directory
            temp_dir = setup_temp_directory(input_file, html_file, images_dir)
            if not temp_dir:
                sys.exit(1)
            
            # Step 4: Convert HTML to Markdown (skip if input.md already exists)
            input_html = os.path.join(temp_dir, "input.html")
            input_md = os.path.join(temp_dir, "input.md")
            
            if os.path.exists(input_md):
                print(f"✓ Skipping HTML to Markdown conversion - input.md already exists")
            else:
                if not convert_html_to_markdown(input_html, input_md):
                    sys.exit(1)
            
            # Step 5: Split markdown into chunks (skip if page files already exist)
            page_files = glob.glob(os.path.join(temp_dir, 'page*.md'))
            if page_files:
                chunk_count = len([f for f in page_files if not os.path.basename(f).startswith('output_')])
                print(f"✓ Skipping markdown splitting - found {chunk_count} existing page files")
            else:
                chunk_count = split_markdown_by_size(input_md, temp_dir, args.chunk_size)
                if chunk_count == 0:
                    sys.exit(1)
            
            # Step 6: Create config file
            create_config_file(temp_dir, input_file, args.ilang, args.olang, args.output, metadata)
            
            print("\n" + "="*50)
            print("✓ Conversion completed successfully!")
            print(f"✓ Temp directory: {temp_dir}")
            print(f"✓ Markdown chunks: {chunk_count} files")
            print(f"✓ Ready for translation pipeline")
            
            # Clean up HTMLZ file
            if os.path.exists(htmlz_file):
                os.remove(htmlz_file)
                print(f"✓ Cleaned up temporary file: {htmlz_file}")
    
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()