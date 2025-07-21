# SCLI - Script CLI Tool

A modern Python CLI tool for managing and executing selectable scripts with an interactive interface.

## Features

- 🚀 **Interactive Script Selection**: Choose scripts from a beautiful interactive menu
- 📁 **Dynamic Script Loading**: Automatically discovers Python scripts in the `scripts/` folder
- 🎨 **Rich UI**: Beautiful terminal interface with colors and tables using Rich
- ⚡ **Fast**: Built with Typer for optimal performance
- 🔧 **Easy to Extend**: Simply add new Python scripts to the `scripts/` folder

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

## Requirements

- Python 3.12+
- typer
- rich

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