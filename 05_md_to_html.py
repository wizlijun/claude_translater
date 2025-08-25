#!/usr/bin/env python3
"""
Step 5: Convert markdown to HTML using template
Converts output.md to HTML with images and template
"""

import os
import sys
import shutil
import subprocess
import re
from pathlib import Path

# Try to import markdown, fallback to basic conversion if not available
try:
    import markdown
    from markdown.extensions import toc, tables, fenced_code, codehilite
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

def translate_title_with_claude(title, target_lang, custom_prompt=None):
    """Translate book title using Claude CLI"""
    if not title or not title.strip():
        return "翻译书籍"  # Default fallback
    
    try:
        print(f"Translating title '{title}' to {target_lang}...")
        
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
- First line must be: <!-- START -->
- Then the translated title (only the title, nothing else)
- Last line must be: <!-- END -->
- Do not add any explanations, warnings, code block markers, or other content
- Absolutely do not output any markdown code block markers (like ```markdown or ```)
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
                print(f"✓ Title translated: '{title}' -> '{translated_title}'")
                return translated_title
            else:
                print(f"Warning: Failed to extract title from markers. Raw output: {raw_output[:100]}...")
                print(f"Using original title: {title}")
                return title
        else:
            print(f"Warning: Title translation failed, using original: {stderr}")
            return title
            
    except Exception as e:
        print(f"Warning: Error translating title: {e}, using original")
        return title

def load_config(temp_dir):
    """Load configuration from step 1"""
    config_file = os.path.join(temp_dir, 'config.txt')
    if not os.path.exists(config_file):
        print("Error: config.txt not found. Run 01_prepare_env.py first.")
        sys.exit(1)
    
    config = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    
    return config

def check_pandoc_available():
    """Check if pandoc is available"""
    try:
        subprocess.run(['pandoc', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_with_pandoc(md_file, html_file, template_file=None, title="翻译书籍"):
    """Convert markdown to HTML using pandoc"""
    print("Converting markdown to HTML using pandoc...")
    
    cmd = ['pandoc', md_file, '-o', html_file]
    
    # Use template if available
    if template_file and os.path.exists(template_file):
        cmd.extend(['--template', template_file])
        print(f"  Using template: {template_file}")
    
    # Add useful pandoc options
    cmd.extend([
        '--standalone',
        '--metadata', f'title={title}',
        '--metadata', 'lang=zh-CN',
        '--from', 'markdown+smart+east_asian_line_breaks',
        '--to', 'html5'
    ])
    
    try:
        print(f"  Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✓ Successfully converted with pandoc")
        
        # Verify output file was created
        if os.path.exists(html_file):
            file_size = os.path.getsize(html_file)
            print(f"  Output file: {html_file} ({file_size:,} bytes)")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Pandoc conversion failed: {e.stderr}")
        if e.stdout:
            print(f"  Stdout: {e.stdout}")
        return False

def apply_template_to_html(html_content, template_file, output_file, title="翻译书籍"):
    """Apply a template to HTML content and save to output file"""
    if not template_file or not os.path.exists(template_file):
        print(f"Warning: Template {template_file} not found, using default template")
        full_html = create_default_html(html_content, title)
    else:
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Replace placeholder with content
            if '$body$' in template_content:
                full_html = template_content.replace('$body$', html_content)
            elif '{{content}}' in template_content:
                full_html = template_content.replace('{{content}}', html_content)
            elif '{content}' in template_content:
                full_html = template_content.replace('{content}', html_content)
            else:
                # If no placeholder found, insert before </body>
                if '</body>' in template_content:
                    full_html = template_content.replace('</body>', f'{html_content}\n</body>')
                else:
                    full_html = template_content + html_content
                    
            # Handle title placeholder
            if '$title$' in full_html:
                full_html = full_html.replace('$title$', title)
                
        except Exception as e:
            print(f"Error reading template {template_file}: {e}")
            full_html = create_default_html(html_content, title)
    
    # Save HTML file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"✓ HTML file created with template: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving HTML file {output_file}: {e}")
        return False

def convert_with_python_markdown(md_file, html_file, template_file=None, title="翻译书籍"):
    
    print("Converting markdown to HTML using python-markdown...")
    
    # Read markdown content
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except Exception as e:
        print(f"Error reading markdown file: {e}")
        return False
    
    # Configure markdown extensions
    extensions = [
        'toc',
        'tables',
        'fenced_code',
        'codehilite',
        'nl2br'
    ]
    
    # Create markdown processor
    md = markdown.Markdown(extensions=extensions)
    
    # Convert to HTML
    html_content = md.convert(md_content)
    
    # Load template if available
    if template_file and os.path.exists(template_file):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Replace placeholder with content
            if '{{content}}' in template_content:
                full_html = template_content.replace('{{content}}', html_content)
            elif '{content}' in template_content:
                full_html = template_content.replace('{content}', html_content)
            elif '$body$' in template_content:
                full_html = template_content.replace('$body$', html_content)
            else:
                # If no placeholder found, insert before </body>
                if '</body>' in template_content:
                    full_html = template_content.replace('</body>', f'{html_content}\n</body>')
                else:
                    full_html = template_content + html_content
        except Exception as e:
            print(f"Error reading template: {e}")
            full_html = create_default_html(html_content, title)
    else:
        full_html = create_default_html(html_content)
    
    # Save HTML file
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print("✓ Successfully converted with python-markdown")
        return True
    except Exception as e:
        print(f"Error saving HTML file: {e}")
        return False

def convert_with_basic_markdown(md_file, html_file, template_file=None):
    """Convert markdown to HTML using basic regex replacements"""
    print("Converting markdown to HTML using basic conversion...")
    
    # Read markdown content
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except Exception as e:
        print(f"Error reading markdown file: {e}")
        return False
    
    # Basic markdown to HTML conversion
    html_content = md_content
    
    # Headers
    html_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html_content, flags=re.MULTILINE)
    
    # Bold and italic
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
    html_content = re.sub(r'_(.*?)_', r'<em>\1</em>', html_content)
    
    # Links
    html_content = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'<a href="\2">\1</a>', html_content)
    
    # Lists and paragraphs
    lines = html_content.split('\n')
    result_lines = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = 'ul'
            item = line.strip()[2:]
            result_lines.append(f'<li>{item}</li>')
        elif re.match(r'^\d+\. ', line.strip()):
            if not in_list:
                result_lines.append('<ol>')
                in_list = 'ol'
            item = re.sub(r'^\d+\. ', '', line.strip())
            result_lines.append(f'<li>{item}</li>')
        else:
            if in_list:
                result_lines.append(f'</{in_list}>')
                in_list = False
            
            if line.strip() and not line.startswith('<'):
                result_lines.append(f'<p>{line}</p>')
            else:
                result_lines.append(line)
    
    if in_list:
        result_lines.append(f'</{in_list}>')
    
    html_content = '\n'.join(result_lines)
    
    # Page separators
    html_content = re.sub(r'---', '<div class="page-separator"></div>', html_content)
    
    # Load template if available
    if template_file and os.path.exists(template_file):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Replace placeholder with content
            if '{{content}}' in template_content:
                full_html = template_content.replace('{{content}}', html_content)
            elif '{content}' in template_content:
                full_html = template_content.replace('{content}', html_content)
            elif '$body$' in template_content:
                full_html = template_content.replace('$body$', html_content)
            else:
                # If no placeholder found, insert before </body>
                if '</body>' in template_content:
                    full_html = template_content.replace('</body>', f'{html_content}\n</body>')
                else:
                    full_html = template_content + html_content
        except Exception as e:
            print(f"Error reading template: {e}")
            full_html = create_default_html(html_content, title)
    else:
        full_html = create_default_html(html_content)
    
    # Save HTML file
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print("✓ Successfully converted with basic markdown converter")
        return True
    except Exception as e:
        print(f"Error saving HTML file: {e}")
        return False

def create_default_html(content, title="翻译书籍"):
    """Create default HTML template"""
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h2 {{
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        pre {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }}
        
        code {{
            background-color: #f1f3f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #555;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        
        .page-separator {{
            border-top: 2px solid #e9ecef;
            margin: 40px 0;
            padding-top: 20px;
        }}
        
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            
            h1 {{
                font-size: 1.5em;
            }}
            
            h2 {{
                font-size: 1.3em;
            }}
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""

def copy_images_to_output(temp_dir, output_dir):
    """Copy image files to output directory"""
    print("Copying images to output directory...")
    
    # Find all image files in temp directory
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(temp_dir, f'*{ext}')
        import glob
        image_files.extend(glob.glob(pattern))
    
    if not image_files:
        print("No image files found")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy images
    copied_count = 0
    for img_file in image_files:
        try:
            filename = os.path.basename(img_file)
            dest_path = os.path.join(output_dir, filename)
            shutil.copy2(img_file, dest_path)
            print(f"  Copied: {filename}")
            copied_count += 1
        except Exception as e:
            print(f"  Error copying {filename}: {e}")
    
    print(f"Copied {copied_count} image files")

def process_html_separators(html_file):
    """Process page separators in HTML"""
    print("Processing page separators...")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace markdown separators with HTML
        content = re.sub(
            r'<hr\s*/?>',
            '<div class="page-separator"></div>',
            content
        )
        
        # Also handle the specific separator format
        content = re.sub(
            r'<p>\s*---\s*</p>',
            '<div class="page-separator"></div>',
            content
        )
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ Page separators processed")
        
    except Exception as e:
        print(f"Error processing separators: {e}")

def main():
    """Main function"""
    print("=== Book Translation Tool - Step 5: Markdown to HTML ===")
    
    # Find temp directory
    temp_dirs = [d for d in os.listdir('.') if d.endswith('_temp')]
    if not temp_dirs:
        print("Error: No temp directory found. Run 01_prepare_env.py first.")
        sys.exit(1)
    
    temp_dir = max(temp_dirs, key=lambda d: os.path.getmtime(d))
    print(f"Using temp directory: {temp_dir}")
    
    # Load configuration
    config = load_config(temp_dir)
    
    # Translate book title if available
    original_title = config.get('original_title', '')
    output_lang = config.get('output_lang', 'zh')
    custom_prompt = config.get('custom_prompt', None)
    translated_title = "翻译书籍"  # Default fallback
    
    if original_title:
        translated_title = translate_title_with_claude(original_title, output_lang, custom_prompt)
        # Add book title marks (书名号) for Chinese titles
        if output_lang == 'zh':
            translated_title = f"《{translated_title}》"
        print(f"Using translated title: {translated_title}")
    else:
        print("No original title found in config, using default title")
    
    # Check if output.md exists
    md_file = os.path.join(temp_dir, 'output.md')
    if not os.path.exists(md_file):
        print("Error: output.md not found. Run 04_merge_md.py first.")
        sys.exit(1)
    
    # Generate output.html in the temp directory first (without template)
    temp_html_file = os.path.join(temp_dir, 'output.html')
    
    # Try pandoc first, then fallback to python-markdown
    success = False
    
    if check_pandoc_available():
        success = convert_with_pandoc(md_file, temp_html_file, None, translated_title)  # No template for raw HTML
    
    if not success:
        print("Pandoc not available or failed, trying python-markdown...")
        success = convert_with_python_markdown(md_file, temp_html_file, None, translated_title)  # No template for raw HTML
    
    if not success:
        print("Error: Failed to convert markdown to HTML")
        sys.exit(1)
    
    # Copy images to temp directory
    copy_images_to_output(temp_dir, temp_dir)
    
    # Process HTML separators
    process_html_separators(temp_html_file)
    
    # Read the raw HTML content
    try:
        with open(temp_html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        sys.exit(1)
    
    # Extract only the body content from the HTML
    import re
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    if body_match:
        body_content = body_match.group(1).strip()
    else:
        # If no body tag found, use the entire content
        body_content = html_content
    
    # Generate book_doc.html with template_ebook.html template
    book_doc_file = os.path.join(temp_dir, 'book_doc.html')
    template_ebook_file = 'template_ebook.html'
    apply_template_to_html(body_content, template_ebook_file, book_doc_file, translated_title)
    
    # Generate book.html with template.html template
    book_file = os.path.join(temp_dir, 'book.html')
    template_file = 'template.html'
    apply_template_to_html(body_content, template_file, book_file, translated_title)
    
    print(f"\n✓ Generated HTML files:")
    print(f"  - Raw HTML: {temp_html_file}")
    print(f"  - eBook template: {book_doc_file}")
    print(f"  - Web template: {book_file}")
    
    # Show file sizes
    try:
        for file_path in [temp_html_file, book_doc_file, book_file]:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"  {os.path.basename(file_path)}: {file_size:,} bytes")
    except:
        pass
    
    print("\n=== Step 5 Complete ===")
    print("Next step: Run 06_add_toc.py")

if __name__ == "__main__":
    main()