#!/usr/bin/env python3
"""
Step 1: Environment preparation and parameter parsing
Creates temp directory and parses command line arguments
"""

import argparse
import os
import sys
from pathlib import Path
import shutil

def create_temp_directory(input_file, clean=False):
    """Create temporary directory based on input filename"""
    input_path = Path(input_file)
    temp_dir = input_path.stem + "_temp"
    
    if os.path.exists(temp_dir):
        print(f"Temp directory {temp_dir} already exists")
        print(f"Using existing {temp_dir}")
    else:
        os.makedirs(temp_dir)
        print(f"Created temp directory: {temp_dir}")
    
    return temp_dir

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Book Translation Tool - Step 1: Environment Setup"
    )
    
    parser.add_argument(
        "input_file",
        help="Input file (PDF, DOCX, or EPUB)"
    )
    
    parser.add_argument(
        "-l", "--ilang",
        default="auto",
        help="Input language (default: auto-detect)"
    )
    
    parser.add_argument(
        "--olang",
        default="zh",
        help="Output language (default: zh - Chinese)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output.html",
        help="Output HTML file name (default: output.html)"
    )
    
    return parser.parse_args()

def validate_input_file(input_file):
    """Validate input file exists and has supported extension"""
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    supported_formats = ['.pdf', '.docx', '.epub']
    file_ext = Path(input_file).suffix.lower()
    
    if file_ext not in supported_formats:
        print(f"Error: Unsupported file format '{file_ext}'")
        print(f"Supported formats: {', '.join(supported_formats)}")
        sys.exit(1)
    
    return file_ext

def save_config(temp_dir, args, file_ext):
    """Save configuration to temp directory for other scripts"""
    # Generate output file path in temp directory
    output_file = args.output
    if not output_file.endswith('.html'):
        output_file += '.html'
    
    # Put output file in temp directory
    output_path = os.path.join(temp_dir, output_file)
    
    config = {
        'input_file': args.input_file,
        'input_lang': args.ilang,
        'output_lang': args.olang,
        'output_file': output_path,
        'file_extension': file_ext,
        'temp_dir': temp_dir
    }
    
    config_file = os.path.join(temp_dir, 'config.txt')
    with open(config_file, 'w', encoding='utf-8') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print(f"Configuration saved to {config_file}")
    return config

def main():
    """Main function"""
    print("=== Book Translation Tool - Step 1: Environment Setup ===")
    
    # Parse arguments
    args = parse_arguments()
    
    # Validate input file
    file_ext = validate_input_file(args.input_file)
    
    # Create temp directory
    temp_dir = create_temp_directory(args.input_file)
    
    # Save configuration
    config = save_config(temp_dir, args, file_ext)
    
    print("\n=== Configuration ===")
    print(f"Input file: {config['input_file']}")
    print(f"Input language: {config['input_lang']}")
    print(f"Output language: {config['output_lang']}")
    print(f"Output file: {config['output_file']}")
    print(f"File type: {config['file_extension']}")
    print(f"Temp directory: {config['temp_dir']}")
    
    print("\n=== Step 1 Complete ===")
    print("Next step: Run 02_split_to_md.py")

if __name__ == "__main__":
    main()