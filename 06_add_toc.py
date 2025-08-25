#!/usr/bin/env python3
"""
Step 6: Generate and insert TOC (Table of Contents) into HTML
Analyzes headings in HTML and creates a navigable TOC
Usage: 06_add_toc.py [-o output_file]
"""

import os
import sys
import re
import argparse
from pathlib import Path

# Try to import BeautifulSoup, fallback to regex if not available
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

def load_config(temp_dir):
    """Load configuration from step 1"""
    config_file = os.path.join(temp_dir, 'config.txt')
    if not config_file or not os.path.exists(config_file):
        # Try to find config in current directory temp folders
        temp_dirs = [d for d in os.listdir('.') if d.endswith('_temp')]
        if temp_dirs:
            config_file = os.path.join(max(temp_dirs, key=lambda d: os.path.getmtime(d)), 'config.txt')
    
    if not os.path.exists(config_file):
        print("Warning: config.txt not found. Using default settings.")
        return {'output_file': 'output.html'}
    
    config = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    
    return config

def extract_headings(soup):
    """Extract all headings from HTML and generate TOC data"""
    headings = []
    toc_data = []
    
    # Find all heading tags
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(heading.name[1])  # Extract number from h1, h2, etc.
        text = heading.get_text().strip()
        
        if not text:
            continue
        
        # Generate unique ID for heading
        heading_id = generate_heading_id(text, headings)
        
        # Add ID to heading tag
        heading['id'] = heading_id
        
        # Store heading info
        heading_info = {
            'level': level,
            'text': text,
            'id': heading_id,
            'element': heading
        }
        
        headings.append(heading_info)
        toc_data.append(heading_info)
    
    return toc_data

def generate_heading_id(text, existing_headings):
    """Generate unique ID for heading"""
    # Clean text for ID
    base_id = re.sub(r'[^\w\s-]', '', text.lower())
    base_id = re.sub(r'[-\s]+', '-', base_id)
    base_id = base_id.strip('-')
    
    if not base_id:
        base_id = 'heading'
    
    # Ensure uniqueness
    heading_id = base_id
    counter = 1
    
    existing_ids = [h['id'] for h in existing_headings if 'id' in h]
    
    while heading_id in existing_ids:
        heading_id = f"{base_id}-{counter}"
        counter += 1
    
    return heading_id

def generate_simple_toc_html(toc_data):
    """Generate simple HTML for table of contents (for sidebar)"""
    if not toc_data:
        return ""
    
    toc_html = '<ul>\n'
    
    current_level = 1
    
    for item in toc_data:
        level = item['level']
        text = item['text']
        heading_id = item['id']
        
        # Adjust nesting level
        if level > current_level:
            # Open new nested lists
            while current_level < level:
                toc_html += '<li><ul>\n'
                current_level += 1
        elif level < current_level:
            # Close nested lists
            while current_level > level:
                toc_html += '</ul></li>\n'
                current_level -= 1
        
        # Add TOC item
        toc_html += f'<li><a href="#{heading_id}">{text}</a></li>\n'
    
    # Close any remaining open lists
    while current_level > 1:
        toc_html += '</ul></li>\n'
        current_level -= 1
    
    toc_html += '</ul>\n'
    
    return toc_html

def get_toc_styles():
    """Get CSS styles for TOC"""
    return '''
    <style>
        #table-of-contents {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0 40px 0;
            max-width: 100%;
        }
        
        #table-of-contents h2 {
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
        }
        
        .toc-nav {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .toc-list {
            list-style: none;
            padding-left: 0;
            margin: 0;
        }
        
        .toc-list .toc-list {
            padding-left: 20px;
            margin-top: 5px;
        }
        
        .toc-list li {
            margin: 5px 0;
        }
        
        .toc-list a {
            color: #34495e;
            text-decoration: none;
            padding: 4px 8px;
            display: block;
            border-radius: 4px;
            transition: background-color 0.2s, color 0.2s;
        }
        
        .toc-list a:hover {
            background-color: #e8f4f8;
            color: #2980b9;
        }
        
        .content-separator {
            border-top: 1px solid #e9ecef;
            margin: 40px 0;
        }
        
        /* Smooth scrolling for anchor links */
        html {
            scroll-behavior: smooth;
        }
        
        /* Highlight target heading */
        h1:target, h2:target, h3:target, h4:target, h5:target, h6:target {
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 4px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }
        
        @media (max-width: 768px) {
            #table-of-contents {
                padding: 15px;
                margin: 15px 0 30px 0;
            }
            
            .toc-nav {
                max-height: 300px;
            }
            
            .toc-list .toc-list {
                padding-left: 15px;
            }
        }
    </style>
    '''

def insert_toc_into_html(html_file):
    """Insert TOC into HTML file"""
    print(f"Processing HTML file: {html_file}")
    
    if not BS4_AVAILABLE:
        print("BeautifulSoup not available, using regex-based TOC generation...")
        return insert_toc_with_regex(html_file)
    
    # Read HTML file
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return False
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract headings and generate TOC
    toc_data = extract_headings(soup)
    
    if not toc_data:
        print("No headings found in HTML file")
        return False
    
    print(f"Found {len(toc_data)} headings")
    
    # Generate simple TOC HTML for sidebar
    toc_html = generate_simple_toc_html(toc_data)
    
    # Find the toc-content div and insert TOC there
    toc_content_div = soup.find('div', class_='toc-content')
    if toc_content_div:
        # Clear existing content and insert new TOC
        toc_content_div.clear()
        toc_soup = BeautifulSoup(toc_html, 'html.parser')
        toc_content_div.append(toc_soup)
        print("✓ TOC inserted into sidebar")
    else:
        print("Warning: .toc-content div not found, TOC not inserted")
        return False
    
    # Save updated HTML
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"✓ TOC inserted successfully")
        return True
        
    except Exception as e:
        print(f"Error saving HTML file: {e}")
        return False

def generate_toc_summary(html_file):
    """Generate summary of TOC structure"""
    print("Generating TOC summary...")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        summary = "# Table of Contents Summary\n\n"
        summary += f"Total headings: {len(headings)}\n\n"
        
        # Count headings by level
        level_counts = {}
        for heading in headings:
            level = heading.name
            level_counts[level] = level_counts.get(level, 0) + 1
        
        summary += "## Heading Distribution\n\n"
        for level in sorted(level_counts.keys()):
            count = level_counts[level]
            summary += f"- {level.upper()}: {count} headings\n"
        
        summary += "\n## TOC Structure\n\n"
        for heading in headings:
            level = int(heading.name[1])
            text = heading.get_text().strip()
            indent = "  " * (level - 1)
            summary += f"{indent}- {text}\n"
        
        # Save summary
        summary_file = html_file.replace('.html', '_toc_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"TOC summary saved to: {summary_file}")
        
    except Exception as e:
        print(f"Error generating TOC summary: {e}")

def insert_toc_with_regex(html_file):
    """Insert TOC into HTML file using regex (fallback when BeautifulSoup not available)"""
    
    # Read HTML file
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return False
    
    # Extract headings using regex
    heading_pattern = r'<(h[1-6])(?:[^>]*)>(.*?)</\1>'
    headings = re.findall(heading_pattern, html_content, re.IGNORECASE | re.DOTALL)
    
    if not headings:
        print("No headings found in HTML file")
        return False
    
    print(f"Found {len(headings)} headings")
    
    # Generate simple TOC HTML
    toc_html = '<ul>\n'
    
    for i, (tag, text) in enumerate(headings):
        level = int(tag[1])  # Extract number from h1, h2, etc.
        # Clean text from any HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        heading_id = f"heading-{i+1}"
        
        # Add ID to the heading in the content
        old_heading = f'<{tag}>{text}</{tag}>'
        new_heading = f'<{tag} id="{heading_id}">{text}</{tag}>'
        html_content = html_content.replace(old_heading, new_heading, 1)
        
        # Add to TOC with proper indentation
        if level > 1:
            for _ in range(level - 1):
                toc_html += '  '
        toc_html += f'<li><a href="#{heading_id}">{clean_text}</a></li>\n'
    
    toc_html += '</ul>\n'
    
    # Find and replace the toc-content div
    toc_content_pattern = r'(<div[^>]*class="toc-content[^"]*"[^>]*>).*?(</div>)'
    if re.search(toc_content_pattern, html_content, re.DOTALL):
        # Replace content inside .toc-content div
        html_content = re.sub(
            toc_content_pattern,
            r'\1' + toc_html + r'\2',
            html_content,
            flags=re.DOTALL
        )
        print("✓ TOC inserted into sidebar")
    else:
        print("Warning: .toc-content div not found, TOC not inserted")
        return False
    
    # Save updated HTML
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ TOC inserted successfully")
        return True
        
    except Exception as e:
        print(f"Error saving HTML file: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate and insert TOC into HTML')
    parser.add_argument('-o', '--output', help='Output HTML file path (default: use config or auto-detect)')
    
    args = parser.parse_args()
    
    print("=== Book Translation Tool - Step 6: Add Table of Contents ===")
    
    # Try to find temp directory - use the correct logic to find the right temp directory
    temp_dir = None
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
        print(f"Using temp directory from config location: {temp_dir}")
    else:
        print("Warning: No temp directory with config.txt found")
        # Fall back to finding any temp directory
        if temp_dirs:
            temp_dir = temp_dirs[0]  # Use first found, not by modification time
            print(f"Using fallback temp directory: {temp_dir}")
    
    # Load configuration
    config = load_config(temp_dir)
    
    # Determine HTML file path
    if args.output:
        html_file = args.output
        # Ensure the output directory exists
        output_dir = os.path.dirname(html_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Find the source HTML file to process - use book.html as the base
        source_html = os.path.join(temp_dir, 'book.html') if temp_dir else 'book.html'
        
        # Check if source HTML file exists
        if not os.path.exists(source_html):
            print(f"Error: Source HTML file '{source_html}' not found. Run 05_md_to_html.py first.")
            sys.exit(1)
        
        # Copy source to target location first if different
        if os.path.abspath(source_html) != os.path.abspath(html_file):
            import shutil
            shutil.copy2(source_html, html_file)
            print(f"Copied {source_html} to {html_file}")
        
    else:
        # Use book.html in temp directory directly
        html_file = os.path.join(temp_dir, 'book.html') if temp_dir else 'book.html'
        
        # Check if HTML file exists
        if not os.path.exists(html_file):
            print(f"Error: HTML file '{html_file}' not found. Run 05_md_to_html.py first.")
            sys.exit(1)
    
    # Insert TOC into HTML
    success = insert_toc_into_html(html_file)
    
    if success:
        # Generate TOC summary
        generate_toc_summary(html_file)
        
        print(f"\n✓ Table of Contents added to: {html_file}")
        
        # Show file size
        try:
            file_size = os.path.getsize(html_file)
            print(f"Final file size: {file_size:,} bytes")
        except:
            pass
        
        print("\n=== Step 6 Complete! ===")
        print(f"Your HTML file with TOC is ready: {html_file}")
    else:
        print("Error: Failed to add TOC to HTML file")
        sys.exit(1)

if __name__ == "__main__":
    main()