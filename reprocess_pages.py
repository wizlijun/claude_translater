#!/usr/bin/env python3
"""
Reprocess pages 3-5 using the improved algorithm
"""

import os
import sys

def main():
    """Reprocess the pages using the improved split_pdf_with_pymupdf"""
    try:
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Import the updated function
        from 02_split_to_md import split_pdf_with_pymupdf
        
        # Process just a few pages to test
        temp_dir = os.path.join(current_dir, "temp")
        input_file = os.path.join(current_dir, "input.pdf")
        
        print("Testing improved PDF extraction...")
        
        # This will use the new algorithm
        split_pdf_with_pymupdf(input_file, temp_dir)
        
        print("Done!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)