#!/usr/bin/env python3
"""
Test the new PDF -> HTML -> Markdown conversion workflow
"""

import os
import sys
import subprocess
import tempfile
import shutil

def test_pdftohtml_availability():
    """Test if pdftohtml is available"""
    try:
        result = subprocess.run(['pdftohtml', '-v'], capture_output=True, text=True, timeout=10)
        print("✓ pdftohtml is available")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("✗ pdftohtml not found. Please install poppler-utils:")
        print("  macOS: brew install poppler")
        print("  Linux: sudo apt-get install poppler-utils")
        return False

def test_pandoc_availability():
    """Test if pandoc is available"""
    try:
        result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True, timeout=10)
        print("✓ pandoc is available")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("✗ pandoc not found. Please install pandoc:")
        print("  macOS: brew install pandoc")
        print("  Linux: sudo apt-get install pandoc")
        return False

def test_pdf_to_html_conversion():
    """Test PDF to HTML conversion"""
    input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.pdf")
    
    if not os.path.exists(input_file):
        print(f"✗ Test PDF file not found: {input_file}")
        return False
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_html = os.path.join(temp_dir, "test.html")
        
        print(f"Testing PDF to HTML conversion...")
        
        # Test pdftohtml command
        cmd = [
            'pdftohtml',
            '-s',  # Single HTML file
            '-fmt', 'html',
            '-zoom', '1.0',
            input_file,
            temp_html
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print("✓ PDF to HTML conversion successful")
                
                # Check if HTML file was created (pdftohtml creates different naming patterns)
                actual_html_file = temp_html
                if not os.path.exists(actual_html_file):
                    # Try different naming patterns
                    base_name = temp_html.replace('.html', '') if temp_html.endswith('.html') else temp_html
                    possible_names = [
                        base_name + 's.html',  # Common pattern
                        base_name + '.html',
                        base_name + '-html.html'
                    ]
                    for name in possible_names:
                        if os.path.exists(name):
                            actual_html_file = name
                            break
                
                if os.path.exists(actual_html_file):
                    with open(actual_html_file, 'r', encoding='utf-8', errors='ignore') as f:
                        html_content = f.read()
                    
                    print(f"✓ HTML file created ({len(html_content)} characters)")
                    
                    # Show first few lines of HTML
                    lines = html_content.split('\n')[:5]
                    print("HTML preview:")
                    for line in lines:
                        print(f"  {line[:80]}...")
                    
                    return True
                else:
                    print("✗ HTML file was not created")
                    return False
            else:
                print(f"✗ pdftohtml failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ PDF to HTML conversion timed out")
            return False
        except Exception as e:
            print(f"✗ PDF to HTML conversion error: {e}")
            return False

def test_html_to_markdown_conversion():
    """Test HTML to Markdown conversion"""
    input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.pdf")
    
    if not os.path.exists(input_file):
        print(f"✗ Test PDF file not found: {input_file}")
        return False
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_html = os.path.join(temp_dir, "test.html")
        temp_md = os.path.join(temp_dir, "test.md")
        media_dir = os.path.join(temp_dir, "media")
        
        print(f"Testing complete PDF -> HTML -> Markdown workflow...")
        
        # Step 1: PDF to HTML
        cmd1 = [
            'pdftohtml',
            '-s',
            '-fmt', 'html',
            '-zoom', '1.0',
            input_file,
            temp_html
        ]
        
        try:
            result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=120)
            if result1.returncode != 0:
                print(f"✗ PDF to HTML failed: {result1.stderr}")
                return False
            
            print("✓ Step 1: PDF to HTML successful")
            
            # Find the actual HTML file created
            actual_html_file = temp_html
            if not os.path.exists(actual_html_file):
                # Try different naming patterns
                base_name = temp_html.replace('.html', '') if temp_html.endswith('.html') else temp_html
                possible_names = [
                    base_name + 's.html',  # Common pattern
                    base_name + '.html',
                    base_name + '-html.html'
                ]
                for name in possible_names:
                    if os.path.exists(name):
                        actual_html_file = name
                        break
            
            # Step 2: HTML to Markdown
            cmd2 = [
                'pandoc',
                actual_html_file,
                '-f', 'html',
                '-t', 'markdown',
                '-o', temp_md,
                '--extract-media', media_dir
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
            if result2.returncode != 0:
                print(f"✗ HTML to Markdown failed: {result2.stderr}")
                return False
            
            print("✓ Step 2: HTML to Markdown successful")
            
            # Check results
            if os.path.exists(temp_md):
                with open(temp_md, 'r', encoding='utf-8', errors='ignore') as f:
                    md_content = f.read()
                
                print(f"✓ Markdown file created ({len(md_content)} characters)")
                
                # Show first few lines of Markdown
                lines = md_content.split('\n')[:10]
                print("Markdown preview:")
                for line in lines:
                    print(f"  {line[:80]}")
                
                # Check if media directory was created
                if os.path.exists(media_dir):
                    media_files = os.listdir(media_dir)
                    print(f"✓ Media directory created with {len(media_files)} files")
                else:
                    print("ℹ No media files extracted")
                
                return True
            else:
                print("✗ Markdown file was not created")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Conversion timed out")
            return False
        except Exception as e:
            print(f"✗ Conversion error: {e}")
            return False

def main():
    """Main test function"""
    print("=== Testing PDF -> HTML -> Markdown Conversion ===")
    
    # Test dependencies
    if not test_pdftohtml_availability():
        return False
    
    if not test_pandoc_availability():
        return False
    
    # Test conversions
    if not test_pdf_to_html_conversion():
        return False
    
    if not test_html_to_markdown_conversion():
        return False
    
    print("\n✓ All tests passed! PDF -> HTML -> Markdown workflow is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)