#!/usr/bin/env python3
"""
Preprocess markdown files to fix OCR errors and improve readability
"""

import os
import sys
import re
import glob
from pathlib import Path

def clean_ocr_text(text):
    """Clean OCR errors and improve text readability"""
    
    # Fix common OCR errors
    text = re.sub(r'ﬂ', 'fl', text)  # Replace ﬂ with fl
    text = re.sub(r'ﬁ', 'fi', text)  # Replace ﬁ with fi
    text = re.sub(r'ﬀ', 'ff', text)  # Replace ﬀ with ff
    text = re.sub(r'ﬃ', 'ffi', text)  # Replace ﬃ with ffi
    text = re.sub(r'ﬄ', 'ffl', text)  # Replace ﬄ with ffl
    
    # Remove trailing backslashes
    text = re.sub(r'\\\s*$', '', text, flags=re.MULTILINE)
    
    # Remove isolated single characters that are likely OCR errors
    text = re.sub(r'^\s*[a-zA-Z]\s*$', '', text, flags=re.MULTILINE)
    
    # Remove lines with only symbols or very short fragments
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            cleaned_lines.append('')
            continue
            
        # Keep image references and markdown links
        if line.startswith('![') or line.startswith('[') and '](' in line:
            cleaned_lines.append(line)
            continue
            
        # Keep lines with asterisks (likely formatting)
        if line.startswith('*') and line.endswith('*'):
            cleaned_lines.append(line)
            continue
            
        # Skip very short lines that are likely OCR fragments
        if len(line) < 3:
            continue
            
        # Skip lines with only special characters
        if re.match(r'^[^a-zA-Z0-9\s]*$', line):
            continue
            
        cleaned_lines.append(line)
    
    # Join lines back together
    text = '\n'.join(cleaned_lines)
    
    # Try to reconstruct sentences by joining broken words
    # Look for patterns like "word \n word" and join them
    text = re.sub(r'(\w+)\s*\\\s*\n\s*(\w+)', r'\1\2', text)
    
    # Join lines that seem to be continuation of sentences
    # (lowercase word at start of line following a line that doesn't end with punctuation)
    lines = text.split('\n')
    reconstructed_lines = []
    i = 0
    
    while i < len(lines):
        current_line = lines[i].strip()
        
        # If current line is empty or an image/link, keep as is
        if not current_line or current_line.startswith('![') or current_line.startswith('['):
            reconstructed_lines.append(current_line)
            i += 1
            continue
        
        # Look ahead to see if next line should be joined
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            # Join if:
            # 1. Current line doesn't end with punctuation
            # 2. Next line starts with lowercase letter
            # 3. Next line is not empty and not an image/link
            if (current_line and 
                not current_line[-1] in '.!?:;' and 
                next_line and 
                not next_line.startswith('![') and
                not next_line.startswith('[') and
                next_line[0].islower()):
                
                # Join the lines
                current_line += ' ' + next_line
                i += 2  # Skip the next line since we've consumed it
            else:
                reconstructed_lines.append(current_line)
                i += 1
        else:
            reconstructed_lines.append(current_line)
            i += 1
    
    text = '\n'.join(reconstructed_lines)
    
    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

def preprocess_file(input_file, output_file):
    """Preprocess a single markdown file"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean the content
        cleaned_content = clean_ocr_text(content)
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"  ✓ Processed: {os.path.basename(input_file)}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {input_file}: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 preprocess_md.py <temp_directory>")
        sys.exit(1)
    
    temp_dir = sys.argv[1]
    
    if not os.path.exists(temp_dir):
        print(f"Error: Directory {temp_dir} does not exist")
        sys.exit(1)
    
    print("=== Markdown Preprocessing Tool ===")
    print(f"Processing directory: {temp_dir}")
    
    # Find all pageXXXX.md files (not output_ files)
    pattern = os.path.join(temp_dir, 'page*.md')
    md_files = glob.glob(pattern)
    md_files = [f for f in md_files if not os.path.basename(f).startswith('output_')]
    md_files.sort()
    
    if not md_files:
        print("No markdown files found to preprocess")
        return
    
    print(f"Found {len(md_files)} files to preprocess")
    
    processed_count = 0
    failed_count = 0
    
    for md_file in md_files:
        filename = os.path.basename(md_file)
        
        # Create cleaned version with _cleaned suffix
        base_name = os.path.splitext(filename)[0]
        cleaned_filename = f"{base_name}_cleaned.md"
        cleaned_path = os.path.join(temp_dir, cleaned_filename)
        
        if preprocess_file(md_file, cleaned_path):
            processed_count += 1
        else:
            failed_count += 1
    
    print(f"\nPreprocessing complete:")
    print(f"  Processed: {processed_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {len(md_files)}")
    
    if processed_count > 0:
        print(f"\nCleaned files are saved with '_cleaned' suffix")
        print("You can now use these cleaned files for translation")

if __name__ == "__main__":
    main()