#!/usr/bin/env python3
"""
Pandoc Document Converter
A comprehensive tool for document conversion, splitting, and merging using pandoc
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path
import re
import glob

def check_pandoc():
    """Check if pandoc is available"""
    try:
        result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True)
        print(f"Pandoc version: {result.stdout.split()[1]}")
        return True
    except FileNotFoundError:
        print("Error: pandoc is not installed. Please install pandoc first.")
        print("Visit: https://pandoc.org/installing.html")
        return False

def convert_document(input_file, output_file, input_format=None, output_format=None):
    """Convert document using pandoc"""
    print(f"Converting {input_file} to {output_file}...")
    
    cmd = ['pandoc', input_file, '-o', output_file]
    
    if input_format:
        cmd.extend(['-f', input_format])
    
    if output_format:
        cmd.extend(['-t', output_format])
    
    # Add useful options
    cmd.extend([
        '--standalone',
        '--self-contained'
    ])
    
    # Add media extraction if converting to markdown
    if output_format == 'markdown' or output_file.endswith('.md'):
        media_dir = os.path.dirname(output_file) or '.'
        cmd.extend(['--extract-media', media_dir])
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Successfully converted to {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Conversion failed: {e.stderr}")
        return False

def split_document(input_file, output_dir, split_by='page'):
    """Split document into smaller parts"""
    print(f"Splitting {input_file} by {split_by}...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # First convert to markdown
    temp_md = os.path.join(output_dir, 'temp_full.md')
    
    if not convert_document(input_file, temp_md, output_format='markdown'):
        return False
    
    # Read the markdown content
    with open(temp_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content based on criteria
    if split_by == 'page':
        parts = split_by_page_breaks(content)
    elif split_by == 'chapter':
        parts = split_by_chapters(content)
    elif split_by == 'section':
        parts = split_by_sections(content)
    else:
        parts = split_by_size(content, int(split_by))
    
    # Fix media paths in content before saving
    def fix_media_paths_in_parts(parts, output_dir):
        """Fix media paths in split parts"""
        import re
        
        def fix_path(match):
            full_path = match.group(1)
            
            # Extract just the image filename
            if '/media/media/' in full_path:
                filename = full_path.split('/media/media/')[-1]
            elif '/media/' in full_path:
                filename = full_path.split('/media/')[-1]
            else:
                filename = os.path.basename(full_path)
            
            return f'![](media/{filename})'
        
        def fix_path_with_desc(match):
            desc = match.group(1)
            full_path = match.group(2)
            
            if '/media/media/' in full_path:
                filename = full_path.split('/media/media/')[-1]
            elif '/media/' in full_path:
                filename = full_path.split('/media/')[-1]
            else:
                filename = os.path.basename(full_path)
            
            return f'![{desc}](media/{filename})'
        
        fixed_parts = []
        for part in parts:
            # Fix image paths
            part = re.sub(r'!\[\]\(([^)]+)\)', fix_path, part)
            part = re.sub(r'!\[([^]]*)\]\(([^)]+)\)', fix_path_with_desc, part)
            fixed_parts.append(part)
        
        return fixed_parts
    
    # Fix media paths in parts
    parts = fix_media_paths_in_parts(parts, output_dir)
    
    # Save split parts
    for i, part in enumerate(parts, 1):
        part_file = os.path.join(output_dir, f'part_{i:04d}.md')
        with open(part_file, 'w', encoding='utf-8') as f:
            f.write(f"# Part {i}\n\n{part.strip()}\n\n")
        print(f"  Created: part_{i:04d}.md")
    
    # Clean up temp file
    os.remove(temp_md)
    
    print(f"✓ Split into {len(parts)} parts")
    return True

def split_by_page_breaks(content):
    """Split content by page breaks"""
    # Split by horizontal rules, page breaks, or newpage commands
    parts = re.split(r'\n\s*---+\s*\n|\n\s*\\newpage\s*\n|\n\s*\\pagebreak\s*\n', content)
    
    # If no clear page breaks found, use estimated page size
    if len(parts) == 1:
        print("No page breaks found, using estimated page size...")
        return split_by_estimated_page_size(content)
    
    return [part.strip() for part in parts if part.strip()]

def split_by_chapters(content):
    """Split content by chapter headers"""
    # Split by main headers (# Header)
    parts = re.split(r'\n(?=# [^#])', content)
    return [part.strip() for part in parts if part.strip()]

def split_by_sections(content):
    """Split content by section headers"""
    # Split by section headers (## Header)
    parts = re.split(r'\n(?=## [^#])', content)
    return [part.strip() for part in parts if part.strip()]

def split_by_size(content, size):
    """Split content by character size"""
    parts = []
    for i in range(0, len(content), size):
        parts.append(content[i:i + size])
    return parts

def split_by_estimated_page_size(content):
    """Split content by estimated page size for better page simulation"""
    # Estimate characters per page (typical A4 page has ~3000-4000 chars)
    chars_per_page = 3500
    
    # Split by paragraphs first
    paragraphs = content.split('\n\n')
    
    pages = []
    current_page = ""
    current_length = 0
    
    for paragraph in paragraphs:
        para_length = len(paragraph)
        
        # If this paragraph contains a major heading, consider it a potential page break
        if paragraph.strip().startswith('# ') and current_page.strip():
            # Save current page if it has reasonable length
            if current_length > 1000:  # Minimum page length
                pages.append(current_page.strip())
                current_page = paragraph
                current_length = para_length
            else:
                # Add to current page if it's too short
                current_page += "\n\n" + paragraph
                current_length += para_length
        # If adding this paragraph would exceed page size, start new page
        elif current_length + para_length > chars_per_page and current_page.strip():
            pages.append(current_page.strip())
            current_page = paragraph
            current_length = para_length
        else:
            if current_page:
                current_page += "\n\n" + paragraph
            else:
                current_page = paragraph
            current_length += para_length
    
    # Add final page
    if current_page.strip():
        pages.append(current_page.strip())
    
    return pages

def merge_documents(input_pattern, output_file, separator='\n\n---\n\n'):
    """Merge multiple documents into one"""
    print(f"Merging documents matching '{input_pattern}'...")
    
    # Find all matching files
    files = glob.glob(input_pattern)
    files.sort()
    
    if not files:
        print(f"No files found matching pattern: {input_pattern}")
        return False
    
    print(f"Found {len(files)} files to merge")
    
    # Merge content
    merged_content = ""
    
    for i, file_path in enumerate(files):
        print(f"  Processing: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if content:
                if i > 0:
                    merged_content += separator
                merged_content += content + "\n\n"
        except Exception as e:
            print(f"    Error reading {file_path}: {e}")
            continue
    
    # Save merged content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"✓ Merged {len(files)} files into {output_file}")
    return True

def batch_convert(input_dir, output_dir, input_format, output_format):
    """Batch convert all files in a directory"""
    print(f"Batch converting {input_format} files to {output_format}...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all files with the input format
    pattern = os.path.join(input_dir, f'*.{input_format}')
    files = glob.glob(pattern)
    
    if not files:
        print(f"No {input_format} files found in {input_dir}")
        return False
    
    success_count = 0
    
    for file_path in files:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file = os.path.join(output_dir, f'{base_name}.{output_format}')
        
        if convert_document(file_path, output_file, input_format, output_format):
            success_count += 1
    
    print(f"✓ Successfully converted {success_count}/{len(files)} files")
    return success_count > 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Pandoc Document Converter')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert document format')
    convert_parser.add_argument('input', help='Input file')
    convert_parser.add_argument('output', help='Output file')
    convert_parser.add_argument('-f', '--from', dest='input_format', help='Input format')
    convert_parser.add_argument('-t', '--to', dest='output_format', help='Output format')
    
    # Split command
    split_parser = subparsers.add_parser('split', help='Split document into parts')
    split_parser.add_argument('input', help='Input file')
    split_parser.add_argument('output_dir', help='Output directory')
    split_parser.add_argument('--by', choices=['page', 'chapter', 'section'], 
                             default='page', help='Split by criteria')
    split_parser.add_argument('--size', type=int, help='Split by character size')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge multiple documents')
    merge_parser.add_argument('pattern', help='Input file pattern (e.g., "*.md")')
    merge_parser.add_argument('output', help='Output file')
    merge_parser.add_argument('--separator', default='\n\n---\n\n', 
                             help='Separator between merged files')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch convert files')
    batch_parser.add_argument('input_dir', help='Input directory')
    batch_parser.add_argument('output_dir', help='Output directory')
    batch_parser.add_argument('-f', '--from', dest='input_format', required=True,
                             help='Input format')
    batch_parser.add_argument('-t', '--to', dest='output_format', required=True,
                             help='Output format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Check if pandoc is available
    if not check_pandoc():
        sys.exit(1)
    
    # Execute command
    if args.command == 'convert':
        success = convert_document(args.input, args.output, 
                                 args.input_format, args.output_format)
    elif args.command == 'split':
        split_by = str(args.size) if args.size else args.by
        success = split_document(args.input, args.output_dir, split_by)
    elif args.command == 'merge':
        success = merge_documents(args.pattern, args.output, args.separator)
    elif args.command == 'batch':
        success = batch_convert(args.input_dir, args.output_dir, 
                               args.input_format, args.output_format)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()