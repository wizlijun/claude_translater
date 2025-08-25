#!/usr/bin/env python3
import os
import sys
import re
import glob

def has_chinese(text):
    """检查文本中是否包含中文字符"""
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(chinese_pattern.search(text))

def check_md_files(input_dir):
    """检查指定目录下的output_*.md文件是否包含中文"""
    input_temp_dir = f"{input_dir}_temp"
    
    if not os.path.exists(input_temp_dir):
        print(f"错误: 目录 {input_temp_dir} 不存在")
        return False
    
    pattern = os.path.join(input_temp_dir, "output_*.md")
    md_files = glob.glob(pattern)
    
    if not md_files:
        print(f"警告: 在 {input_temp_dir} 中未找到 output_*.md 文件")
        return True
    
    files_without_chinese = []
    
    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not has_chinese(content):
                files_without_chinese.append(file_path)
                
        except Exception as e:
            print(f"错误: 无法读取文件 {file_path}: {e}")
            return False
    
    if files_without_chinese:
        print("错误: 以下文件没有包含中文内容:")
        for file_path in files_without_chinese:
            print(f"  - {file_path}")
        return False
    else:
        print(f"检查完成: 所有 {len(md_files)} 个output_*.md文件都包含中文内容")
        return True

def main():
    if len(sys.argv) != 2:
        print("用法: python check_md_is_chinese.py <input_directory>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    temp_dir = f"{input_dir}_temp"
    
    if not os.path.exists(temp_dir):
        print(f"错误: 输入目录 {temp_dir} 不存在")
        sys.exit(1)
    
    success = check_md_files(input_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()