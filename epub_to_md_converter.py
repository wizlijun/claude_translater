#!/usr/bin/env python3
"""
Better EPUB to MD conversion using EPUB->HTML->MD workflow
Avoids TeX dependencies and PDF encoding issues
"""

import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
import re

def check_pypandoc():
    """Check if pypandoc is available"""
    try:
        import pypandoc
        return True
    except ImportError:
        print("pypandoc not found. Install with: pip install pypandoc")
        return False

def extract_epub_to_html(epub_path, output_dir):
    """Extract EPUB and convert to clean HTML"""
    try:
        import pypandoc
        
        # Convert EPUB to HTML
        html_content = pypandoc.convert_file(epub_path, 'html')
        
        # Clean up HTML
        html_content = html_content.replace('\ufeff', '')  # Remove BOM
        html_content = html_content.replace('\u00a0', ' ')  # Replace non-breaking space
        
        # Save HTML file
        html_file = os.path.join(output_dir, 'book.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ EPUB to HTML conversion successful: {html_file}")
        return html_file
        
    except Exception as e:
        print(f"✗ EPUB to HTML conversion failed: {e}")
        return None

def convert_html_to_markdown(html_file, md_file):
    """Convert HTML to Markdown"""
    try:
        import pypandoc
        
        # Convert HTML to Markdown with image extraction
        output_dir = os.path.dirname(md_file)
        media_dir = os.path.join(output_dir, 'media')
        
        extra_args = [
            '--extract-media', media_dir,
            '--wrap=none',  # Don't wrap lines
            '--atx-headers'  # Use ATX-style headers
        ]
        
        pypandoc.convert_file(
            html_file,
            'markdown',
            outputfile=md_file,
            extra_args=extra_args
        )
        
        print(f"✓ HTML to Markdown conversion successful: {md_file}")
        
        # Check if media directory was created
        if os.path.exists(media_dir):
            media_files = os.listdir(media_dir)
            print(f"✓ Media directory created with {len(media_files)} files")
        
        return True
        
    except Exception as e:
        print(f"✗ HTML to Markdown conversion failed: {e}")
        return False

def extract_epub_images(epub_path, output_dir):
    """Extract images directly from EPUB file"""
    try:
        media_dir = os.path.join(output_dir, 'media')
        os.makedirs(media_dir, exist_ok=True)
        
        with zipfile.ZipFile(epub_path, 'r') as epub:
            # Find image files
            image_files = [f for f in epub.namelist() 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg'))]
            
            # Extract images
            for image_file in image_files:
                # Get just the filename
                filename = os.path.basename(image_file)
                if filename:  # Skip if empty filename
                    try:
                        with epub.open(image_file) as source:
                            target_path = os.path.join(media_dir, filename)
                            with open(target_path, 'wb') as target:
                                target.write(source.read())
                    except Exception as e:
                        print(f"Warning: Could not extract {image_file}: {e}")
            
            print(f"✓ Extracted {len(image_files)} images to {media_dir}")
            return media_dir
            
    except Exception as e:
        print(f"✗ Image extraction failed: {e}")
        return None

def clean_markdown_content(md_file):
    """Clean up markdown content for better readability"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean up common issues
        content = re.sub(r'\n{3,}', '\n\n', content)  # Reduce multiple newlines
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)  # Remove trailing spaces
        content = content.replace('\ufeff', '')  # Remove BOM
        content = content.replace('\u00a0', ' ')  # Replace non-breaking space
        
        # Fix image paths to point to media directory
        content = re.sub(r'!\[([^\]]*)\]\(images/([^)]+)\)', r'![\1](media/\2)', content)
        
        # Write cleaned content back
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Markdown content cleaned")
        return True
        
    except Exception as e:
        print(f"✗ Markdown cleaning failed: {e}")
        return False

def convert_epub_to_markdown_improved(epub_path, output_dir):
    """Convert EPUB to Markdown using improved workflow"""
    if not check_pypandoc():
        return False
    
    print(f"Converting {epub_path} to Markdown...")
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Extract images first
        extract_epub_images(epub_path, output_dir)
        
        # Step 2: Convert EPUB to HTML
        html_file = extract_epub_to_html(epub_path, output_dir)
        if not html_file:
            return False
        
        # Step 3: Convert HTML to Markdown
        md_file = os.path.join(output_dir, 'book.md')
        if not convert_html_to_markdown(html_file, md_file):
            return False
        
        # Step 4: Clean up markdown
        clean_markdown_content(md_file)
        
        # Check final result
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✓ Conversion completed successfully!")
            print(f"  Output: {md_file}")
            print(f"  Size: {len(content)} characters")
            print(f"  Lines: {len(content.splitlines())}")
            
            # Show preview
            lines = content.split('\n')[:10]
            print("Preview:")
            for line in lines:
                print(f"  {line[:80]}")
            
            return True
        else:
            print("✗ Markdown file was not created")
            return False
            
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False

def main():
    """Test EPUB to Markdown conversion"""
    epub_file = "flint.epub"
    output_dir = "flint_md_output"
    
    if not os.path.exists(epub_file):
        print(f"EPUB file not found: {epub_file}")
        return False
    
    print("=== EPUB to Markdown Conversion (No PDF needed) ===")
    
    success = convert_epub_to_markdown_improved(epub_file, output_dir)
    
    if success:
        print(f"\n✓ Success! Markdown files created in: {output_dir}")
        print("You can now use the existing translation pipeline on the .md file")
        return True
    else:
        print("\n✗ Conversion failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)