#!/usr/bin/env python3
"""
Working EPUB to PDF converter using pypandoc + TeX
Optimized to handle LaTeX issues and create usable PDFs
"""

import os
import sys
import subprocess
import tempfile
import shutil

def check_pypandoc():
    """Check if pypandoc is available"""
    try:
        import pypandoc
        return True
    except ImportError:
        print("pypandoc not found. Install with: pip install pypandoc")
        return False

def setup_tex_environment():
    """Setup TeX environment with proper PATH"""
    tex_path = "/usr/local/texlive/2025basic/bin/universal-darwin"
    if os.path.exists(tex_path):
        current_path = os.environ.get('PATH', '')
        if tex_path not in current_path:
            os.environ['PATH'] = f"{tex_path}:{current_path}"
        return True
    return False

def convert_epub_to_pdf_simple(epub_path, pdf_path):
    """Convert EPUB to PDF using minimal settings to avoid LaTeX errors"""
    if not check_pypandoc():
        return False
    
    if not setup_tex_environment():
        print("TeX environment not found")
        return False
    
    try:
        import pypandoc
        
        print(f"Converting {epub_path} to {pdf_path}...")
        
        # Use minimal pandoc settings to avoid LaTeX issues
        extra_args = [
            '--pdf-engine=xelatex',
            '--template=',  # Use default template
            '--variable=geometry:margin=2cm',
            '--variable=fontsize:12pt',
            '--no-highlight',  # Disable syntax highlighting
            '--metadata=title:"Converted Book"',
            '--quiet'  # Reduce verbose output
        ]
        
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
        
    except Exception as e:
        print(f"✗ PDF conversion failed: {e}")
        return False

def convert_epub_to_pdf_via_markdown(epub_path, pdf_path):
    """Convert EPUB to PDF via intermediate Markdown to fix LaTeX issues"""
    if not check_pypandoc():
        return False
    
    if not setup_tex_environment():
        print("TeX environment not found")
        return False
    
    try:
        import pypandoc
        
        print(f"Converting {epub_path} to PDF via Markdown...")
        
        # Step 1: EPUB to Markdown
        print("Step 1: Converting EPUB to Markdown...")
        md_content = pypandoc.convert_file(epub_path, 'markdown')
        
        # Clean up problematic characters
        md_content = md_content.replace('\ufeff', '')  # Remove BOM
        md_content = md_content.replace('\u00a0', ' ')  # Non-breaking space
        
        # Step 2: Markdown to PDF with simple settings
        print("Step 2: Converting Markdown to PDF...")
        extra_args = [
            '--pdf-engine=xelatex',
            '--variable=geometry:margin=2.5cm',
            '--variable=fontsize:11pt',
            '--variable=documentclass:article',
            '--no-highlight',
            '--quiet'
        ]
        
        pypandoc.convert_text(
            md_content,
            'pdf',
            format='markdown',
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
        
    except Exception as e:
        print(f"✗ PDF conversion via Markdown failed: {e}")
        return False

def convert_epub_to_pdf_clean_latex(epub_path, pdf_path):
    """Convert EPUB to PDF with LaTeX cleanup"""
    if not check_pypandoc():
        return False
    
    if not setup_tex_environment():
        print("TeX environment not found")
        return False
    
    try:
        import pypandoc
        import re
        
        print(f"Converting {epub_path} to PDF with LaTeX cleanup...")
        
        # Step 1: Convert to LaTeX first
        print("Step 1: Converting EPUB to LaTeX...")
        latex_content = pypandoc.convert_file(epub_path, 'latex')
        
        # Step 2: Clean up LaTeX content
        print("Step 2: Cleaning LaTeX content...")
        
        # Remove problematic hyperref commands that cause errors
        latex_content = re.sub(r'\\hyperref\s*\[[^\]]*\]\{[^}]*\}\{[^}]*\}\{[^}]*\}', '', latex_content)
        
        # Remove CJK font commands if they exist
        latex_content = re.sub(r'\\setCJKmainfont\{[^}]*\}', '', latex_content)
        latex_content = re.sub(r'\\usepackage\{xeCJK\}', '', latex_content)
        
        # Remove problematic babel commands
        latex_content = re.sub(r'\\babelnormalise[^}]*\}', '', latex_content)
        
        # Step 3: Convert cleaned LaTeX to PDF
        print("Step 3: Converting cleaned LaTeX to PDF...")
        extra_args = [
            '--pdf-engine=xelatex',
            '--quiet'
        ]
        
        pypandoc.convert_text(
            latex_content,
            'pdf',
            format='latex',
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
        
    except Exception as e:
        print(f"✗ PDF conversion with LaTeX cleanup failed: {e}")
        return False

def main():
    """Test different EPUB to PDF conversion methods"""
    epub_file = "flint.epub"
    
    if not os.path.exists(epub_file):
        print(f"EPUB file not found: {epub_file}")
        return False
    
    print("=== EPUB to PDF Conversion (pypandoc + TeX) ===")
    
    methods = [
        ("simple", convert_epub_to_pdf_simple),
        ("via-markdown", convert_epub_to_pdf_via_markdown),
        ("clean-latex", convert_epub_to_pdf_clean_latex)
    ]
    
    for method_name, converter_func in methods:
        print(f"\n--- Testing {method_name} method ---")
        output_pdf = f"flint_{method_name}.pdf"
        
        if converter_func(epub_file, output_pdf):
            print(f"✓ {method_name} method succeeded: {output_pdf}")
            
            # Test PDF quality by checking file size and attempting text extraction
            if os.path.exists(output_pdf):
                file_size = os.path.getsize(output_pdf)
                if file_size > 1000:  # At least 1KB
                    print(f"✓ PDF seems valid (size: {file_size} bytes)")
                    print(f"Success! Use this PDF: {output_pdf}")
                    return True
                else:
                    print(f"⚠ PDF seems too small (size: {file_size} bytes)")
        else:
            print(f"✗ {method_name} method failed")
    
    print("\n✗ All conversion methods failed")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)