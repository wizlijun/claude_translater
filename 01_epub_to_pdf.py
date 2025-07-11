#!/usr/bin/env python3
"""
01_epub_to_pdf.py - Convert EPUB to PDF using pypandoc + TeX
Updated to handle encoding issues and create quality PDFs
"""

import os
import sys
import subprocess
import tempfile
import shutil

def setup_tex_environment():
    """Setup TeX environment with proper PATH"""
    tex_path = "/usr/local/texlive/2025basic/bin/universal-darwin"
    if os.path.exists(tex_path):
        current_path = os.environ.get('PATH', '')
        if tex_path not in current_path:
            os.environ['PATH'] = f"{tex_path}:{current_path}"
        return True
    return False

def extract_epub_images(epub_path, output_dir):
    """Extract images from EPUB file"""
    try:
        import zipfile
        
        media_dir = os.path.join(output_dir, 'media')
        os.makedirs(media_dir, exist_ok=True)
        
        with zipfile.ZipFile(epub_path, 'r') as epub:
            # Find image files
            image_files = [f for f in epub.namelist() 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg'))]
            
            # Extract images
            extracted_count = 0
            for image_file in image_files:
                # Get just the filename
                filename = os.path.basename(image_file)
                if filename:  # Skip if empty filename
                    try:
                        with epub.open(image_file) as source:
                            target_path = os.path.join(media_dir, filename)
                            with open(target_path, 'wb') as target:
                                target.write(source.read())
                            extracted_count += 1
                    except Exception as e:
                        print(f"Warning: Could not extract {image_file}: {e}")
            
            print(f"✓ Extracted {extracted_count} images to {media_dir}")
            return media_dir if extracted_count > 0 else None
            
    except Exception as e:
        print(f"✗ Image extraction failed: {e}")
        return None

def convert_epub_to_pdf(epub_path, pdf_path):
    """Convert EPUB to PDF directly using pypandoc with image support"""
    try:
        import pypandoc
    except ImportError:
        print("Error: pypandoc not found. Install with: pip install pypandoc")
        return False
    
    if not setup_tex_environment():
        print("Error: TeX environment not found. Install BasicTeX with: brew install --cask basictex")
        return False
    
    try:
        print(f"Converting {epub_path} to {pdf_path}...")
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Step 1: Extract images from EPUB
            print("Step 1: Extracting images from EPUB...")
            media_dir = extract_epub_images(epub_path, temp_dir)
            
            # Step 2: Direct EPUB to PDF conversion with image support
            print("Step 2: Converting EPUB directly to PDF...")
            extra_args = [
                '--pdf-engine=xelatex',
                '--variable=geometry:margin=2.5cm',
                '--variable=fontsize:11pt',
                '--variable=documentclass:article',
                '--no-highlight',
                '--quiet'
            ]
            
            # Add resource path for images if we extracted any
            if media_dir:
                extra_args.extend(['--resource-path', temp_dir])
                extra_args.extend(['--extract-media', temp_dir])
            
            pypandoc.convert_file(
                epub_path,
                'pdf',
                outputfile=pdf_path,
                extra_args=extra_args
            )
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"✓ PDF conversion successful: {pdf_path} ({file_size} bytes)")
                return True
            else:
                print("✗ PDF file was not created")
                return False
                
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"✗ PDF conversion failed: {e}")
        return False

def main():
    """Main conversion function"""
    if len(sys.argv) != 3:
        print("Usage: python3 01_epub_to_pdf.py <input.epub> <output.pdf>")
        sys.exit(1)
    
    epub_file = sys.argv[1]
    pdf_file = sys.argv[2]
    
    if not os.path.exists(epub_file):
        print(f"Error: EPUB file not found: {epub_file}")
        sys.exit(1)
    
    print("=== EPUB to PDF Conversion ===")
    success = convert_epub_to_pdf(epub_file, pdf_file)
    
    if success:
        print(f"\n✓ Success! PDF created: {pdf_file}")
        print("You can now use this PDF with the existing translation pipeline.")
    else:
        print("\n✗ Conversion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()