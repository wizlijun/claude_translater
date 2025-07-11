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

def generate_docx_with_script(html_file, temp_dir):
    """Generate DOCX file using html2docx.sh script"""
    log_info("Generating DOCX file using html2docx.sh...")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docx_script = os.path.join(script_dir, "html2docx.sh")
    
    if not os.path.exists(docx_script):
        log_error(f"html2docx.sh script not found at: {docx_script}")
        return None
    
    # Create output filename in temp directory
    html_name = os.path.splitext(os.path.basename(html_file))[0]
    docx_file = os.path.join(temp_dir, f"{html_name}.docx")
    
    try:
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

def generate_epub_with_script(html_file, temp_dir):
    """Generate EPUB file using html2epub.sh script"""
    log_info("Generating EPUB file using html2epub.sh...")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    epub_script = os.path.join(script_dir, "html2epub.sh")
    
    if not os.path.exists(epub_script):
        log_error(f"html2epub.sh script not found at: {epub_script}")
        return None
    
    # Create output filename in temp directory
    html_name = os.path.splitext(os.path.basename(html_file))[0]
    epub_file = os.path.join(temp_dir, f"{html_name}.epub")
    
    try:
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
    
    # Generate DOCX file using script
    docx_file = generate_docx_with_script(html_file, temp_dir)
    
    # Generate EPUB file using script
    epub_file = generate_epub_with_script(html_file, temp_dir)
    
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