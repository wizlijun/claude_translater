#!/bin/bash

# Book Translation Tool - Complete Pipeline Script
# Usage: ./translatebook.sh [options] input_file
# Example: ./translatebook.sh --olang zh --clean sample.pdf

set -e  # Exit on any error

# Script information
SCRIPT_NAME="translatebook.sh"
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
INPUT_FILE=""
INPUT_LANG="auto"
OUTPUT_LANG="zh"
CUSTOM_PROMPT=""
CLEAN_TEMP=false
SKIP_EXISTING=true
VERBOSE=false
DRY_RUN=false
STEP_START=1
STEP_END=7
REINSTALL_PACKAGES=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP $1]${NC} $2"
}

# Help function
show_help() {
    cat << EOF
${SCRIPT_NAME} v${VERSION} - Book Translation Tool

DESCRIPTION:
    Translates PDF, DOCX, or EPUB files to HTML using Claude CLI.
    Automatically runs all 7 steps in sequence.
    Creates and manages Python virtual environment automatically.
    Uses Calibre for unified file conversion via HTMLZ format.

USAGE:
    ${SCRIPT_NAME} [OPTIONS] INPUT_FILE

OPTIONS:
    -l, --ilang LANG        Input language (default: auto)
    --olang LANG           Output language (default: zh)
    -p, --prompt TEXT      Custom prompt for translation (step 3)
    --clean                Clean temp directory before starting
    --no-skip              Don't skip existing intermediate files
    --reinstall-packages   Reinstall Python packages in virtual environment
    --start-step NUM       Start from step NUM (1-7, default: 1)
    --end-step NUM         End at step NUM (1-7, default: 7)
    --dry-run              Show what would be done without executing
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

STEPS:
    1. Environment preparation and parameter parsing
    2. Split file to markdown and extract images
    3. Translate markdown files using Claude API
    4. Merge translated markdown files
    5. Convert markdown to HTML with template
    6. Generate and insert table of contents
    7. Generate DOCX and EPUB files in temp directory

NOTE:
    For PDF/DOCX/EPUB files, steps 1-2 are automatically replaced by Calibre HTMLZ conversion
    which creates optimized markdown chunks ready for translation.

EXAMPLES:
    # Basic usage
    ${SCRIPT_NAME} book.pdf

    # Translate to English with custom output
    ${SCRIPT_NAME} --olang en book.pdf

    # Clean temp and run with verbose output
    ${SCRIPT_NAME} --clean -v book.epub
    
    # Use custom prompt for translation
    ${SCRIPT_NAME} -p "Focus on technical accuracy and use formal language" book.pdf

    # Run only translation steps (3-4)
    ${SCRIPT_NAME} --start-step 3 --end-step 4 book.docx
    
    # Run only format conversion steps (5-7)
    ${SCRIPT_NAME} --start-step 5 --end-step 7 book.docx

    # Dry run to see what would happen
    ${SCRIPT_NAME} --dry-run book.pdf

REQUIREMENTS:
    - Python 3.6+
    - Claude CLI (https://docs.anthropic.com/en/docs/claude-code)
    - Calibre (for PDF/DOCX/EPUB support): https://calibre-ebook.com/
    - Internet connection (for initial package installation)
    
NOTE:
    Python packages are automatically installed in a virtual environment.
    The virtual environment is created in the script directory.

EXIT CODES:
    0   Success
    1   General error
    2   Invalid arguments
    3   Missing dependencies
    4   Claude CLI not found
    5   Input file not found

EOF
}

# Setup Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    local venv_dir="${SCRIPT_DIR}/venv"
    
    # Create virtual environment if it doesn't exist or if reinstall is requested
    if [[ ! -d "$venv_dir" ]] || [[ "$REINSTALL_PACKAGES" == true ]]; then
        if [[ "$REINSTALL_PACKAGES" == true ]] && [[ -d "$venv_dir" ]]; then
            log_info "Removing existing virtual environment for reinstall..."
            rm -rf "$venv_dir"
        fi
        
        log_info "Creating Python virtual environment..."
        python3 -m venv "$venv_dir"
        if [[ $? -ne 0 ]]; then
            log_error "Failed to create virtual environment"
            exit 3
        fi
    fi
    
    # Activate virtual environment
    source "$venv_dir/bin/activate"
    if [[ $? -ne 0 ]]; then
        log_error "Failed to activate virtual environment"
        exit 3
    fi
    
    log_success "Virtual environment activated"
    
    # Install required packages if needed
    local requirements_file="${SCRIPT_DIR}/requirements.txt"
    if [[ ! -f "$venv_dir/.packages_installed" ]] || [[ "$REINSTALL_PACKAGES" == true ]]; then
        log_info "Installing required Python packages..."
        
        if [[ -f "$requirements_file" ]]; then
            log_info "Installing packages from requirements.txt..."
            pip install -r "$requirements_file"
        else
            log_info "Installing essential packages..."
            pip install python-docx PyMuPDF ebooklib beautifulsoup4 lxml markdown Pillow pdf2image pypandoc
        fi
        
        if [[ $? -ne 0 ]]; then
            log_warning "Some packages failed to install, but continuing..."
            log_info "Missing packages will be handled gracefully by the scripts"
            log_info "If PIL/Pillow is missing, images will not be compressed but processing will continue"
        fi
        
        # Mark packages as installed
        touch "$venv_dir/.packages_installed"
        log_success "Python packages installation completed"
    else
        log_info "Python packages already installed, skipping installation"
    fi
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 3
    fi
    
    # Check required Python scripts
    local scripts=("01_prepare_env.py" "02_split_to_md.py" "03_translate_md.py" "04_merge_md.py" "05_md_to_html.py" "06_add_toc.py")
    for script in "${scripts[@]}"; do
        if [[ ! -f "${SCRIPT_DIR}/${script}" ]]; then
            log_error "Required script not found: ${script}"
            exit 3
        fi
    done
    
    # Check for file conversion script and Calibre for all supported formats
    if [[ "${INPUT_FILE}" == *.epub ]] || [[ "${INPUT_FILE}" == *.EPUB ]] || [[ "${INPUT_FILE}" == *.pdf ]] || [[ "${INPUT_FILE}" == *.PDF ]] || [[ "${INPUT_FILE}" == *.docx ]] || [[ "${INPUT_FILE}" == *.DOCX ]]; then
        if [[ ! -f "${SCRIPT_DIR}/01_convert_to_htmlz.py" ]]; then
            log_error "File converter not found: 01_convert_to_htmlz.py"
            log_error "This script is required for PDF/DOCX/EPUB file processing"
            exit 3
        fi
        
        # Check for Calibre ebook-convert
        local calibre_paths=(
            "/Applications/calibre.app/Contents/MacOS/ebook-convert"
            "/usr/bin/ebook-convert"
            "/usr/local/bin/ebook-convert"
        )
        
        local calibre_found=false
        for path in "${calibre_paths[@]}"; do
            if [[ -f "$path" ]]; then
                calibre_found=true
                break
            fi
        done
        
        if [[ "$calibre_found" == false ]] && ! command -v ebook-convert &> /dev/null; then
            log_error "Calibre ebook-convert not found"
            log_error "Please install Calibre: https://calibre-ebook.com/"
            exit 3
        fi
    fi
    
    # Check Claude CLI availability
    if ! command -v claude &> /dev/null; then
        log_error "Claude CLI not found"
        log_error "Please install Claude CLI: https://docs.anthropic.com/en/docs/claude-code"
        exit 4
    fi
    
    log_success "Dependencies check passed"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -l|--ilang)
                INPUT_LANG="$2"
                shift 2
                ;;
            --olang)
                OUTPUT_LANG="$2"
                shift 2
                ;;
            -p|--prompt)
                CUSTOM_PROMPT="$2"
                shift 2
                ;;
            --clean)
                CLEAN_TEMP=true
                shift
                ;;
            --no-skip)
                SKIP_EXISTING=false
                shift
                ;;
            --reinstall-packages)
                REINSTALL_PACKAGES=true
                shift
                ;;
            --start-step)
                STEP_START="$2"
                if [[ ! "$STEP_START" =~ ^[1-7]$ ]]; then
                    log_error "Invalid start step: $STEP_START (must be 1-7)"
                    exit 2
                fi
                shift 2
                ;;
            --end-step)
                STEP_END="$2"
                if [[ ! "$STEP_END" =~ ^[1-7]$ ]]; then
                    log_error "Invalid end step: $STEP_END (must be 1-7)"
                    exit 2
                fi
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 2
                ;;
            *)
                if [[ -z "$INPUT_FILE" ]]; then
                    INPUT_FILE="$1"
                else
                    log_error "Multiple input files specified"
                    exit 2
                fi
                shift
                ;;
        esac
    done
    
    # Validate arguments
    if [[ -z "$INPUT_FILE" ]]; then
        log_error "Input file is required"
        echo "Use -h or --help for usage information"
        exit 2
    fi
    
    if [[ ! -f "$INPUT_FILE" ]]; then
        log_error "Input file not found: $INPUT_FILE"
        exit 5
    fi
    
    if [[ $STEP_START -gt $STEP_END ]]; then
        log_error "Start step ($STEP_START) cannot be greater than end step ($STEP_END)"
        exit 2
    fi
}

# Execute Python script with error handling
execute_python_script() {
    local script_name="$1"
    local step_num="$2"
    local description="$3"
    
    log_step "$step_num" "$description"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would execute: python3 ${script_name}"
        return 0
    fi
    
    # Ensure virtual environment is activated before running Python scripts
    local venv_dir="${SCRIPT_DIR}/venv"
    if [[ -d "$venv_dir" ]]; then
        source "$venv_dir/bin/activate"
    fi
    
    local cmd="python3 ${SCRIPT_DIR}/${script_name}"
    
    if [[ "$VERBOSE" == true ]]; then
        log_info "Executing: $cmd"
    fi
    
    if ! $cmd; then
        log_error "Step $step_num failed: $description"
        log_error "Command: $cmd"
        exit 1
    fi
    
    log_success "Step $step_num completed: $description"
}

# Clean temporary directory
clean_temp_directory() {
    if [[ "$CLEAN_TEMP" == true ]]; then
        local temp_dir="${INPUT_FILE%.*}_temp"
        if [[ -d "$temp_dir" ]]; then
            log_info "Cleaning temporary directory: $temp_dir"
            if [[ "$DRY_RUN" == false ]]; then
                rm -rf "$temp_dir"
            fi
            log_success "Temporary directory cleaned"
        fi
    fi
}

# Show configuration
show_config() {
    log_info "Configuration:"
    echo "  Input file: $INPUT_FILE"
    echo "  Input language: $INPUT_LANG"
    echo "  Output language: $OUTPUT_LANG"
    echo "  Custom prompt: ${CUSTOM_PROMPT:-'None'}"
    echo "  Steps to run: $STEP_START-$STEP_END"
    echo "  Clean temp: $CLEAN_TEMP"
    echo "  Skip existing: $SKIP_EXISTING"
    echo "  Verbose: $VERBOSE"
    echo "  Dry run: $DRY_RUN"
    echo ""
}

# Main execution function
main() {
    # Show banner
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Book Translation Tool v${VERSION}${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    # Parse arguments
    parse_args "$@"
    
    # Show configuration
    show_config
    
    # Setup Python virtual environment
    setup_venv
    
    # Check dependencies
    check_dependencies
    
    # Clean temp directory if requested
    clean_temp_directory
    
    # Record start time
    local start_time=$(date +%s)
    
    # Convert supported file formats using Calibre HTMLZ method
    if [[ "${INPUT_FILE}" == *.epub ]] || [[ "${INPUT_FILE}" == *.EPUB ]] || [[ "${INPUT_FILE}" == *.pdf ]] || [[ "${INPUT_FILE}" == *.PDF ]] || [[ "${INPUT_FILE}" == *.docx ]] || [[ "${INPUT_FILE}" == *.DOCX ]]; then
        log_info "Detected supported file format, converting via Calibre HTMLZ..."
        
        local original_file="$INPUT_FILE"
        
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY RUN] Would convert file to markdown chunks: $original_file"
        else
            # Ensure virtual environment is activated
            local venv_dir="${SCRIPT_DIR}/venv"
            if [[ -d "$venv_dir" ]]; then
                source "$venv_dir/bin/activate"
            fi
            
            # Check if 01_convert_to_htmlz.py exists
            if [[ ! -f "${SCRIPT_DIR}/01_convert_to_htmlz.py" ]]; then
                log_error "File converter not found: 01_convert_to_htmlz.py"
                exit 3
            fi
            
            # Convert file using new method
            local convert_cmd="python3 ${SCRIPT_DIR}/01_convert_to_htmlz.py \"$original_file\" -l \"$INPUT_LANG\" --olang \"$OUTPUT_LANG\""
            
            if [[ "$VERBOSE" == true ]]; then
                log_info "Executing: $convert_cmd"
            fi
            
            if ! eval $convert_cmd; then
                log_error "File conversion failed"
                exit 1
            fi
            
            log_success "File converted to markdown chunks successfully"
            
            # The conversion creates a temp directory with markdown files
            # Skip step 1 and 2 since conversion is already done
            STEP_START=3
        fi
    fi
    
    # Execute steps
    local step_descriptions=(
        "Environment preparation and parameter parsing"
        "Split file to markdown and extract images"
        "Translate markdown files using Claude API"
        "Merge translated markdown files"
        "Convert markdown to HTML with template"
        "Generate and insert table of contents"
        "Generate DOCX and EPUB files in temp directory"
    )
    
    local step_scripts=(
        "01_prepare_env.py"
        "02_split_to_md.py"
        "03_translate_md.py"
        "04_merge_md.py"
        "05_md_to_html.py"
        "06_add_toc.py"
        "07_generate_formats.py"
    )
    
    # Execute Step 1 with parameters if it's in range
    if [[ $STEP_START -le 1 && $STEP_END -ge 1 ]]; then
        log_step "1" "${step_descriptions[0]}"
        
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY RUN] Would execute: python3 ${step_scripts[0]} with parameters"
        else
            # Ensure virtual environment is activated before running Python scripts
            local venv_dir="${SCRIPT_DIR}/venv"
            if [[ -d "$venv_dir" ]]; then
                source "$venv_dir/bin/activate"
            fi
            
            local cmd="python3 ${SCRIPT_DIR}/${step_scripts[0]} \"$INPUT_FILE\" -l \"$INPUT_LANG\" --olang \"$OUTPUT_LANG\""
            
            if [[ "$VERBOSE" == true ]]; then
                log_info "Executing: $cmd"
            fi
            
            if ! eval $cmd; then
                log_error "Step 1 failed: ${step_descriptions[0]}"
                exit 1
            fi
            
            log_success "Step 1 completed: ${step_descriptions[0]}"
        fi
    fi
    
    # Execute remaining steps
    for i in $(seq 2 7); do
        if [[ $STEP_START -le $i && $STEP_END -ge $i ]]; then
            # Special handling for step 3 (translation) with custom prompt
            if [[ $i -eq 3 && -n "$CUSTOM_PROMPT" ]]; then
                log_step "3" "${step_descriptions[2]}"
                
                if [[ "$DRY_RUN" == true ]]; then
                    log_info "[DRY RUN] Would execute: python3 ${step_scripts[2]} -p \"$CUSTOM_PROMPT\""
                else
                    # Ensure virtual environment is activated before running Python scripts
                    local venv_dir="${SCRIPT_DIR}/venv"
                    if [[ -d "$venv_dir" ]]; then
                        source "$venv_dir/bin/activate"
                    fi
                    
                    local cmd="python3 ${SCRIPT_DIR}/${step_scripts[2]} -p \"$CUSTOM_PROMPT\""
                    
                    if [[ "$VERBOSE" == true ]]; then
                        log_info "Executing: $cmd"
                    fi
                    
                    if ! eval $cmd; then
                        log_error "Step 3 failed: ${step_descriptions[2]}"
                        log_error "Translation is incomplete. Please fix the issues and run again."
                        exit 1
                    fi
                    
                    log_success "Step 3 completed: ${step_descriptions[2]}"
                fi
            elif [[ $i -eq 6 ]]; then
                # Special handling for step 6 (TOC generation) with base_temp/book.html output
                log_step "6" "${step_descriptions[5]}"
                
                if [[ "$DRY_RUN" == true ]]; then
                    log_info "[DRY RUN] Would execute: python3 ${step_scripts[5]} with base_temp/book.html output"
                else
                    # Ensure virtual environment is activated before running Python scripts
                    local venv_dir="${SCRIPT_DIR}/venv"
                    if [[ -d "$venv_dir" ]]; then
                        source "$venv_dir/bin/activate"
                    fi
                    
                    # Use input file name to determine temp directory
                    local base_temp_dir="${INPUT_FILE%.*}_temp"
                    
                    if [[ ! -d "$base_temp_dir" ]]; then
                        log_error "Temp directory not found: $base_temp_dir"
                        exit 1
                    fi
                    
                    # Step 6 will process book.html in the temp directory directly
                    local cmd="python3 ${SCRIPT_DIR}/${step_scripts[5]}"
                    
                    if [[ "$VERBOSE" == true ]]; then
                        log_info "Executing: $cmd"
                    fi
                    
                    if ! eval $cmd; then
                        log_error "Step 6 failed: ${step_descriptions[5]}"
                        exit 1
                    fi
                    
                    log_success "Step 6 completed: ${step_descriptions[5]} -> ${base_temp_dir}/book.html"
                fi
            else
                execute_python_script "${step_scripts[$((i-1))]}" "$i" "${step_descriptions[$((i-1))]}"
            fi
        fi
    done
    
    # Calculate execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Show completion message
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  Translation Complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    
    if [[ "$DRY_RUN" == false ]]; then
        echo -e "${GREEN}✓ Input file:${NC} $INPUT_FILE"
        echo -e "${GREEN}✓ Execution time:${NC} ${duration}s"
        echo -e "${GREEN}✓ Files generated in temp directory:${NC} ${INPUT_FILE%.*}_temp/"
    else
        echo -e "${YELLOW}Note: This was a dry run. No files were modified.${NC}"
    fi
    
    echo ""
    log_success "All steps completed successfully!"
}

# Handle interruption
trap 'log_error "Script interrupted by user"; exit 1' INT TERM

# Run main function with all arguments
main "$@"