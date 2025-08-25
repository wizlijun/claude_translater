#!/usr/bin/env python3
"""
Step 7: Generate DOCX and EPUB files in temp directory
Uses existing html2docx.sh and html2epub.sh scripts to generate files in temp directory
"""

import os
import sys
import subprocess
from pathlib import Path

def log_info(message):
    """Log info message"""
    print(f"[INFO] {message}")

def log_success(message):
    """Log success message"""
    print(f"[SUCCESS] {message}")

def log_error(message):
    """Log error message"""
    print(f"[ERROR] {message}")

def log_warning(message):
    """Log warning message"""
    print(f"[WARNING] {message}")

def translate_title_with_claude(title, target_lang, custom_prompt=None):
    """Translate book title using Claude CLI"""
    if not title or not title.strip():
        return title
    
    try:
        import subprocess
        
        log_info(f"Translating title '{title}' to {target_lang}...")
        
        # Create translation prompt
        lang_map = {
            'zh': 'Chinese',
            'en': 'English', 
            'ja': 'Japanese',
            'ko': 'Korean',
            'fr': 'French',
            'de': 'German',
            'es': 'Spanish',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian'
        }
        
        target_lang_name = lang_map.get(target_lang.lower(), target_lang)
        
        prompt = f"""Please translate this book title to {target_lang_name}. 
CRITICAL OUTPUT FORMAT: You must strictly follow this format:
- Do not output any explanatory text or metadata
- Strictly follow the format: <!-- START -->[translated title]<!-- END -->

Title: {title}"""

        if custom_prompt:
            prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt}"
        
        # Run Claude CLI
        process = subprocess.Popen(
            ['claude'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        stdout, stderr = process.communicate(input=prompt, timeout=30)
        
        if process.returncode == 0 and stdout.strip():
            # Extract content between START and END markers
            def extract_title_from_markers(text):
                """Extract title content between START and END markers"""
                start_marker = '<!-- START -->'
                end_marker = '<!-- END -->'
                
                # Find the positions of markers
                start_pos = text.find(start_marker)
                end_pos = text.find(end_marker)
                
                if start_pos == -1:
                    # Try to find markers with variations
                    for variation in ['<!--START-->', '<!-- START-->', '<!--START -->', '<!-- START-->']:
                        start_pos = text.find(variation)
                        if start_pos != -1:
                            start_marker = variation
                            break
                
                if end_pos == -1:
                    # Try to find markers with variations
                    for variation in ['<!--END-->', '<!-- END-->', '<!--END -->', '<!-- END-->']:
                        end_pos = text.find(variation)
                        if end_pos != -1:
                            end_marker = variation
                            break
                
                if start_pos != -1 and end_pos != -1 and start_pos < end_pos:
                    # Extract content between markers
                    content_start = start_pos + len(start_marker)
                    extracted = text[content_start:end_pos].strip()
                    return extracted
                
                return None
            
            raw_output = stdout.strip()
            translated_title = extract_title_from_markers(raw_output)
            
            if translated_title:
                # Clean up any formatting markers
                translated_title = translated_title.replace('**', '').replace('*', '').strip()
                log_success(f"Title translated: '{title}' -> '{translated_title}'")
                return translated_title
            else:
                log_warning(f"Failed to extract title from markers. Raw output: {raw_output[:100]}...")
                log_warning(f"Using original title: {title}")
                return title
        else:
            log_warning(f"Title translation failed, using original: {stderr}")
            return title
            
    except Exception as e:
        log_warning(f"Error translating title: {e}, using original")
        return title

def load_config():
    """Load configuration from temp directory"""
    # Look for config files in temp directories - use the same logic as main
    config_files = []
    
    # Check for config.txt files in temp directories
    import glob
    temp_dirs = glob.glob("*_temp")
    for temp_dir in temp_dirs:
        config_file = os.path.join(temp_dir, "config.txt")
        if os.path.exists(config_file):
            config_files.append(config_file)
    
    # Also check current directory as fallback
    if os.path.exists("config.txt"):
        config_files.append("config.txt")
    
    if not config_files:
        return None
    
    # Use the most recent config file
    config_file = max(config_files, key=os.path.getmtime)
    
    config = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        return config
    except Exception as e:
        log_warning(f"Could not read config file {config_file}: {e}")
        return None

def generate_docx_with_script(html_file, temp_dir, metadata=None):
    """Generate DOCX file using calibre_html_publish.py script"""
    # Create output filename in temp directory - use book.docx as requested
    docx_file = os.path.join(temp_dir, "book.docx")
    
    # Skip if DOCX already exists
    if os.path.exists(docx_file):
        log_info(f"Skipping DOCX generation - file already exists: {docx_file}")
        file_size = os.path.getsize(docx_file)
        log_success(f"Found existing DOCX: {docx_file} ({file_size} bytes)")
        return docx_file
    
    log_info("Generating DOCX file using calibre_html_publish.py...")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    publish_script = os.path.join(script_dir, "calibre_html_publish.py")
    
    if not os.path.exists(publish_script):
        log_error(f"calibre_html_publish.py script not found at: {publish_script}")
        return None
    
    try:
        # Run calibre_html_publish.py script with output filename
        cmd = ["python3", publish_script, html_file, "-o", docx_file]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if os.path.exists(docx_file):
            log_success(f"DOCX file created: {docx_file}")
            return docx_file
        else:
            log_error("DOCX file was not created")
            if result.stdout:
                log_info(f"Script output: {result.stdout}")
            return None
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to generate DOCX: {e.stderr}")
        if e.stdout:
            log_info(f"Script output: {e.stdout}")
        return None
    except Exception as e:
        log_error(f"Error running calibre_html_publish.py: {e}")
        return None

def generate_epub_with_script(html_file, temp_dir, metadata=None):
    """Generate EPUB file using calibre_html_publish.py script"""
    # Create output filename in temp directory - use book.epub as requested
    epub_file = os.path.join(temp_dir, "book.epub")
    
    # Skip if EPUB already exists
    if os.path.exists(epub_file):
        log_info(f"Skipping EPUB generation - file already exists: {epub_file}")
        file_size = os.path.getsize(epub_file)
        log_success(f"Found existing EPUB: {epub_file} ({file_size} bytes)")
        return epub_file
    
    log_info("Generating EPUB file using calibre_html_publish.py...")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    publish_script = os.path.join(script_dir, "calibre_html_publish.py")
    
    if not os.path.exists(publish_script):
        log_error(f"calibre_html_publish.py script not found at: {publish_script}")
        return None
    
    try:
        # Run calibre_html_publish.py script with output filename
        cmd = ["python3", publish_script, html_file, "-o", epub_file]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if os.path.exists(epub_file):
            log_success(f"EPUB file created: {epub_file}")
            return epub_file
        else:
            log_error("EPUB file was not created")
            if result.stdout:
                log_info(f"Script output: {result.stdout}")
            return None
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to generate EPUB: {e.stderr}")
        if e.stdout:
            log_info(f"Script output: {e.stdout}")
        return None
    except Exception as e:
        log_error(f"Error running calibre_html_publish.py: {e}")
        return None

def generate_pdf_with_script(html_file, temp_dir, metadata=None):
    """Generate PDF file using calibre_html_publish.py script"""
    # Create output filename in temp directory - use book.pdf as requested
    pdf_file = os.path.join(temp_dir, "book.pdf")
    
    # Skip if PDF already exists
    if os.path.exists(pdf_file):
        log_info(f"Skipping PDF generation - file already exists: {pdf_file}")
        file_size = os.path.getsize(pdf_file)
        log_success(f"Found existing PDF: {pdf_file} ({file_size} bytes)")
        return pdf_file
    
    log_info("Generating PDF file using calibre_html_publish.py...")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    publish_script = os.path.join(script_dir, "calibre_html_publish.py")
    
    if not os.path.exists(publish_script):
        log_error(f"calibre_html_publish.py script not found at: {publish_script}")
        return None
    
    try:
        # Run calibre_html_publish.py script with output filename
        cmd = ["python3", publish_script, html_file, "-o", pdf_file]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if os.path.exists(pdf_file):
            log_success(f"PDF file created: {pdf_file}")
            return pdf_file
        else:
            log_error("PDF file was not created")
            if result.stdout:
                log_info(f"Script output: {result.stdout}")
            return None
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to generate PDF: {e.stderr}")
        if e.stdout:
            log_info(f"Script output: {e.stdout}")
        return None
    except Exception as e:
        log_error(f"Error running calibre_html_publish.py: {e}")
        return None

def main():
    """Main function"""
    log_info("Starting Step 7: Generate DOCX, EPUB, and PDF files")
    
    # Load configuration
    config = load_config()
    if not config:
        log_error("Could not find configuration file. Please ensure step 1 completed successfully.")
        sys.exit(1)
    
    # Get temp directory
    temp_dir = config.get('temp_dir')
    output_lang = config.get('output_lang', 'zh')
    
    # If temp_dir not specified in config, try to determine from config file location
    if not temp_dir:
        # Try to determine from the config file path
        config_files = []
        
        # Check for config.txt files in temp directories
        import glob
        temp_dirs = glob.glob("*_temp")
        for temp_dir_candidate in temp_dirs:
            config_file = os.path.join(temp_dir_candidate, "config.txt")
            if os.path.exists(config_file):
                config_files.append((config_file, temp_dir_candidate))
        
        if config_files:
            # Use the most recent config file's directory
            _, temp_dir = max(config_files, key=lambda x: os.path.getmtime(x[0]))
            log_info(f"Using temp directory from config location: {temp_dir}")
        else:
            log_error("No temp directory found and none specified in config.")
            sys.exit(1)
    
    # Use book_doc.html from the base_temp directory as input for format conversion
    html_file = os.path.join(temp_dir, "book_doc.html")
    
    # Check if book_doc.html exists
    if not os.path.exists(html_file):
        log_error(f"HTML file not found: {html_file}")
        log_error("Please ensure step 5 (HTML generation) completed successfully.")
        
        # Try to find alternative HTML files in temp directory
        import glob
        html_files = glob.glob(os.path.join(temp_dir, "*.html"))
        if html_files:
            html_file = max(html_files, key=os.path.getmtime)
            log_info(f"Found alternative HTML file: {html_file}")
        else:
            log_error("No HTML files found in temp directory.")
            sys.exit(1)
    
    # Extract metadata from config (title should already be translated in step 5)
    original_title = config.get('original_title', '')
    creator = config.get('creator', '')
    publisher = config.get('publisher', '')
    
    log_info(f"Processing HTML file: {html_file}")
    log_info(f"Output directory: {temp_dir}")
    
    # Ensure temp directory exists
    os.makedirs(temp_dir, exist_ok=True)
    
    # Prepare metadata dictionary for generation scripts
    book_metadata = {}
    if original_title:
        book_metadata['title'] = original_title  # Use original title for metadata
    if creator:
        book_metadata['creator'] = creator
    if publisher:
        book_metadata['publisher'] = publisher
    
    # Generate all formats using calibre_html_publish.py
    docx_file = generate_docx_with_script(html_file, temp_dir, book_metadata)
    epub_file = generate_epub_with_script(html_file, temp_dir, book_metadata)
    pdf_file = generate_pdf_with_script(html_file, temp_dir, book_metadata)
    
    # Report results
    generated_files = []
    if docx_file:
        file_size = os.path.getsize(docx_file)
        log_success(f"DOCX: {docx_file} ({file_size} bytes)")
        generated_files.append("DOCX")
    if epub_file:
        file_size = os.path.getsize(epub_file)
        log_success(f"EPUB: {epub_file} ({file_size} bytes)")
        generated_files.append("EPUB")
    if pdf_file:
        file_size = os.path.getsize(pdf_file)
        log_success(f"PDF: {pdf_file} ({file_size} bytes)")
        generated_files.append("PDF")
    
    if generated_files:
        log_success(f"Format generation completed! Generated: {', '.join(generated_files)}")
        log_success(f"All files saved to: {temp_dir}")
    else:
        log_error("No files were generated")
        sys.exit(1)

if __name__ == "__main__":
    main()