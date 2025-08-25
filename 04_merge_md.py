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
    
    # Find all original pageXXXX.md files to check completeness
    original_files = glob.glob(os.path.join(temp_dir, 'page*.md'))
    original_files = [f for f in original_files if not os.path.basename(f).startswith('output_')]
    
    # Find all output_pageXXXX.md files
    output_files = glob.glob(os.path.join(temp_dir, 'output_page*.md'))
    
    if not output_files:
        print("Error: No translated markdown files found. Run 03_translate_md.py first.")
        sys.exit(1)
    
    # Check if translation is complete
    if len(output_files) < len(original_files):
        missing_count = len(original_files) - len(output_files)
        print(f"ERROR: Translation incomplete!")
        print(f"  Original pages: {len(original_files)}")
        print(f"  Translated pages: {len(output_files)}")
        print(f"  Missing translations: {missing_count}")
        print("\nPlease complete all page translations before merging.")
        print("Run the translation step again to complete missing pages.")
        sys.exit(1)
    
    # Sort files naturally (page0001, page0002, etc.)
    output_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    
    print(f"Found {len(output_files)} translated files to merge (complete set)")
    
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
        
    except Exception as e:
        print(f"Error saving merged file: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("=== Book Translation Tool - Step 4: Merge Markdown ===")
    
    # Find temp directory
    temp_dirs = [d for d in os.listdir('.') if d.endswith('_temp')]
    if not temp_dirs:
        print("Error: No temp directory found. Run 01_prepare_env.py first.")
        sys.exit(1)
    
    temp_dir = max(temp_dirs, key=lambda d: os.path.getmtime(d))
    print(f"Using temp directory: {temp_dir}")
    
    # Load configuration
    config = load_config(temp_dir)
    
    # Check if output.md already exists - skip if it does
    output_md = os.path.join(temp_dir, 'output.md')
    if os.path.exists(output_md):
        print(f"✓ Skipping merge - output.md already exists")
        print(f"  Found existing output.md: {output_md}")
        file_size = os.path.getsize(output_md)
        print(f"  File size: {file_size:,} bytes")
        print("\n=== Step 4 Complete ===")
        print("Next step: Run 05_md_to_html.py")
        return
    
    # Merge markdown files
    merge_markdown_files(temp_dir)
    
    print("\n=== Step 4 Complete ===")
    print("Next step: Run 05_md_to_html.py")

if __name__ == "__main__":
    main()