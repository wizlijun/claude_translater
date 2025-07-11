#!/bin/bash

# HTML to EPUB converter with automatic title extraction and cover image
# Usage: ./html2epub.sh <input.html> [output.epub]

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.html> [output.epub]"
    echo "Example: $0 book.html my-book.epub"
    exit 1
fi

INPUT_HTML="$1"
OUTPUT_EPUB="${2:-${INPUT_HTML%.html}.epub}"

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

echo "Converting $INPUT_HTML to $OUTPUT_EPUB..."

# Extract title from HTML
extract_title() {
    local html_file="$1"
    local title=""
    
    # Try to extract from <title> tag first
    title=$(grep -oiE '<title[^>]*>.*</title>' "$html_file" | sed 's/<[tT][iI][tT][lL][eE][^>]*>//g' | sed 's/<\/[tT][iI][tT][lL][eE]>//g' | head -1 | tr -d '\n\r' | sed 's/^[ \t]*//g' | sed 's/[ \t]*$//g')
    
    # If no title tag or empty, try first h1
    if [ -z "$title" ]; then
        title=$(grep -oiE '<h1[^>]*>.*</h1>' "$html_file" | sed 's/<[hH]1[^>]*>//g' | sed 's/<\/[hH]1>//g' | head -1 | tr -d '\n\r' | sed 's/^[ \t]*//g' | sed 's/[ \t]*$//g')
    fi
    
    # If still no title, try first h2
    if [ -z "$title" ]; then
        title=$(grep -oiE '<h2[^>]*>.*</h2>' "$html_file" | sed 's/<[hH]2[^>]*>//g' | sed 's/<\/[hH]2>//g' | head -1 | tr -d '\n\r' | sed 's/^[ \t]*//g' | sed 's/[ \t]*$//g')
    fi
    
    # Remove HTML tags and clean up
    title=$(echo "$title" | sed 's/<[^>]*>//g' | sed 's/&nbsp;/ /g' | sed 's/&amp;/\&/g' | sed 's/&lt;/</g' | sed 's/&gt;/>/g')
    
    # If still empty, use filename
    if [ -z "$title" ]; then
        title=$(basename "$html_file" .html)
    fi
    
    echo "$title"
}

# Extract author information
extract_author() {
    local html_file="$1"
    local author=""
    
    # Try to extract from meta tag
    author=$(grep -oE '<meta[^>]*name=["\']author["\'][^>]*content=["\'][^"\']*["\']' "$html_file" | sed 's/.*content=["\'\'']//' | sed 's/["\'\'']*$//' | head -1)
    
    # If no meta author, try to find in content
    if [ -z "$author" ]; then
        author=$(grep -oiE '(作者|author|by)[:：]\s*[^<>\n]*' "$html_file" | sed 's/.*[:：]\s*//' | head -1 | tr -d '\n\r' | sed 's/^[ \t]*//g' | sed 's/[ \t]*$//g')
    fi
    
    # Default author if none found
    if [ -z "$author" ]; then
        author="Unknown Author"
    fi
    
    echo "$author"
}

# Store original directory
ORIGINAL_DIR=$(pwd)

# Extract metadata from HTML
echo "Extracting metadata..."
BOOK_TITLE=$(extract_title "$INPUT_HTML")
BOOK_AUTHOR=$(extract_author "$INPUT_HTML")

echo "📖 Title: $BOOK_TITLE"
echo "👤 Author: $BOOK_AUTHOR"

# Create temporary directory for processing
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy HTML file to temp directory
cp "$INPUT_HTML" "$TEMP_DIR/input.html"

# Handle images - extract first image from HTML content for cover
HTML_DIR=$(dirname "$INPUT_HTML")
echo "Extracting images..."

# Copy media directory if it exists
if [ -d "$HTML_DIR/media" ]; then
    echo "Copying media directory..."
    cp -r "$HTML_DIR/media" "$TEMP_DIR/"
    IMAGE_COUNT=$(find "$TEMP_DIR/media" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
    echo "Found $IMAGE_COUNT images in media directory"
else
    echo "No media directory found"
    IMAGE_COUNT=0
fi

# Extract first image from HTML content (in order of appearance)
echo "Looking for first image in HTML content..."
FIRST_IMAGE=""

# Extract the first image src from HTML file (in document order)
FIRST_IMG_SRC=$(grep -oE '<img[^>]*src="[^"]*"' "$INPUT_HTML" | head -1 | grep -oE 'src="[^"]*"' | sed 's/src="//g' | sed 's/"//g')

if [ -n "$FIRST_IMG_SRC" ]; then
    echo "Found first image reference in HTML: $FIRST_IMG_SRC"
    
    # Handle different path formats
    if [[ "$FIRST_IMG_SRC" == /* ]]; then
        # Absolute path
        full_image_path="$FIRST_IMG_SRC"
    elif [[ "$FIRST_IMG_SRC" == http* ]]; then
        # Web URL - skip
        echo "Skipping web URL: $FIRST_IMG_SRC"
        full_image_path=""
    else
        # Relative path - combine with HTML directory
        full_image_path="$HTML_DIR/$FIRST_IMG_SRC"
    fi
    
    # Check if the image file exists
    if [ -n "$full_image_path" ] && [ -f "$full_image_path" ]; then
        # Copy to temp directory if not already there
        TEMP_IMAGE_PATH="$TEMP_DIR/$FIRST_IMG_SRC"
        
        # Create directory structure if needed
        mkdir -p "$(dirname "$TEMP_IMAGE_PATH")"
        
        # Copy the image if it's not already in temp directory
        if [ ! -f "$TEMP_IMAGE_PATH" ]; then
            cp "$full_image_path" "$TEMP_IMAGE_PATH"
            echo "Copied cover image: $FIRST_IMG_SRC"
        fi
        
        FIRST_IMAGE="$FIRST_IMG_SRC"
        echo "🖼️  Cover image (first in HTML): $FIRST_IMAGE"
    else
        echo "Warning: First image file not found: $full_image_path"
    fi
else
    echo "No image tags found in HTML content"
fi

# If still no cover image found, try to use first image from media directory as fallback
if [ -z "$FIRST_IMAGE" ] && [ -d "$TEMP_DIR/media" ]; then
    echo "Using first image from media directory as fallback..."
    FALLBACK_IMAGE=$(find "$TEMP_DIR/media" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | head -1)
    if [ -n "$FALLBACK_IMAGE" ]; then
        FIRST_IMAGE=$(echo "$FALLBACK_IMAGE" | sed "s|$TEMP_DIR/||")
        echo "🖼️  Fallback cover image: $FIRST_IMAGE"
    fi
fi

# Convert to EPUB with pandoc
echo "Converting to EPUB..."
cd "$TEMP_DIR"

OUTPUT_BASENAME=$(basename "$OUTPUT_EPUB")

# Create CSS file
cat > style.css << 'EOF'
body { 
    font-family: Georgia, serif; 
    line-height: 1.6; 
    max-width: 800px; 
    margin: 0 auto; 
    padding: 20px; 
}
img { 
    max-width: 100%; 
    height: auto; 
    display: block; 
    margin: 20px auto; 
}
h1, h2, h3, h4, h5, h6 { 
    color: #333; 
    margin-top: 30px; 
}
p { 
    text-align: justify; 
    margin-bottom: 15px; 
}
.cover-image {
    width: 100%;
    height: auto;
    margin: 0;
}
EOF

# Execute pandoc conversion
echo "Converting to EPUB with pandoc..."
echo "Output file: $OUTPUT_BASENAME"

# Simple and reliable pandoc execution
if [ -n "$FIRST_IMAGE" ] && [ -f "$FIRST_IMAGE" ]; then
    echo "📸 Setting cover image: $FIRST_IMAGE"
    pandoc input.html \
        --from html \
        --to epub3 \
        --output "$OUTPUT_BASENAME" \
        --standalone \
        --metadata title="$BOOK_TITLE" \
        --metadata author="$BOOK_AUTHOR" \
        --epub-cover-image="$FIRST_IMAGE" \
        --css style.css
else
    echo "No cover image, converting without cover"
    pandoc input.html \
        --from html \
        --to epub3 \
        --output "$OUTPUT_BASENAME" \
        --standalone \
        --metadata title="$BOOK_TITLE" \
        --metadata author="$BOOK_AUTHOR" \
        --css style.css
fi

# Check if conversion was successful
if [ ! -f "$OUTPUT_BASENAME" ]; then
    echo "❌ EPUB conversion failed"
    echo "Contents of working directory:"
    ls -la
    exit 1
fi

echo "✅ Pandoc conversion completed successfully"

# Move output file to original directory
OUTPUT_BASENAME=$(basename "$OUTPUT_EPUB")
if [ -f "$OUTPUT_BASENAME" ]; then
    mv "$OUTPUT_BASENAME" "$ORIGINAL_DIR/$OUTPUT_BASENAME"
    echo ""
    echo "✅ EPUB created successfully!"
    echo "📁 File: $ORIGINAL_DIR/$OUTPUT_BASENAME"
    echo "📖 Title: $BOOK_TITLE"
    echo "👤 Author: $BOOK_AUTHOR"
    
    # Count images in media directory
    if [ -d "media" ]; then
        ACTUAL_IMAGE_COUNT=$(find media -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
        echo "🖼️  Images included: $ACTUAL_IMAGE_COUNT files"
    else
        echo "🖼️  Images included: 0 files"
    fi
    
    # Show cover image info
    if [ -n "$FIRST_IMAGE" ]; then
        echo "📸 Cover image: $FIRST_IMAGE"
    else
        echo "📸 Cover image: None (no images found)"
    fi
    
    # Show file size
    if [ -f "$ORIGINAL_DIR/$OUTPUT_BASENAME" ]; then
        FILE_SIZE=$(stat -f%z "$ORIGINAL_DIR/$OUTPUT_BASENAME" 2>/dev/null || stat -c%s "$ORIGINAL_DIR/$OUTPUT_BASENAME" 2>/dev/null || echo "unknown")
        echo "💾 File size: $(numfmt --to=iec $FILE_SIZE 2>/dev/null || echo "$FILE_SIZE bytes")"
    fi
else
    echo "❌ EPUB file not found in temp directory"
    echo "Debug: Contents of temp directory:"
    ls -la "$TEMP_DIR/"
fi