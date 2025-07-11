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

def translate_title_with_claude(title, target_lang):
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
Only return the translated title, nothing else.
Title: {title}"""
        
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
            translated_title = stdout.strip()
            # Clean up any formatting markers
            translated_title = translated_title.replace('**', '').replace('*', '').strip()
            log_success(f"Title translated: '{title}' -> '{translated_title}'")
            return translated_title
        else:
            log_warning(f"Title translation failed, using original: {stderr}")
            return title
            
    except Exception as e:
        log_warning(f"Error translating title: {e}, using original")
        return title

def load_config():
    """Load configuration from temp directory"""
    # Look for config files in current directory and temp directories
    config_files = []
    
    # Check for config.txt files in temp directories
    import glob
    temp_dirs = glob.glob("*_temp")
    for temp_dir in temp_dirs:
        config_file = os.path.join(temp_dir, "config.txt")
        if os.path.exists(config_file):
            config_files.append(config_file)
    
    # Also check current directory
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
    """Generate DOCX file using html2docx.sh script"""
    # Create output filename in temp directory
    html_name = os.path.splitext(os.path.basename(html_file))[0]
    docx_file = os.path.join(temp_dir, f"{html_name}.docx")
    
    # Skip if DOCX already exists
    if os.path.exists(docx_file):
        log_info(f"Skipping DOCX generation - file already exists: {docx_file}")
        file_size = os.path.getsize(docx_file)
        log_success(f"Found existing DOCX: {docx_file} ({file_size} bytes)")
        return docx_file
    
    log_info("Generating DOCX file using html2docx.sh...")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docx_script = os.path.join(script_dir, "html2docx.sh")
    
    if not os.path.exists(docx_script):
        log_error(f"html2docx.sh script not found at: {docx_script}")
        return None
    
    try:
        # Create a metadata file for the script to use
        if metadata and (metadata.get('title') or metadata.get('creator')):
            metadata_file = os.path.join(temp_dir, 'book_metadata.env')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                if metadata.get('title'):
                    f.write(f'BOOK_TITLE="{metadata["title"]}"\n')
                if metadata.get('creator'):
                    f.write(f'BOOK_AUTHOR="{metadata["creator"]}"\n')
                if metadata.get('publisher'):
                    f.write(f'BOOK_PUBLISHER="{metadata["publisher"]}"\n')
            log_info(f"Created metadata file for DOCX generation: {metadata_file}")
        
        # Run html2docx.sh script with output filename
        cmd = [docx_script, html_file, docx_file]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Check if the script created the file in the current directory instead
        current_dir_file = f"{html_name}.docx"
        if os.path.exists(current_dir_file):
            # Move the file to temp directory
            import shutil
            shutil.move(current_dir_file, docx_file)
            log_info(f"Moved DOCX file to temp directory: {docx_file}")
        
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
        log_error(f"Error running html2docx.sh: {e}")
        return None

def generate_epub_with_script(html_file, temp_dir, metadata=None):
    """Generate EPUB file using html2epub.sh script"""
    # Create output filename in temp directory
    html_name = os.path.splitext(os.path.basename(html_file))[0]
    epub_file = os.path.join(temp_dir, f"{html_name}.epub")
    
    # Skip if EPUB already exists
    if os.path.exists(epub_file):
        log_info(f"Skipping EPUB generation - file already exists: {epub_file}")
        file_size = os.path.getsize(epub_file)
        log_success(f"Found existing EPUB: {epub_file} ({file_size} bytes)")
        return epub_file
    
    log_info("Generating EPUB file using html2epub.sh...")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    epub_script = os.path.join(script_dir, "html2epub.sh")
    
    if not os.path.exists(epub_script):
        log_error(f"html2epub.sh script not found at: {epub_script}")
        return None
    
    try:
        # Create a metadata file for the script to use
        if metadata and (metadata.get('title') or metadata.get('creator')):
            metadata_file = os.path.join(temp_dir, 'book_metadata.env')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                if metadata.get('title'):
                    f.write(f'BOOK_TITLE="{metadata["title"]}"\n')
                if metadata.get('creator'):
                    f.write(f'BOOK_AUTHOR="{metadata["creator"]}"\n')
                if metadata.get('publisher'):
                    f.write(f'BOOK_PUBLISHER="{metadata["publisher"]}"\n')
            log_info(f"Created metadata file for EPUB generation: {metadata_file}")
        
        # Run html2epub.sh script with output filename
        cmd = [epub_script, html_file, epub_file]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Check if the script created the file in the current directory instead
        current_dir_file = f"{html_name}.epub"
        if os.path.exists(current_dir_file):
            # Move the file to temp directory
            import shutil
            shutil.move(current_dir_file, epub_file)
            log_info(f"Moved EPUB file to temp directory: {epub_file}")
        
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
        log_error(f"Error running html2epub.sh: {e}")
        return None

def main():
    """Main function"""
    log_info("Starting Step 7: Generate DOCX and EPUB files")
    
    # Load configuration
    config = load_config()
    if not config:
        log_error("Could not find configuration file. Please ensure step 1 completed successfully.")
        sys.exit(1)
    
    # Get HTML file path from config
    html_file = config.get('output_file')
    temp_dir = config.get('temp_dir', 'temp')
    output_lang = config.get('output_lang', 'zh')
    
    # Extract metadata
    original_title = config.get('original_title', '')
    creator = config.get('creator', '')
    publisher = config.get('publisher', '')
    
    # Translate title if available
    translated_title = ''
    if original_title:
        translated_title = translate_title_with_claude(original_title, output_lang)
        log_info(f"Book metadata - Title: {translated_title}, Creator: {creator}")
    
    if not html_file:
        log_error("No output file specified in configuration.")
        sys.exit(1)
    
    if not os.path.exists(html_file):
        log_error(f"HTML file not found: {html_file}")
        log_error("Please ensure step 5 (HTML generation) completed successfully.")
        sys.exit(1)
    
    log_info(f"Found HTML file: {html_file}")
    log_info(f"Using temp directory: {temp_dir}")
    
    # Ensure temp directory exists
    os.makedirs(temp_dir, exist_ok=True)
    
    # Prepare metadata dictionary for generation scripts
    book_metadata = {}
    if translated_title:
        book_metadata['title'] = translated_title
    if creator:
        book_metadata['creator'] = creator
    if publisher:
        book_metadata['publisher'] = publisher
    
    # Generate DOCX file using script
    docx_file = generate_docx_with_script(html_file, temp_dir, book_metadata)
    
    # Generate EPUB file using script
    epub_file = generate_epub_with_script(html_file, temp_dir, book_metadata)
    
    # Report results
    if docx_file or epub_file:
        log_success("Format generation completed!")
        if docx_file:
            file_size = os.path.getsize(docx_file)
            log_success(f"DOCX: {docx_file} ({file_size} bytes)")
        if epub_file:
            file_size = os.path.getsize(epub_file)
            log_success(f"EPUB: {epub_file} ({file_size} bytes)")
    else:
        log_error("No files were generated")
        sys.exit(1)

if __name__ == "__main__":
    main()