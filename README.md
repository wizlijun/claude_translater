# Claude Translator - 文档翻译工具集

这是一个基于 Claude AI 的文档翻译工具集，支持多种文档格式的批量翻译。

[![Version](https://img.shields.io/badge/version-v2.1-blue.svg)](https://github.com/your-username/claude_translater)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://python.org)

## 🎯 最新重大更新 v2.1

### 管道优化 - Temp目录一致性修复
- **修复**: Step 4 和 Step 5 temp目录查找逻辑错误
- **优化**: 确保所有步骤使用一致的temp目录传递机制
- **增强**: 改进多项目并行处理时的目录识别
- **稳定**: 提高在多个temp目录并存时的可靠性

### 统一转换架构 - Calibre HTMLZ 方案
- **新增**: `01_convert_to_htmlz.py` - 统一文件转换脚本
- **支持格式**: PDF、DOCX、EPUB → 统一通过 Calibre 转换为 HTMLZ
- **质量提升**: 解决PDF转MD乱码问题，保持原始排版和图片
- **智能分块**: 自动按5-8K字符分割为翻译块
- **清理优化**: 自动清理Calibre标记、页码、无用标签

### 新的转换流程
```
PDF/DOCX/EPUB → Calibre → HTMLZ → 解压 → HTML + Images
                    ↓
            pypandoc → Markdown → 智能分块 → 翻译流水线
```

## 工具概览

### 1. translatebook.sh - 统一文档翻译工具 ⭐️ 主要工具
完整的文档翻译管道，支持 PDF、DOCX、EPUB 等格式，输出为 HTML 格式。

### 2. 01_convert_to_htmlz.py - 新一代转换引擎
使用 Calibre 进行高质量文件转换，替代传统PDF解析方案。

### 3. pptxtrans.py - PowerPoint翻译工具
专门用于翻译 PowerPoint 演示文稿的工具。

### 4. clean_markdown.py - Markdown清理工具
清理转换后markdown文件中的换行符和格式问题。

## 🚀 快速开始

### 1. 安装依赖
```bash
# 安装 Calibre（必需）
brew install --cask calibre  # macOS
# 或者 sudo apt-get install calibre  # Linux

# 安装 Claude CLI
# 参考：https://docs.anthropic.com/en/docs/claude-code
```

### 2. 一键翻译
```bash
# 任何格式文档翻译（自动检测并优化转换）
./translatebook.sh book.pdf
./translatebook.sh document.docx  
./translatebook.sh ebook.epub
```

### 3. 获取结果
翻译完成后，在 `output/` 目录下获得 HTML 格式的翻译文档。

## 功能特点

### 统一文档翻译工具 (translatebook.sh) ⭐️
- **支持格式**: PDF、DOCX、EPUB（统一处理）
- **新转换架构**: Calibre HTMLZ → HTML → Markdown
- **质量保证**: 解决乱码问题，完整保留图片和排版
- **智能分块**: 5-8K字符优化块大小，提高翻译质量
- **自动清理**: 
  - 去除 `{.calibre123}` 等标记
  - 去除 `:::` 开头的行
  - 去除只有数字的行（页码）
  - 去除 `.ct}` `.cn}` 结尾的行
- **7步流程**: 转换 → 翻译 → 合并 → HTML → 目录 → 格式转换
- **跳过优化**: 新架构下自动跳过步骤1-2，直接进入翻译
- **目录精确**: 每个步骤使用正确的temp目录，支持多项目并行

### 新转换引擎 (01_convert_to_htmlz.py)
- **Calibre集成**: 使用 `ebook-convert` 命令行工具
- **格式统一**: PDF/DOCX/EPUB 使用相同转换路径
- **图片保留**: 完整提取并保存到 `images/` 目录
- **内容清理**: 自动清理转换标记和无用内容
- **参数调整**: 支持自定义分块大小（默认6000字符）

## 安装要求

### 基础依赖
```bash
# Python 3.6+
python3 --version

# Claude CLI
# 参考：https://docs.anthropic.com/en/docs/claude-code

# Calibre（新增必需）
# macOS: brew install --cask calibre
# Linux: sudo apt-get install calibre
# Windows: 从 https://calibre-ebook.com/ 下载
```

### Python 包依赖
```bash
# 自动安装的包（通过 translatebook.sh）
pip install python-docx PyMuPDF ebooklib beautifulsoup4 lxml markdown Pillow pdf2image pypandoc

# PowerPoint 翻译工具额外依赖
pip install python-pptx
```

## 使用说明

### 统一文档翻译工具 ⭐️ 推荐

#### 基本用法
```bash
# 任何格式文档翻译（自动检测并优化转换）
./translatebook.sh book.pdf
./translatebook.sh document.docx  
./translatebook.sh ebook.epub

# 指定目标语言翻译
./translatebook.sh --olang en book.pdf

# 带自定义提示的专业翻译
./translatebook.sh -p "Bushcraft、石器打制领域的生僻词汇在翻译后加上(原词)，请逐行翻译，不要遗漏" book.pdf

# 清理临时目录并详细输出
./translatebook.sh --clean -v book.epub

# 只运行翻译步骤（3-4）
./translatebook.sh --start-step 3 --end-step 4 book.docx

# 只运行格式转换步骤（5-7）
./translatebook.sh --start-step 5 --end-step 7 book.docx

# 预览执行计划
./translatebook.sh --dry-run book.pdf
```

#### 新架构优势
- ✅ **无乱码**: Calibre转换解决PDF乱码问题
- ✅ **保留图片**: 完整提取和保留所有图片文件
- ✅ **智能分块**: 优化分块大小，提高翻译质量
- ✅ **自动清理**: 清除标记和页码
- ✅ **跳过步骤**: 自动跳过步骤1-2，从翻译开始

### 独立转换工具
```bash
# 单独使用新转换引擎
python3 01_convert_to_htmlz.py input.pdf --chunk-size 5000
python3 01_convert_to_htmlz.py document.docx 
python3 01_convert_to_htmlz.py ebook.epub
```

### Markdown清理工具
```bash
# 清理markdown换行符
python3 clean_markdown.py book.md
python3 clean_markdown.py temp_directory/
python3 clean_markdown.py *.md
```

## 新架构处理流程

### 1. 文件转换阶段（替代原步骤1-2）
```
输入文件 → Calibre ebook-convert → HTMLZ → 解压提取
    ↓
HTML + Images → 复制到temp目录 → input.html + images/
    ↓
pypandoc → input.md → 内容清理 → 智能分块
```

### 2. 翻译流程（步骤3-7）
```
page0001.md ~ page0042.md → Claude翻译 → 合并 → HTML → 目录 → 输出
```

### 3. Temp目录管理机制 (v2.1新增)
```
输入文件: book.pdf
    ↓
创建目录: book_temp/
    ├── config.txt          # 配置文件，记录输入文件名
    ├── input.html          # 转换后的HTML
    ├── input.md           # 转换后的Markdown
    ├── page0001.md        # 分块文件
    ├── output_page0001.md # 翻译后文件
    ├── output.md          # 合并后翻译
    ├── book.html          # 最终HTML输出
    └── images/            # 图片目录
```

**智能目录选择**：
- 基于`config.txt`中的`input_file`字段匹配对应的输入文件
- 验证temp目录名称格式：`{filename}_temp`
- 支持多项目并行：每个输入文件创建独立的temp目录
- 自动处理多个temp目录并存的情况

## 清理优化详情

### 自动清理规则
1. **Calibre标记**: 删除 `{.calibre123}` 等标记
2. **容器标记**: 删除 `:::` 开头的行
3. **页码清理**: 删除只有数字的行
4. **特殊标记**: 删除 `.ct}` `.cn}` 结尾的行
5. **空行优化**: 合并多个连续空行

### 转换质量对比
| 转换方式 | 文件大小 | 图片保留 | 乱码问题 | 分块质量 |
|---------|---------|----------|----------|----------|
| 旧方案(PDF直接) | 小 | 部分丢失 | 严重 | 一般 |
| 新方案(Calibre) | 大 | 完整保留 | 无 | 优秀 |

## 参数说明

### translatebook.sh 主要参数
- `-l, --ilang`: 输入语言（默认：auto）
- `--olang`: 目标语言（默认：zh）
- `-p, --prompt`: 自定义翻译提示
- `--clean`: 清理临时目录
- `--no-skip`: 不跳过已存在的中间文件
- `--reinstall-packages`: 重新安装Python包
- `--start-step NUM`: 从指定步骤开始（1-7）
- `--end-step NUM`: 在指定步骤结束（1-7）
- `--dry-run`: 预览执行计划
- `-v, --verbose`: 详细输出
- `-h, --help`: 显示帮助信息

### 01_convert_to_htmlz.py 参数
- `--chunk-size`: 分块大小（默认6000字符）
- `-l, --ilang`: 输入语言
- `--olang`: 输出语言
- `-o, --output`: 输出文件名

## 🔧 故障排除

### 新架构常见问题

| 问题 | 解决方案 |
|------|----------|
| Calibre未安装 | `brew install --cask calibre` (macOS) 或 `sudo apt-get install calibre` (Linux) |
| pypandoc缺失 | `pip install pypandoc` |
| 转换失败 | 检查文件格式和Calibre版本 |
| 权限问题 | 确保脚本有执行权限：`chmod +x translatebook.sh` |
| temp目录错误 | v2.1已修复，确保使用最新版本 |
| 多项目冲突 | 每个项目都会创建独立的`{filename}_temp`目录 |

### 调试建议
```bash
# 详细输出查看转换过程
./translatebook.sh -v --dry-run book.pdf

# 单独测试转换
python3 01_convert_to_htmlz.py book.pdf --chunk-size 5000

# 检查环境
which calibre  # 检查Calibre是否正确安装
python3 -c "import pypandoc; print('pypandoc OK')"  # 检查pypandoc
```

## 性能优化

### 新架构优势
- **内存效率**: 分块处理大文件
- **并行支持**: 可并行翻译多个块
- **缓存复用**: 避免重复转换
- **错误恢复**: 支持断点续传

### 推荐配置
- **小文件**: 默认6000字符分块
- **大文件**: 可调整为5000字符分块
- **专业翻译**: 使用详细自定义提示

---

## 版本历史

### v2.1 (当前版本) - 2025年8月更新
- 🔧 修复Step 4和Step 5的temp目录查找逻辑
- 🎯 确保所有步骤使用一致的temp目录传递机制
- 🔄 增强多项目并行处理支持
- ⚡ 提高在多个temp目录并存时的可靠性
- 📦 添加`--temp-dir`参数支持各个步骤

### v2.0 - 2025年7月更新
- ✨ 新增 Calibre HTMLZ 统一转换架构
- 🚀 解决PDF转MD乱码问题
- 🖼️ 完整保留图片和排版
- 🧹 智能内容清理和优化
- ⚡ 自动跳过无用步骤，提高效率
- 🔧 优化核心转换脚本和处理流程
- 📦 更新依赖管理和环境配置

### v1.0
- 基础PDF/DOCX/EPUB翻译功能
- 7步处理流程
- Claude API集成

## 项目状态

📅 **最后更新**: 2025年8月  
✅ **状态**: 活跃开发中  
🔄 **架构**: v2.1 Calibre HTMLZ 统一转换 + 管道优化  
🎯 **主要功能**: PDF/DOCX/EPUB → 中文翻译 → HTML输出  
🔧 **最新改进**: 修复temp目录逻辑，支持多项目并行  

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境
```bash
git clone https://github.com/your-username/claude_translater.git
cd claude_translater
chmod +x translatebook.sh
```

### 测试
```bash
# 测试基本功能
./translatebook.sh --dry-run test.pdf

# 测试转换引擎
python3 01_convert_to_htmlz.py test.pdf --chunk-size 5000
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

*本工具集基于 Claude AI 和 Calibre 提供高质量文档翻译服务，致力于解决多格式文档转换和翻译中的实际问题。*
