#!/usr/bin/env python3
"""
Clean markdown files by removing line breaks
"""

import os
import sys
import glob

def clean_markdown_content(content):
    """Remove all line breaks from markdown content"""
    
    # Simply remove all line breaks
    content = content.replace('\n', ' ')
    
    # Clean up multiple spaces
    content = ' '.join(content.split())
    
    return content

def clean_markdown_file(file_path):
    """Clean a single markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned_content = clean_markdown_content(content)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"✓ Cleaned: {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error cleaning {file_path}: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 clean_markdown.py <file_or_directory>")
        print("Examples:")
        print("  python3 clean_markdown.py book.md")
        print("  python3 clean_markdown.py temp_directory/")
        print("  python3 clean_markdown.py *.md")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # Handle different input types
    md_files = []
    
    if os.path.isfile(target) and target.endswith('.md'):
        md_files = [target]
    elif os.path.isdir(target):
        # Find all .md files in directory
        md_files = glob.glob(os.path.join(target, "*.md"))
        md_files.extend(glob.glob(os.path.join(target, "**/*.md"), recursive=True))
    elif '*' in target:
        # Handle glob patterns
        md_files = glob.glob(target)
    else:
        print(f"Error: '{target}' is not a valid file, directory, or pattern")
        sys.exit(1)
    
    if not md_files:
        print("No markdown files found")
        sys.exit(1)
    
    print(f"Found {len(md_files)} markdown files to clean:")
    for f in md_files:
        print(f"  {f}")
    
    print("\nCleaning files...")
    
    success_count = 0
    for md_file in md_files:
        if clean_markdown_file(md_file):
            success_count += 1
    
    print(f"\nCompleted: {success_count}/{len(md_files)} files cleaned successfully")

if __name__ == "__main__":
    main()