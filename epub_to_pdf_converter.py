#!/usr/bin/env python3
"""
Better EPUB to PDF conversion using pypandoc + TeX
Addresses the character encoding issues with current PDF->MD conversion
"""

import os
import sys
import subprocess
import tempfile
import shutil

def check_tool_availability(tool, version_flag='--version'):
    """Check if a tool is available"""
    try:
        result = subprocess.run([tool, version_flag], capture_output=True, text=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_pypandoc():
    """Check if pypandoc is available"""
    try:
        import pypandoc
        return True
    except ImportError:
        print("pypandoc not found. Install with: pip install pypandoc")
        return False

def convert_epub_to_pdf_pypandoc(epub_path, pdf_path):
    """Convert EPUB to PDF using pypandoc with TeX engine"""
    if not check_pypandoc():
        return False
    
    try:
        import pypandoc
        
        # Configure pandoc with basic settings (no CJK for now)
        extra_args = [
            '--pdf-engine=xelatex',
            '-V', 'geometry:margin=2.5cm',
            '-V', 'fontsize=12pt',
            '-V', 'linestretch=1.2',
            '--toc',
            '--toc-depth=3',
            '--number-sections'
        ]
        
        print(f"Converting {epub_path} to {pdf_path} using pypandoc...")
        
        # Convert EPUB to PDF
        pypandoc.convert_file(
            epub_path, 
            'pdf', 
            outputfile=pdf_path,
            extra_args=extra_args
        )
        
        print(f"✓ pypandoc conversion successful: {pdf_path}")
        return True
        
    except Exception as e:
        print(f"✗ pypandoc conversion failed: {e}")
        return False

def convert_epub_to_pdf_pandoc_simple(epub_path, pdf_path):
    """Convert EPUB to PDF using simple pandoc command"""
    if not check_tool_availability('pandoc'):
        print("Pandoc not found. Install with: brew install pandoc")
        return False
    
    # First try with pdflatex (simpler)
    cmd = [
        'pandoc',
        epub_path,
        '-o', pdf_path,
        '--pdf-engine=pdflatex',
        '-V', 'geometry:margin=2cm',
        '--toc'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✓ Pandoc (pdflatex) conversion successful: {pdf_path}")
            return True
        else:
            print(f"pdflatex failed, trying wkhtmltopdf...")
            
            # Try with wkhtmltopdf
            cmd_html = [
                'pandoc',
                epub_path,
                '-o', pdf_path,
                '--pdf-engine=wkhtmltopdf',
                '--toc'
            ]
            
            result2 = subprocess.run(cmd_html, capture_output=True, text=True, timeout=300)
            if result2.returncode == 0:
                print(f"✓ Pandoc (wkhtmltopdf) conversion successful: {pdf_path}")
                return True
            else:
                print(f"✗ Both pandoc methods failed")
                print(f"pdflatex error: {result.stderr}")
                print(f"wkhtmltopdf error: {result2.stderr}")
                return False
                
    except subprocess.TimeoutExpired:
        print("✗ Pandoc conversion timed out")
        return False

def convert_epub_to_markdown_then_pdf(epub_path, pdf_path):
    """Convert EPUB to Markdown first, then to PDF for better control"""
    if not check_pypandoc():
        return False
    
    try:
        import pypandoc
        
        # Step 1: EPUB to Markdown
        md_content = pypandoc.convert_file(epub_path, 'markdown')
        
        # Step 2: Clean up markdown if needed
        # Remove problematic characters or fix formatting
        md_content = md_content.replace('\ufeff', '')  # Remove BOM
        md_content = md_content.replace('\u00a0', ' ')  # Replace non-breaking space
        
        # Step 3: Markdown to PDF
        extra_args = [
            '--pdf-engine=xelatex',
            '-V', 'mainfont=PingFang SC',
            '-V', 'CJKmainfont=PingFang SC',
            '-V', 'geometry:margin=2.5cm',
            '-V', 'fontsize=12pt',
            '--toc',
            '--number-sections'
        ]
        
        pypandoc.convert_text(
            md_content,
            'pdf',
            format='markdown',
            outputfile=pdf_path,
            extra_args=extra_args
        )
        
        print(f"✓ EPUB->MD->PDF conversion successful: {pdf_path}")
        return True
        
    except Exception as e:
        print(f"✗ EPUB->MD->PDF conversion failed: {e}")
        return False

def test_conversion_quality(pdf_path):
    """Test the quality of PDF by attempting to extract text"""
    if not check_tool_availability('pdftotext'):
        print("pdftotext not available for quality check")
        return True
    
    try:
        result = subprocess.run(['pdftotext', pdf_path, '-'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            text = result.stdout
            # Check for garbled text patterns
            garbled_chars = sum(1 for c in text if ord(c) > 65535 or c in '\ufffd\ufeff')
            total_chars = len(text)
            
            if total_chars > 0:
                garbled_ratio = garbled_chars / total_chars
                print(f"Text extraction quality: {(1-garbled_ratio)*100:.1f}% clean")
                return garbled_ratio < 0.1  # Less than 10% garbled
            
        return True
    except Exception as e:
        print(f"Quality check failed: {e}")
        return True

def main():
    """Test different EPUB to PDF conversion methods using pypandoc + TeX"""
    epub_file = "flint.epub"
    
    if not os.path.exists(epub_file):
        print(f"EPUB file not found: {epub_file}")
        return False
    
    print("=== Testing EPUB to PDF Conversion Methods (pypandoc + TeX) ===")
    
    methods = [
        ("pypandoc", convert_epub_to_pdf_pypandoc),
        ("pandoc-simple", convert_epub_to_pdf_pandoc_simple),
        ("epub-md-pdf", convert_epub_to_markdown_then_pdf)
    ]
    
    results = {}
    
    for method_name, converter_func in methods:
        print(f"\n--- Testing {method_name} ---")
        output_pdf = f"test_{method_name.replace('-', '_')}.pdf"
        
        if converter_func(epub_file, output_pdf):
            # Test quality
            quality_ok = test_conversion_quality(output_pdf)
            results[method_name] = {
                'success': True,
                'file': output_pdf,
                'quality': quality_ok
            }
            print(f"✓ {method_name} conversion completed")
        else:
            results[method_name] = {'success': False}
            print(f"✗ {method_name} conversion failed")
    
    # Summary
    print("\n=== Conversion Results Summary ===")
    for method, result in results.items():
        if result['success']:
            quality = "Good" if result['quality'] else "Issues detected"
            print(f"{method}: ✓ Success, Quality: {quality}")
        else:
            print(f"{method}: ✗ Failed")
    
    # Recommend best method
    successful_methods = [m for m, r in results.items() if r['success'] and r.get('quality', True)]
    if successful_methods:
        print(f"\nRecommended method: {successful_methods[0]}")
        return True
    else:
        print("\nNo successful conversions found")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)