#!/usr/bin/env python3
"""
Step 3: Translate markdown files using Claude CLI
Translates each pageXXXX.md file to output_pageXXXX.md
"""

import os
import sys
import glob
import time
import argparse
import subprocess
import tempfile
from pathlib import Path

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

def check_claude_cli():
    """Check if Claude CLI is available"""
    try:
        result = subprocess.run(['claude', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_info = result.stdout.strip().split('\n')[-1]
            print(f"Claude CLI available: {version_info}")
            return True
        else:
            print(f"Claude CLI check failed with code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print("Error: Claude CLI version check timed out")
        return False
    except FileNotFoundError:
        print("Error: 'claude' command not found")
        print("Please ensure Claude CLI is installed and in your PATH")
        return False
    except Exception as e:
        print(f"Error checking Claude CLI: {e}")
        return False

def get_language_name(lang_code):
    """Convert language code to full name"""
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
        'ru': 'Russian',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'th': 'Thai',
        'vi': 'Vietnamese'
    }
    return lang_map.get(lang_code.lower(), lang_code)

def create_translation_prompt(output_lang, custom_prompt=None):
    """Create translation prompt with optional custom additions"""
    lang_name = get_language_name(output_lang)
    
    base_prompt = f"""请翻译markdown文件为 {lang_name}. 
IMPORTANT REQUIREMENTS:
1.	严格保持 Markdown 格式不变，包括标题、链接、图片引用等
2.	仅翻译文字内容，保留所有 Markdown 语法和文件名
3.	删除页码、空链接、不必要的字符和如: 行末的'\\' 
4.	删除只有数字的行，那可能是页码
5. 使用 Sonnet 4 模型完成，保证格式和语义准确翻译内容自然流畅
6.	只输出翻译后的正文内容，不要有任何说明、提示、注释或对话内容。
7.  CRITICAL OUTPUT FORMAT: 你的回复必须严格遵循以下格式：
    - 第一行必须是：<!-- START -->
    - 然后是翻译后的markdown内容
    - 最后一行必须是：<!-- END -->
    - 不要在这些标记之前或之后添加任何说明、警告、代码块标记或其他内容
    - 绝对不要输出任何markdown代码块标记（如```markdown或```）
    - 不要输出任何解释性文字或元数据
    - 不要输出"我来帮您翻译"、"以下是翻译结果"等开场白
    - 不要输出任何关于翻译质量、注意事项的说明
    - 严格按照：<!-- START -->[翻译内容]<!-- END --> 的格式输出
    - 如果输出不符合此格式，系统将重新请求翻译
8.  表达清晰简洁，不要使用复杂的句式。请严格按顺序翻译，不要跳过任何内容。
9.  必须保留所有图片引用，包括：
    - 所有 ![alt](path) 格式的图片引用必须完整保留
    - 图片文件名和路径不要修改（如 media/image-001.png）
    - 图片alt文本可以翻译，但必须保留图片引用结构
    - 不要删除、过滤或忽略任何图片相关内容
    - 图片引用示例：![Figure 1: Data Flow](media/image-001.png) → ![图1：数据流](media/image-001.png)
10. 智能识别和处理多级标题，按照以下规则添加markdown标记：
    - 主标题（书名、章节名等）使用 # 标记
    - 一级标题（大节标题）使用 ## 标记  
    - 二级标题（小节标题）使用 ### 标记
    - 三级标题（子标题）使用 #### 标记
    - 四级及以下标题使用 ##### 标记
11. 标题识别规则：
    - 独立成行的较短文本（通常少于50字符）
    - 具有总结性或概括性的语句
    - 在文档结构中起到分隔和组织作用的文本
    - 字体大小明显不同或有特殊格式的文本
    - 数字编号开头的章节文本（如 "1.1 概述"、"第三章"等）
12. 标题层级判断：
    - 根据上下文和内容重要性判断标题层级
    - 章节类标题通常为高层级（# 或 ##）
    - 小节、子节标题依次降级（### #### #####）
    - 保持同一文档内标题层级的一致性
13. 注意事项：
    - 不要过度添加标题标记，只对真正的标题文本添加
    - 正文段落不要添加标题标记
    - 如果原文已有markdown标题标记，保持其层级结构"""
    if custom_prompt:
        base_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt}"
    
    base_prompt += "\n\n markdown文件正文:"
    
    return base_prompt

def translate_with_claude_cli(text, output_lang, custom_prompt=None, max_retries=3):
    """Translate text using Claude CLI with retry mechanism and real-time output"""
    
    # Create translation prompt
    prompt = create_translation_prompt(output_lang, custom_prompt)
    
    def run_claude_with_realtime_output(full_input, attempt_num):
        """Run Claude CLI and show real-time output"""
        print(f"    Starting Claude translation (attempt {attempt_num})...")
        
        try:
            # Start Claude process
            command = ['claude']
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True
            )
            
            # Send input to Claude
            stdout, stderr = process.communicate(input=full_input, timeout=180)
            
            # Show real-time output
            if stdout:
                print("    Claude output:")
                # Split output into lines and print with indentation
                for line in stdout.split('\n'):
                    if line.strip():
                        print(f"      {line}")
                print("    Claude output complete.")
            
            return process.returncode, stdout, stderr
            
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", "Translation timeout (3 minutes)"
        except Exception as e:
            return -1, "", str(e)
    
    for attempt in range(max_retries):
        if attempt > 0:
            print(f"    Retry attempt {attempt + 1}/{max_retries}")
            time.sleep(1)  # Brief delay before retry
        
        try:
            # Prepare the full input text
            full_input = f"{prompt}\n\n{text}"
            
            # Run Claude with real-time output
            returncode, stdout, stderr = run_claude_with_realtime_output(full_input, attempt + 1)
            
            if returncode == 0:
                translated_text = stdout.strip()
                
                # Strictly extract content between START and END markers
                def extract_content_between_markers(text):
                    """Strictly extract content between START and END markers"""
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
                
                # Try to extract content
                extracted_content = extract_content_between_markers(translated_text)
                
                if extracted_content and len(extracted_content.strip()) > 0:
                    if attempt > 0:
                        print(f"    ✓ Translation successful on attempt {attempt + 1}")
                    return extracted_content
                else:
                    # Show detailed debug information
                    print(f"    Attempt {attempt + 1}: Failed to extract content between START/END markers")
                    print(f"    Raw output (first 300 chars): {translated_text[:300]}...")
                    
                    # Check if markers exist at all
                    has_start = False
                    has_end = False
                    
                    start_variations = ['<!-- START -->', '<!--START-->', '<!-- START-->', '<!--START -->']
                    end_variations = ['<!-- END -->', '<!--END-->', '<!-- END-->', '<!--END -->']
                    
                    for var in start_variations:
                        if var in translated_text:
                            has_start = True
                            print(f"    Found START marker: {var}")
                            break
                    
                    for var in end_variations:
                        if var in translated_text:
                            has_end = True
                            print(f"    Found END marker: {var}")
                            break
                    
                    if not has_start:
                        print(f"    No START marker found")
                    if not has_end:
                        print(f"    No END marker found")
                    
                    # Last resort: if both markers exist but extraction failed, try emergency extraction
                    if has_start and has_end:
                        print(f"    Attempting emergency extraction...")
                        lines = translated_text.split('\n')
                        start_line = -1
                        end_line = -1
                        
                        for i, line in enumerate(lines):
                            if any(marker in line for marker in start_variations):
                                start_line = i
                            if any(marker in line for marker in end_variations):
                                end_line = i
                                break
                        
                        if start_line != -1 and end_line != -1 and start_line < end_line:
                            emergency_content = '\n'.join(lines[start_line+1:end_line]).strip()
                            if emergency_content:
                                print(f"    Emergency extraction successful")
                                return emergency_content
                    
                    continue  # Retry
            else:
                error_msg = stderr.strip() if stderr else "No error message"
                print(f"    Attempt {attempt + 1}: Claude CLI error (code {returncode}): {error_msg}")
                continue  # Retry
                
        except FileNotFoundError:
            print(f"    Error: 'claude' command not found. Please ensure Claude CLI is installed and in PATH")
            return None  # Don't retry for this error
        except Exception as e:
            print(f"    Attempt {attempt + 1}: Error calling Claude CLI: {e}")
            continue  # Retry
    
    # All retries failed
    print(f"    ✗ Translation failed after {max_retries} attempts, skipping file")
    return None

def translate_markdown_files(temp_dir, output_lang, custom_prompt=None):
    """Translate all markdown files in temp directory"""
    print(f"Translating markdown files to {output_lang}...")
    if custom_prompt:
        print(f"Using custom prompt: {custom_prompt[:100]}...")
    
    # Find all pageXXXX.md files
    md_files = glob.glob(os.path.join(temp_dir, 'page*.md'))
    md_files.sort()
    
    if not md_files:
        print("Error: No markdown files found. Run 02_split_to_md.py first.")
        sys.exit(1)
    
    total_files = len(md_files)
    translated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, md_file in enumerate(md_files, 1):
        filename = os.path.basename(md_file)
        output_filename = f"output_{filename}"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Skip if output file already exists
        if os.path.exists(output_path):
            print(f"  [{i}/{total_files}] Skipping {filename} (already translated)")
            skipped_count += 1
            continue
        
        print(f"  [{i}/{total_files}] Translating {filename}...")
        
        # Read input file
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"    Error reading {filename}: {e}")
            failed_count += 1
            continue
        
        # Skip if file is empty or very short
        if len(content.strip()) < 1:
            print(f"    Skipping {filename} (too short)")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            skipped_count += 1
            continue
        
        # Translate with Claude CLI
        translated_content = translate_with_claude_cli(content, output_lang, custom_prompt)
        
        if translated_content:
            # Save translated content
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(translated_content)
                print(f"    ✓ Translated and saved to {output_filename}")
                translated_count += 1
            except Exception as e:
                print(f"    Error saving {output_filename}: {e}")
                failed_count += 1
        else:
            # Translation failed after all retries - skip file creation completely
            print(f"    ✗ Failed to translate {filename} after retries, skipping file creation")
            failed_count += 1
        
        # Add delay to avoid rate limits
        if i < total_files:
            time.sleep(0.5)  # Reduced delay for CLI
    
    print(f"\nTranslation complete:")
    print(f"  Translated: {translated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {total_files}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Book Translation Tool - Step 3: Translate Markdown using Claude CLI"
    )
    
    parser.add_argument(
        '-p', '--prompt',
        default=None,
        help="Additional custom prompt to add to the translation instructions"
    )
    
    parser.add_argument(
        '--temp-dir',
        required=True,
        help="Temp directory path (required)"
    )
    
    parser.add_argument(
        '--output-lang',
        default=None,
        help="Override output language from config"
    )
    
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help="Retry translating files that failed previously"
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    print("=== Book Translation Tool - Step 3: Translate Markdown (Claude CLI) ===")
    
    # Parse arguments
    args = parse_arguments()
    
    # Check Claude CLI availability
    if not check_claude_cli():
        sys.exit(1)
    
    # Find temp directory
    temp_dir = args.temp_dir
    if not os.path.exists(temp_dir):
        print(f"Error: Specified temp directory not found: {temp_dir}")
        sys.exit(1)
    
    print(f"Using temp directory: {temp_dir}")
    
    # Load configuration
    config = load_config(temp_dir)
    output_lang = args.output_lang or config['output_lang']
    
    print(f"Target language: {output_lang}")
    
    if args.prompt:
        print(f"Custom prompt: {args.prompt}")
    
    # If retry failed, remove existing output files that might be incomplete
    if args.retry_failed:
        print("Retry mode: removing potentially incomplete translation files...")
        output_files = glob.glob(os.path.join(temp_dir, 'output_page*.md'))
        for output_file in output_files:
            try:
                # Check if file is very small (likely failed)
                if os.path.getsize(output_file) < 50:
                    os.remove(output_file)
                    print(f"  Removed: {os.path.basename(output_file)}")
            except:
                pass
    
    # Translate markdown files
    translate_markdown_files(temp_dir, output_lang, args.prompt)
    
    print("\n=== Step 3 Complete ===")
    print("Next step: Run 04_merge_md.py")

if __name__ == "__main__":
    main()