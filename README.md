# Claude Translator - 文档翻译工具集

这是一个基于 Claude AI 的文档翻译工具集，支持多种文档格式的批量翻译。

## 工具概览

### 1. pptxtrans.py - PowerPoint翻译工具
专门用于翻译 PowerPoint 演示文稿的工具，支持文本框、表格、图表等多种元素的翻译。

### 2. translatebook.sh - 电子书和文档翻译工具
完整的文档翻译管道，支持 PDF、DOCX、EPUB 等格式，输出为 HTML 格式。

## 功能特点

### PowerPoint 翻译工具 (pptxtrans.py)
- **支持格式**: PPTX 文件
- **翻译元素**: 文本框、表格、图表标题、占位符
- **分步处理**: 文本提取 → 翻译 → 应用翻译
- **缓存机制**: 避免重复翻译相同内容
- **错误恢复**: 支持失败重试和断点续传

### 电子书翻译工具 (translatebook.sh)
- **支持格式**: PDF、DOCX、EPUB
- **输出格式**: HTML（主要）、DOCX、EPUB
- **7步处理流程**: 环境准备 → 文件分割 → 翻译 → 合并 → HTML转换 → 目录生成 → 格式转换
- **自动化**: 虚拟环境管理，依赖包自动安装
- **灵活控制**: 支持指定执行步骤范围

## 安装要求

### 基础依赖
```bash
# Python 3.6+
python3 --version

# Claude CLI
# 参考：https://docs.anthropic.com/en/docs/claude-code
```

### Python 包依赖
```bash
# PowerPoint 翻译工具
pip install python-pptx

# 电子书翻译工具（自动安装）
pip install python-docx PyMuPDF ebooklib beautifulsoup4 lxml markdown Pillow pdf2image
```

## 使用说明

### PowerPoint 翻译工具

#### 基本用法
```bash
# 完整翻译（推荐）
python3 pptxtrans.py input.pptx --olang zh -o output.pptx

# 分步执行
python3 pptxtrans.py input.pptx --extract-text
python3 pptxtrans.py input.pptx --translate-json --olang zh
python3 pptxtrans.py input.pptx --apply-translations -o output.pptx
```

#### 参数说明
- `--olang`: 目标语言（zh/en/ja/ko/fr/de/es/it/pt/ru/ar/hi/th/vi）
- `-o, --output`: 输出文件路径
- `-p, --prompt`: 自定义翻译提示
- `--extract-text`: 仅提取文本到 JSON
- `--translate-json`: 仅翻译 JSON 文件
- `--apply-translations`: 仅应用翻译到 PPT

### 电子书翻译工具

#### 基本用法
```bash
# 完整翻译
./translatebook.sh --olang zh book.pdf

# 自定义输出
./translatebook.sh --olang en -o english_book.html book.epub

# 使用自定义提示
./translatebook.sh -p "专业技术翻译，保持术语准确" book.docx
```

#### 参数说明
- `--olang`: 目标语言
- `-o, --output`: 输出 HTML 文件
- `-p, --prompt`: 自定义翻译提示
- `--clean`: 清理临时目录
- `--start-step, --end-step`: 指定执行步骤范围（1-7）
- `--dry-run`: 预览执行计划
- `-v, --verbose`: 详细输出

#### 处理步骤
1. 环境准备和参数解析
2. 文件分割为 Markdown 并提取图片
3. 使用 Claude API 翻译 Markdown 文件
4. 合并翻译后的 Markdown 文件
5. 转换 Markdown 为 HTML
6. 生成和插入目录
7. 生成 DOCX 和 EPUB 格式文件

## 高级用法

### 自定义翻译提示
```bash
# PowerPoint
python3 pptxtrans.py input.pptx --olang zh -p "商务演示翻译，保持专业术语" -o output.pptx

# 电子书
./translatebook.sh --olang en -p "学术论文翻译，保持引用格式" paper.pdf
```

### 部分步骤执行
```bash
# 仅执行翻译步骤
./translatebook.sh --start-step 3 --end-step 4 book.pdf

# 仅执行格式转换
./translatebook.sh --start-step 5 --end-step 7 book.pdf
```

### 错误处理和恢复
```bash
# 清理后重新开始
./translatebook.sh --clean book.pdf

# 不跳过已存在文件
./translatebook.sh --no-skip book.pdf
```

## 输出结果

### PowerPoint 翻译
- 输出文件：完整翻译的 PPTX 文件
- 中间文件：`{输入文件}_temp_{语言}/` 目录中的 JSON 文件
- 支持断点续传和缓存复用

### 电子书翻译
- 主要输出：HTML 文件（带样式和目录）
- 附加输出：DOCX 和 EPUB 文件（在临时目录中）
- 中间文件：Markdown 文件、图片、翻译缓存等

## 注意事项

1. **Claude CLI 配置**: 确保 Claude CLI 已正确安装和配置
2. **网络连接**: 翻译过程需要稳定的网络连接
3. **文件路径**: 避免使用包含特殊字符的文件路径
4. **大文件处理**: 大文件翻译可能需要较长时间，建议使用分步执行
5. **中间文件**: 保留中间文件可用于调试和续传

## 故障排除

### 常见问题
1. **Claude CLI 未找到**: 确保 Claude CLI 在 PATH 中
2. **Python 包缺失**: 使用 `--reinstall-packages` 重新安装
3. **翻译失败**: 检查网络连接和 Claude API 配额
4. **文件格式不支持**: 确认输入文件格式正确

### 调试模式
```bash
# 详细输出
./translatebook.sh -v book.pdf

# 预览执行
./translatebook.sh --dry-run book.pdf
```

## 联系方式

如有问题或建议，请通过以下方式联系：
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)

## 许可证

本工具集遵循开源许可证，请查看 LICENSE 文件获取详细信息。

---

*本工具集基于 Claude AI 提供智能翻译服务，旨在提高文档翻译效率和质量。*
