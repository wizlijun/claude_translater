# Claude Translator - 文档翻译工具集

这是一个基于 Claude AI 的文档翻译工具集，支持多种文档格式的批量翻译。

## 🎯 最新重大更新 v2.0

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

## 故障排除

### 新架构常见问题
1. **Calibre未安装**: 
   ```bash
   # macOS
   brew install --cask calibre
   # Linux  
   sudo apt-get install calibre
   ```

2. **pypandoc缺失**:
   ```bash
   pip install pypandoc
   ```

3. **转换失败**: 检查文件格式和Calibre版本

### 调试建议
```bash
# 详细输出查看转换过程
./translatebook.sh -v --dry-run book.pdf

# 单独测试转换
python3 01_convert_to_htmlz.py book.pdf --chunk-size 5000
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

### v2.0 (当前版本) - 2025年7月更新
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

📅 **最后更新**: 2025年7月  
✅ **状态**: 活跃开发中  
🔄 **架构**: v2.0 Calibre HTMLZ 统一转换  
🎯 **主要功能**: PDF/DOCX/EPUB → 中文翻译 → HTML输出  

---

*本工具集基于 Claude AI 和 Calibre 提供高质量文档翻译服务，致力于解决多格式文档转换和翻译中的实际问题。*
