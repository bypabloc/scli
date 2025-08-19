# SCLI Project Context for Claude Code

## Project Overview

SCLI is a modern Python CLI tool for managing and executing selectable scripts with an interactive interface. Key features include:

- 🚀 **Interactive Script Selection**: Choose scripts from a beautiful interactive menu
- 📁 **Dynamic Script Loading**: Automatically discovers Python scripts in the `scripts/` folder  
- 🎨 **Rich UI**: Beautiful terminal interface with colors and tables using Rich
- ⚡ **Fast**: Built with Typer for optimal performance
- 🔧 **Easy to Extend**: Simply add new Python scripts to the `scripts/` folder

## Tech Stack & Dependencies

### Core Framework

- **Python**: 3.12+
- **Typer**: CLI framework for command handling
- **Rich**: Terminal rendering and formatting
- **Inquirer**: Interactive menu system
- **Textual**: TUI framework for complex interfaces

### Main Dependencies

```python
dependencies = [
    "typer>=0.12.0",      # CLI framework
    "rich>=13.0.0",       # Terminal formatting
    "inquirer>=3.2.0",    # Interactive menus
    "textual>=0.47.0",    # Text UI framework
    "pandas>=2.0.0",      # Data manipulation
    "questionary>=2.0.0", # User prompts
    "requests>=2.31.0",   # HTTP requests
    "pyyaml>=6.0",        # YAML processing
]
```

### Optional Dependencies

```python
pdf = [
    "PyPDF2>=3.0.0",
    "PyMuPDF>=1.23.0",
    "pdf2image>=1.16.0",
    "Pillow>=10.0.0",
    "pdfplumber>=0.10.0",
]
```

## Project Structure

```text
scli/
├── src/scli/             # Main package directory
│   ├── __init__.py
│   ├── main.py          # Main CLI entry point with Typer app
│   ├── script_loader.py # Dynamic script discovery and execution
│   ├── menu_utils.py    # Interactive menu utilities
│   ├── config_loader.py # Configuration management
│   ├── logger.py        # Logging configuration
│   └── output_manager.py # Output formatting utilities
├── scripts/             # Script directory (auto-discovered)
│   ├── hello_world.py   # Simple test script
│   ├── system_info.py   # System information display
│   ├── file_counter.py  # File counting by extension
│   ├── csv_viewer.py    # Interactive CSV viewer with Textual
│   ├── network_tools.py # Network diagnostic tools
│   ├── cobol_processor.py # COBOL file processing
│   ├── consumer_debt_checker.py # Consumer debt checking
│   ├── pdf_converter.py # PDF conversion utilities
│   └── log_analyzer.py  # Log file analysis
├── pyproject.toml       # Project configuration
├── uv.lock             # Dependency lock file
└── README.md           # Project documentation
```

## Installation

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Using uv (recommended)

```bash
uv sync
```

### Using pip

```bash
pip install -e .
```

## Commands & Build Scripts

### Development Commands

```bash
# Install dependencies using uv (recommended)
uv sync
uv sync --group dev  # Include dev dependencies

# Install using pip (alternative)
pip install -e .

# Run the CLI
scli                     # Interactive mode
scli -s script_name      # Direct script execution
scli run                 # Interactive mode (alternative)
scli run script_name     # Run specific script
scli list-scripts        # List all available scripts
scli info               # Show CLI information

# Development mode (before installation)
python -m scli          # Run from module
python -m scli -s script_name
```

### Testing & Quality Commands

```bash
# Run tests
pytest

# Code formatting
black src/
ruff check src/

# Type checking (if configured)
# mypy src/  # Not currently configured but recommended
```

### Build & Distribution

```bash
# Build package
uv build

# Install from built package
uv pip install dist/scli-*.whl

# Install in development mode
uv pip install -e .
```

## Usage

### Interactive Mode (Main Feature)

```bash
scli
```

### Run Specific Script Directly

```bash
scli -s hello_world
```

### Alternative Commands

```bash
scli run                    # Interactive mode
scli run hello_world        # Run specific script
scli list-scripts          # List all available scripts
scli info                  # Show information
```

## Adding New Scripts

1. Create a new Python file in the `scripts/` folder
2. Add a `DESCRIPTION` variable with a description of what the script does
3. Implement a `main()` function that contains your script logic

Example script structure:

```python
DESCRIPTION = "Your script description here"

def main():
    print("Your script logic here")
    # Add your code
```

## Example Scripts Included

- **hello_world.py**: Simple hello world example
- **system_info.py**: Display system information
- **file_counter.py**: Count files by extension in current directory
- **csv_viewer.py**: Interactive CSV viewer with filtering and pagination
- **network_tools.py**: Network diagnostic tools (ping, port check, DNS lookup)
- **cobol_processor.py**: COBOL file processing utilities
- **consumer_debt_checker.py**: Consumer debt checking tools
- **pdf_converter.py**: PDF conversion utilities
- **log_analyzer.py**: Log file analysis tools

## Code Style Guidelines

### Python Code Standards

- **Python Version**: 3.12+ with modern type hints
- **Import Style**: Use absolute imports for package modules
- **Module Structure**: Each script must have `DESCRIPTION` variable and `main()` function
- **Error Handling**: Always use try-except blocks in script execution
- **Type Hints**: Use type hints for function parameters and returns

### Script Development Pattern

All scripts in the `scripts/` directory must follow this structure:

```python
DESCRIPTION = "Your script description here"

def main():
    """Main entry point for the script"""
    # Script logic here
    pass
```

### Interactive UI Guidelines

- Use emoji icons for visual clarity in menus
- Implement fallback for non-TTY environments
- Always provide keyboard shortcuts and help text
- Use Rich console for colored output
- Handle KeyboardInterrupt gracefully

### Import Pattern for Scripts

Scripts should add the src directory to path when importing scli modules:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from scli.menu_utils import interactive_menu, text_input, confirm
```

## Core Files & Utilities

### Main Entry Points

- `src/scli/main.py`: Typer app definition and command handlers
- `src/scli/__main__.py`: Module execution entry point

### Key Modules

- `script_loader.py`: Discovers and executes scripts dynamically
- `menu_utils.py`: Provides `interactive_menu()`, `text_input()`, `confirm()` functions
- `config_loader.py`: Handles configuration loading
- `logger.py`: Configures logging for the application
- `output_manager.py`: Manages output formatting

### Script Examples

- **csv_viewer.py**: Complex Textual app for CSV viewing with pagination
- **network_tools.py**: Network diagnostics (ping, port check, DNS)
- **system_info.py**: System information display
- **file_counter.py**: File counting by extension

## Development

### Development Mode (Before Installation)

If you want to test the CLI without installing it, use the module execution method:

```bash
# Activate virtual environment
source .venv/bin/activate

# Interactive mode
python -m scli

# Run specific script directly
python -m scli -s script_name

# List all available scripts
python -m scli list-scripts

# Show CLI information
python -m scli info

# Alternative commands
python -m scli run                    # Interactive mode
python -m scli run hello_world        # Run specific script
```

### Development Dependencies

Install development dependencies:

```bash
uv sync --group dev
```

Run tests:

```bash
pytest
```

Format code:

```bash
black src/
ruff check src/
```

## Production Build

### Build and Install Locally

```bash
# Build the package
uv build

# Install from built package
uv pip install dist/scli-*.whl
```

### Install from Source (Editable)

```bash
# Install in development mode (recommended for testing)
uv pip install -e .

# Now you can use the CLI directly
scli                    # Interactive mode
scli -s script_name     # Direct execution
```

### Build Distribution

```bash
# Create source and wheel distributions
uv build

# Files will be created in dist/
# - scli-0.1.0.tar.gz (source distribution)
# - scli-0.1.0-py3-none-any.whl (wheel distribution)
```

### Install from PyPI (Future)

```bash
# When published to PyPI
pip install scli
```

## Repository Conventions

### Git Workflow

- **Main branch**: `master`
- **Development branch**: `dev`
- **Feature branches**: `feature/description`
- Use pull requests for merging to master
- Write clear commit messages

### File Naming

- Python files: lowercase with underscores (`script_name.py`)
- Classes: PascalCase (`ScriptLoader`)
- Functions: lowercase with underscores (`interactive_menu`)
- Constants: UPPERCASE (`DESCRIPTION`)

## Important Notes & Warnings

### IMPORTANT: Script Discovery

- Scripts are auto-discovered from the `scripts/` directory
- Each script MUST have a `main()` function and `DESCRIPTION` variable
- Scripts are loaded dynamically using importlib

### IMPORTANT: Error Handling

- Always handle exceptions in script execution
- Provide fallback for non-TTY environments
- Use try-except blocks for file operations

### IMPORTANT: Dependencies

- Use `uv` package manager for dependency management
- Check if optional dependencies are installed before using them
- Handle import errors gracefully with informative messages

## Testing Guidelines

### Unit Testing

- Test files should be named `test_*.py`
- Use pytest for testing framework
- Mock external dependencies when testing

### Manual Testing

- Test scripts in both TTY and non-TTY environments
- Verify keyboard shortcuts work correctly
- Test with different terminal sizes

## Performance Considerations

### CSV Viewer Optimization

- Uses pagination with default 1000 rows per page
- Implements chunk reading for large files
- Lazy loading of data on demand

### Script Loading

- Scripts are loaded only when needed
- Module caching prevents repeated imports
- Dynamic discovery happens once per session

## Security Notes

### Input Validation

- Always validate user input in scripts
- Sanitize file paths and prevent directory traversal
- Use proper encoding when reading files

### Network Tools

- Implement timeouts for network operations
- Validate host names and port numbers
- Handle network errors gracefully

## Common Workflows

### Adding a New Script

1. Create a new Python file in `scripts/` directory
2. Add `DESCRIPTION` variable at module level
3. Implement `main()` function with script logic
4. Import scli utilities if needed (menu_utils, etc.)
5. Test the script using `scli -s script_name`

### Debugging Scripts

```bash
# Run with Python directly for debugging
python scripts/script_name.py

# Use the module execution for testing
python -m scli -s script_name
```

### Building for Distribution

```bash
# Clean previous builds
rm -rf dist/ build/

# Build new distribution
uv build

# Test installation
pip install dist/scli-*.whl

# Upload to PyPI (when ready)
# twine upload dist/*
```

## Troubleshooting

### Common Issues

1. **ImportError in scripts**: Ensure src directory is added to path
2. **TTY not available**: Fallback menus will be used automatically
3. **Encoding errors**: Scripts try multiple encodings (utf-8, latin-1, cp1252)
4. **Missing dependencies**: Install with `uv sync` or check optional dependencies

### Debug Mode

Set environment variables for debugging:

```bash
export SCLI_DEBUG=1  # If implemented
python -m scli
```

## Future Enhancements

### Planned Features

- Configuration file support (YAML/TOML)
- Script categories and grouping
- Script parameter support
- Plugin system for external scripts
- Improved logging and debugging

### Architecture Improvements

- Async script execution support
- Script dependency management
- Better error reporting with stack traces
- Performance monitoring

## Contact & Support

- **Author**: bypabloc
- **Email**: bypabloc@example.com
- **Repository**: GitHub repository for SCLI project
- **Issues**: Report bugs in GitHub Issues

---

**Note**: This file is designed to provide comprehensive context to Claude Code for understanding and working with the SCLI project. Keep it updated as the project evolves.