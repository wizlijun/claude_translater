#!/bin/bash

# HTML to DOCX converter with automatic title extraction and font setting
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

# Handle images - simplified approach similar to epub script
HTML_DIR=$(dirname "$INPUT_HTML")
echo "Extracting images..."

# Copy media directory if it exists (common structure from your pipeline)
if [ -d "$HTML_DIR/media" ]; then
    echo "Copying media directory..."
    cp -r "$HTML_DIR/media" "$TEMP_DIR/"
    IMAGE_COUNT=$(find "$TEMP_DIR/media" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
    echo "Found $IMAGE_COUNT images in media directory"
else
    echo "No media directory found"
    IMAGE_COUNT=0
fi

# Convert to DOCX with pandoc
echo "Converting to DOCX..."
cd "$TEMP_DIR"

OUTPUT_BASENAME=$(basename "$OUTPUT_DOCX")

# Create a custom reference document for font styling
create_reference_docx() {
    echo "Creating reference document for font styling..."
    
    # Create a simple HTML file for reference
    cat > reference.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reference Document</title>
</head>
<body>
    <h1>标题一</h1>
    <h2>标题二</h2>
    <p>这是正文内容，应该使用仿宋体字体。</p>
    <p>This is body text that should use FangSong font.</p>
</body>
</html>
EOF

    # Convert to DOCX to create reference
    pandoc reference.html \
        --from html \
        --to docx \
        --output reference.docx \
        --standalone
        
    echo "Reference document created"
}

# Create reference document (optional, for font consistency)
# create_reference_docx

# Create CSS file for font styling (will be embedded in HTML)
cat > fangsong_style.css << 'EOF'
body {
    font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif;
    font-size: 12pt;
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
    font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif;
    font-weight: bold;
}

p {
    font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif;
}
EOF

# Modify HTML to include font styling
echo "Applying FangSong font styling..."
sed -i.bak 's/<head>/<head>\n<style>\nbody { font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif; }\nh1, h2, h3, h4, h5, h6 { font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif; }\np { font-family: "FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif; }\n<\/style>/' input.html

# Convert HTML to DOCX with metadata and font settings
echo "Converting with title: $BOOK_TITLE"
echo "Converting with author: $BOOK_AUTHOR"

pandoc input.html \
    --from html \
    --to docx \
    --output "$OUTPUT_BASENAME" \
    --standalone \
    --metadata title="$BOOK_TITLE" \
    --metadata author="$BOOK_AUTHOR" \
    --metadata lang="zh-CN" \
    --wrap=auto

# Move output file to original directory
OUTPUT_BASENAME=$(basename "$OUTPUT_DOCX")
if [ -f "$OUTPUT_BASENAME" ]; then
    mv "$OUTPUT_BASENAME" "$ORIGINAL_DIR/$OUTPUT_BASENAME"
    echo ""
    echo "✅ DOCX created successfully!"
    echo "📁 File: $ORIGINAL_DIR/$OUTPUT_BASENAME"
    echo "📖 Title: $BOOK_TITLE"
    echo "👤 Author: $BOOK_AUTHOR"
    echo "🖼️  Images included: $IMAGE_COUNT files"
    echo "🔤 Language: zh-CN (Chinese)"
    echo "📝 Font: 仿宋体 (FangSong) - 已内嵌CSS样式设置"
    
    # Show file size
    if [ -f "$ORIGINAL_DIR/$OUTPUT_BASENAME" ]; then
        FILE_SIZE=$(stat -f%z "$ORIGINAL_DIR/$OUTPUT_BASENAME" 2>/dev/null || stat -c%s "$ORIGINAL_DIR/$OUTPUT_BASENAME" 2>/dev/null || echo "unknown")
        echo "💾 File size: $(numfmt --to=iec $FILE_SIZE 2>/dev/null || echo "$FILE_SIZE bytes")"
    fi
else
    echo "❌ DOCX file not found in temp directory"
    echo "Debug: Contents of temp directory:"
    ls -la "$TEMP_DIR/"
fi