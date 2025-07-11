#!/usr/bin/env python3
"""
Step 4: Merge translated markdown files
Combines all output_pageXXXX.md files into output.md
"""

import os
import sys
import glob
import re
from pathlib import Path

def load_config(temp_dir):
    """Load configuration from step 1"""
    config_file = os.path.join(temp_dir, 'config.txt')
    if not os.path.exists(config_file):
        print("Error: config.txt not found. Run 01_prepare_env.py first.")
        sys.exit(1)
    
    config = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    
    return config

def natural_sort_key(text):
    """Natural sorting key for filenames with numbers"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', text)]

def merge_markdown_files(temp_dir):
    """Merge all translated markdown files"""
    print("Merging translated markdown files...")
    
    # Find all output_pageXXXX.md files
    output_files = glob.glob(os.path.join(temp_dir, 'output_page*.md'))
    
    if not output_files:
        print("Error: No translated markdown files found. Run 03_translate_md.py first.")
        sys.exit(1)
    
    # Sort files naturally (page0001, page0002, etc.)
    output_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    
    print(f"Found {len(output_files)} translated files to merge")
    
    # Merge content
    merged_content = ""
    
    for i, file_path in enumerate(output_files):
        filename = os.path.basename(file_path)
        print(f"  Processing: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if content:
                merged_content += content + "\n\n"
            else:
                print(f"    Warning: {filename} is empty")
        
        except Exception as e:
            print(f"    Error reading {filename}: {e}")
            continue
    
    # Save merged content
    output_file = os.path.join(temp_dir, 'output.md')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        
        print(f"Successfully merged {len(output_files)} files into output.md")
        
        # Show file size info
        file_size = os.path.getsize(output_file)
        print(f"Output file size: {file_size:,} bytes")
        
        # Try using pandoc to create additional output formats
        try_pandoc_merge(output_file, temp_dir)
        
    except Exception as e:
        print(f"Error saving merged file: {e}")
        sys.exit(1)

def try_pandoc_merge(md_file, temp_dir):
    """Create additional output formats starting with HTML"""
    print("Creating additional output formats...")
    
    import subprocess
    
    # First, create HTML file from markdown
    html_file = os.path.join(temp_dir, 'output.html')
    try:
        print("  Creating HTML file...")
        cmd = ['pandoc', md_file, '-o', html_file]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  Created HTML: {html_file}")
    except Exception as e:
        print(f"  HTML creation failed: {e}")
        return
    
    # Now create DOCX using html2docx.sh
    try:
        docx_file = os.path.join(temp_dir, 'output.docx')
        html2docx_script = './html2docx.sh'
        
        if os.path.exists(html2docx_script):
            print("  Converting HTML to DOCX...")
            cmd = [html2docx_script, html_file, docx_file]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  Created DOCX: {docx_file}")
        else:
            print("  html2docx.sh not found, skipping DOCX creation")
    except Exception as e:
        print(f"  DOCX creation failed: {e}")
    
    # Create EPUB using html2epub.sh
    try:
        epub_file = os.path.join(temp_dir, 'output.epub')
        html2epub_script = './html2epub.sh'
        
        if os.path.exists(html2epub_script):
            print("  Converting HTML to EPUB...")
            cmd = [html2epub_script, html_file, epub_file]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  Created EPUB: {epub_file}")
        else:
            print("  html2epub.sh not found, skipping EPUB creation")
    except Exception as e:
        print(f"  EPUB creation failed: {e}")
    
    # Try to create PDF output (optional)
    try:
        print("  Creating PDF file...")
        pdf_file = os.path.join(temp_dir, 'output.pdf')
        cmd = ['pandoc', md_file, '-o', pdf_file, '--pdf-engine=xelatex']
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  Created PDF: {pdf_file}")
    except:
        print("  PDF creation failed (xelatex may not be installed)")

def create_file_index(temp_dir):
    """Create an index of processed files for reference"""
    print("Creating file index...")
    
    # Find all original and translated files
    original_files = glob.glob(os.path.join(temp_dir, 'page*.md'))
    translated_files = glob.glob(os.path.join(temp_dir, 'output_page*.md'))
    
    original_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    translated_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    
    index_content = "# File Processing Index\n\n"
    index_content += f"Total original files: {len(original_files)}\n"
    index_content += f"Total translated files: {len(translated_files)}\n\n"
    
    index_content += "## File List\n\n"
    index_content += "| Original | Translated | Status |\n"
    index_content += "|----------|------------|--------|\n"
    
    # Create mapping of original to translated files
    original_map = {}
    for orig_file in original_files:
        base_name = os.path.basename(orig_file)
        translated_name = f"output_{base_name}"
        translated_path = os.path.join(temp_dir, translated_name)
        
        if os.path.exists(translated_path):
            status = "✓ Translated"
        else:
            status = "✗ Not translated"
        
        index_content += f"| {base_name} | {translated_name} | {status} |\n"
    
    # Save index
    index_file = os.path.join(temp_dir, 'file_index.md')
    
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"File index saved to: file_index.md")
        
    except Exception as e:
        print(f"Error saving file index: {e}")

def main():
    """Main function"""
    print("=== Book Translation Tool - Step 4: Merge Markdown ===")
    
    # Find temp directory
    temp_dirs = [d for d in os.listdir('.') if d.endswith('_temp')]
    if not temp_dirs:
        print("Error: No temp directory found. Run 01_prepare_env.py first.")
        sys.exit(1)
    
    temp_dir = temp_dirs[0]
    print(f"Using temp directory: {temp_dir}")
    
    # Load configuration
    config = load_config(temp_dir)
    
    # Merge markdown files
    merge_markdown_files(temp_dir)
    
    # Create file index
    create_file_index(temp_dir)
    
    print("\n=== Step 4 Complete ===")
    print("Next step: Run 05_md_to_html.py")

if __name__ == "__main__":
    main()