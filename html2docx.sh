#!/bin/bash

# HTML to DOCX converter with image support
# Usage: ./html2docx.sh <input.html> [output.docx]

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.html> [output.docx]"
    echo "Example: $0 book.html my-book.docx"
    exit 1
fi

INPUT_HTML="$1"
OUTPUT_DOCX="${2:-${INPUT_HTML%.html}.docx}"

# Check if input file exists
if [ ! -f "$INPUT_HTML" ]; then
    echo "Error: Input file '$INPUT_HTML' not found"
    exit 1
fi

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc is required but not installed"
    echo "Install with: brew install pandoc (macOS) or apt-get install pandoc (Linux)"
    exit 1
fi

echo "Converting $INPUT_HTML to $OUTPUT_DOCX..."

# Store original directory
ORIGINAL_DIR=$(pwd)

# Create temporary directory for processing
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy HTML file to temp directory
cp "$INPUT_HTML" "$TEMP_DIR/input.html"

# Extract and copy images
HTML_DIR=$(dirname "$INPUT_HTML")
IMAGE_DIR="$TEMP_DIR/images"
mkdir -p "$IMAGE_DIR"

# Find all image references in HTML and copy them
echo "Extracting images..."
grep -oE 'src="[^"]*\.(jpg|jpeg|png|gif|svg|webp)"' "$INPUT_HTML" | sed 's/src="//g' | sed 's/"//g' | while read -r img_path; do
    # Handle relative paths
    if [[ "$img_path" == /* ]]; then
        # Absolute path
        full_path="$img_path"
    else
        # Relative path
        full_path="$HTML_DIR/$img_path"
    fi
    
    if [ -f "$full_path" ]; then
        # Create directory structure in temp images folder
        img_dir=$(dirname "$img_path")
        mkdir -p "$IMAGE_DIR/$img_dir"
        cp "$full_path" "$IMAGE_DIR/$img_path"
        echo "Copied: $img_path"
    else
        echo "Warning: Image not found: $full_path"
    fi
done

# Update image paths in HTML to point to images directory
sed -i.bak 's/src="images\//src="images\//g' "$TEMP_DIR/input.html"
sed -i.bak 's/src="\([^"]*\)\.\(jpg\|jpeg\|png\|gif\|svg\|webp\)"/src="images\/\1.\2"/g' "$TEMP_DIR/input.html"

# Convert to DOCX with pandoc
echo "Converting to DOCX..."
cd "$TEMP_DIR"

OUTPUT_BASENAME=$(basename "$OUTPUT_DOCX")
pandoc input.html \
    --from html \
    --to docx \
    --output "$OUTPUT_BASENAME" \
    --resource-path=".:images" \
    --standalone \
    --metadata title="Generated DOCX" \
    --metadata author="HTML2DOCX Converter" \
    --wrap=auto

# Move output file to original directory
OUTPUT_BASENAME=$(basename "$OUTPUT_DOCX")
echo "DEBUG: Moving $OUTPUT_BASENAME to $ORIGINAL_DIR/$OUTPUT_BASENAME"
if [ -f "$OUTPUT_BASENAME" ]; then
    mv "$OUTPUT_BASENAME" "$ORIGINAL_DIR/$OUTPUT_BASENAME"
    echo "✅ DOCX created successfully: $ORIGINAL_DIR/$OUTPUT_BASENAME"
else
    echo "❌ DOCX file not found in temp directory"
    ls -la "$TEMP_DIR/"
fi
echo "📖 Images included: $(find images -type f 2>/dev/null | wc -l) files"