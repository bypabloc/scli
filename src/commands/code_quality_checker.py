#!/usr/bin/env python3
"""
Code Quality Checker Command - Python code quality analysis
"""

import argparse
import fnmatch
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.code_quality_checker_model import CodeQualityCheckerModel
from menu_utils import confirm, simple_menu, interactive_menu, text_input

DESCRIPTION = "🔍 Code quality checker for Python files using pycodestyle"

try:
    import pycodestyle
except ImportError:
    pycodestyle = None

try:
    import yaml
except ImportError:
    yaml = None


class CodeQualityConfig:
    """Configuration for code quality checker."""

    def __init__(self, config_file: Optional[Path] = None):
        self.config = self._load_config(config_file)

    def _load_config(self, config_file: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        default_config = {
            "pycodestyle": {
                # Modern 2025 best practices - Black compatibility + PEP 8 compliance
                "ignore": [
                    # Black compatibility (essential for modern Python)
                    "E203",  # Whitespace before ':' (conflicts with Black)
                    "W503",  # Line break before binary operator (Black style, PEP 8 compliant since 2016)
                    "W504",  # Line break after binary operator (mutually exclusive with W503)
                    # Commonly ignored for practical reasons
                    "E501",  # Line too long (handled by max-line-length)
                    "E701",  # Multiple statements on one line (sometimes needed)
                    "E731",  # Do not assign lambda (sometimes useful)
                    # Deprecated or controversial rules
                    "E121",  # Continuation line under-indented
                    "E123",  # Closing bracket does not match indentation
                    "E126",  # Continuation line over-indented for hanging indent
                    "E133",  # Closing bracket is missing indentation
                    "E226",  # Missing whitespace around arithmetic operator
                    "E241",  # Multiple spaces after ','
                    "E242",  # Tab after ','
                    "E704",  # Multiple statements on one line (def)
                    "W505",  # Doc line too long (handled by max-doc-length)
                ],
                "max_line_length": 88,  # Black standard, modern Python best practice
                "max_doc_length": 100,  # Slightly longer for documentation
                "indent_size": 4,  # PEP 8 standard
                "show_source": False,
                "show_pep8": False,
                "statistics": True,
                "count": True,
                "hang_closing": False,  # Compatible with Black
                "aggressive": 0,  # For autopep8 compatibility
                "experimental": False,  # For autopep8 compatibility
            },
            "exclusions": {
                "patterns": [
                    # Python cache and compiled files
                    "__pycache__",
                    "*.pyc",
                    "*.pyo",
                    "*.pyd",
                    "*.so",
                    # Version control
                    ".git",
                    ".hg",
                    ".svn",
                    ".bzr",
                    # Virtual environments
                    ".venv",
                    "venv",
                    ".env",
                    "env",
                    ".virtualenv",
                    # Package management
                    "node_modules",
                    ".npm",
                    ".yarn",
                    # Python packaging
                    "*.egg-info",
                    "*.egg",
                    "dist",
                    "build",
                    ".eggs",
                    # Testing and coverage
                    ".pytest_cache",
                    ".coverage",
                    "htmlcov",
                    ".tox",
                    # IDE and editor files
                    ".vscode",
                    ".idea",
                    "*.swp",
                    "*.swo",
                    "*~",
                    # OS files
                    ".DS_Store",
                    "Thumbs.db",
                    # Documentation
                    "docs/_build",
                    "doc/_build",
                    "_build",
                    # Common generated directories
                    "migrations",
                    "locale",
                    "static/CACHE",
                ],
                "directories": [
                    "vendor",
                    "third_party",
                    "external",
                    "lib",
                    "libs",
                    "node_modules",
                    "bower_components",
                    "jspm_packages",
                ],
                "files": [
                    "settings_local.py",
                    "local_settings.py",
                    "config_local.py",
                    "manage.py",
                    "setup.py",
                    "conftest.py",
                ],
            },
            "limits": {
                "max_total_errors": 0,  # Strict by default for quality
                "max_errors_per_file": 10,  # Reasonable limit per file
                "file_specific": {
                    # Test files can be more lenient
                    "test_*.py": 25,
                    "*_test.py": 25,
                    "tests/*.py": 25,
                    "test*.py": 25,
                    # Django migrations and management
                    "migrations/*.py": 100,
                    "manage.py": 50,
                    # Configuration files
                    "settings*.py": 30,
                    "config*.py": 30,
                    "setup.py": 50,
                    "conftest.py": 30,
                    # Scripts and utilities
                    "scripts/*.py": 20,
                    "utils/*.py": 15,
                    "tools/*.py": 20,
                },
            },
            "default_mode": "all",
            "output": {
                "verbose": False,
                "show_summary": True,
                "show_suggestions": True,
                "use_colors": True,
                "show_progress": True,
                "show_error_codes": True,
                "show_statistics": True,
            },
            "git": {
                "auto_detect": True,
                "respect_gitignore": True,
                "include_untracked": True,
            },
            "tools": {
                "suggest_black": True,
                "suggest_isort": True,
                "suggest_ruff": True,  # Modern recommendation for 2025
                "suggest_flake8": False,  # Less relevant with Ruff available
                "suggest_pylint": False,
                "suggest_mypy": True,  # Type checking is important
                "auto_format": False,
            },
            "compatibility": {
                "black_compatible": True,  # Ensure Black compatibility
                "ruff_compatible": True,  # Modern tool compatibility
                "pep8_compliant": True,  # PEP 8 compliance
            },
        }

        if config_file and config_file.exists() and yaml:
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        default_config.update(user_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load config file {config_file}: {e}")
                print("📝 Using default configuration")
        elif config_file and config_file.exists() and not yaml:
            print(
                "⚠️  Warning: YAML support not available. Install with: pip install pyyaml"
            )
            print("📝 Using default configuration")

        return default_config

    def get(self, key: str, default=None):
        """Get configuration value using dot notation."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class CodeQualityChecker:
    """Code quality checker for Python files."""

    def __init__(self, project_root: Path, config: Optional[CodeQualityConfig] = None):
        self.project_root = project_root
        self.config = config or CodeQualityConfig()
        self.git_root = self._find_git_root()
        self.gitignore_patterns = self._load_gitignore_patterns()

    def _find_git_root(self) -> Path:
        """Find the git repository root."""
        current = self.project_root
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return self.project_root

    def _load_gitignore_patterns(self) -> List[str]:
        """Load patterns from .gitignore file and configuration."""
        patterns = []

        # Load from config first
        config_patterns = self.config.get("exclusions.patterns", [])
        patterns.extend(config_patterns)

        # Add gitignore patterns if enabled
        if self.config.get("git.respect_gitignore", True):
            gitignore_file = self.git_root / ".gitignore"
            if gitignore_file.exists():
                try:
                    with open(gitignore_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                patterns.append(line)
                except Exception as e:
                    print(f"⚠️  Warning: Could not read .gitignore: {e}")

        # Add configured directories and files
        directories = self.config.get("exclusions.directories", [])
        files = self.config.get("exclusions.files", [])
        patterns.extend(directories)
        patterns.extend(files)

        return patterns

    def _is_ignored(self, file_path: Path) -> bool:
        """Check if file should be ignored based on .gitignore patterns."""
        relative_path = file_path.relative_to(self.git_root)
        path_str = str(relative_path)

        for pattern in self.gitignore_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(
                file_path.name, pattern
            ):
                return True
            # Check if any parent directory matches
            for parent in relative_path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True

        return False

    def _get_git_files(self, status_filter: str = "all") -> Set[Path]:
        """Get Python files from git based on status."""
        files = set()

        try:
            if status_filter == "staged":
                # Get staged files
                result = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True,
                )
            elif status_filter == "unstaged":
                # Get unstaged files
                result = subprocess.run(
                    ["git", "diff", "--name-only", "--diff-filter=ACM"],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True,
                )
            elif status_filter == "modified":
                # Get all modified files (staged + unstaged)
                staged = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True,
                )
                unstaged = subprocess.run(
                    ["git", "diff", "--name-only", "--diff-filter=ACM"],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True,
                )

                result = type("Result", (), {})()
                result.stdout = staged.stdout + unstaged.stdout
                result.returncode = 0
            else:
                # Get all tracked files
                result = subprocess.run(
                    ["git", "ls-files"],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True,
                )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and line.endswith(".py"):
                        file_path = self.git_root / line
                        if file_path.exists():
                            files.add(file_path)

        except subprocess.SubprocessError as e:
            print(f"⚠️  Git command failed: {e}")

        return files

    def _get_all_python_files(self) -> Set[Path]:
        """Get all Python files in the project recursively."""
        files = set()

        for file_path in self.project_root.rglob("*.py"):
            if file_path.is_file() and not self._is_ignored(file_path):
                files.add(file_path)

        return files

    def get_files_to_check(self, mode: str) -> Set[Path]:
        """Get files to check based on mode."""
        if self.git_root == self.project_root and mode != "all":
            return self._get_git_files(mode)
        else:
            if mode != "all":
                print(
                    "⚠️  Not in a git repository or git root not found. Using all files mode."
                )
            return self._get_all_python_files()

    def check_code_quality(
        self, files: Set[Path], verbose: Optional[bool] = None
    ) -> Tuple[int, Dict[str, int]]:
        """Check code quality using pycodestyle."""
        if not pycodestyle:
            print("❌ pycodestyle not installed. Install with: pip install pycodestyle")
            return 0, {}

        if not files:
            print("📝 No Python files found to check.")
            return 0, {}

        # Use config verbose if not specified
        if verbose is None:
            verbose = self.config.get("output.verbose", False)

        show_progress = self.config.get("output.show_progress", True)

        # Configure style checker from config with full options support
        ignore_rules = self.config.get("pycodestyle.ignore", [])
        select_rules = self.config.get("pycodestyle.select", [])
        max_line_length = self.config.get("pycodestyle.max_line_length", 88)
        max_doc_length = self.config.get("pycodestyle.max_doc_length", 100)
        indent_size = self.config.get("pycodestyle.indent_size", 4)
        show_source = self.config.get("pycodestyle.show_source", False)
        show_pep8 = self.config.get("pycodestyle.show_pep8", False)
        statistics = self.config.get("pycodestyle.statistics", True)
        count = self.config.get("pycodestyle.count", True)
        hang_closing = self.config.get("pycodestyle.hang_closing", False)

        # Build style guide arguments
        style_args = {
            "quiet": not verbose,
            "max_line_length": max_line_length,
            "show_source": show_source,
            "show_pep8": show_pep8,
            "statistics": statistics,
            "count": count,
            "hang_closing": hang_closing,
            "indent_size": indent_size,
        }

        # Add ignore or select (mutually exclusive)
        if select_rules:
            style_args["select"] = select_rules
        elif ignore_rules:
            style_args["ignore"] = ignore_rules

        # Add max_doc_length if supported (newer versions)
        try:
            style = pycodestyle.StyleGuide(max_doc_length=max_doc_length, **style_args)
        except TypeError:
            # Fallback for older pycodestyle versions
            style = pycodestyle.StyleGuide(**style_args)

        total_errors = 0
        error_summary = {}

        # Process files with dynamic loading indicator
        sorted_files = sorted(files)
        for i, file_path in enumerate(sorted_files, 1):
            # Show progress with current file being processed
            if show_progress:
                try:
                    display_path = file_path.relative_to(self.project_root)
                except ValueError:
                    display_path = file_path

                # Dynamic loading indicator - overwrites previous line
                # Truncate path if too long for terminal
                display_path_str = str(display_path)
                if len(display_path_str) > 50:
                    display_path_str = "..." + display_path_str[-47:]

                progress_msg = (
                    f"🔍 Processing [{i}/{len(sorted_files)}]: {display_path_str}"
                )

                # Only use dynamic updating in non-verbose mode to avoid issues
                if verbose:
                    print(progress_msg)
                else:
                    # Clear line and print new progress (only in non-verbose)
                    # Use simple carriage return to overwrite current line
                    print(f"\r{progress_msg.ljust(80)}", end="", flush=True)

            result = style.check_files([str(file_path)])
            file_errors = result.total_errors
            total_errors += file_errors

            if file_errors > 0:
                try:
                    relative_path = str(file_path.relative_to(self.project_root))
                except ValueError:
                    # File is outside project root, use absolute path
                    relative_path = str(file_path)

                error_summary[relative_path] = file_errors

                # Check file-specific limits (only in verbose mode to avoid cluttering)
                if verbose:
                    max_errors_per_file = self._get_max_errors_for_file(file_path)
                    if file_errors > max_errors_per_file:
                        print(
                            f"⚠️  {relative_path}: {file_errors} errors (limit: {max_errors_per_file})"
                        )

        # Clear the final progress line and add newline (only in non-verbose)
        if show_progress and not verbose:
            print(f"\r{' ' * 80}", end="\r", flush=True)

        # Show completion message with files successfully checked
        if show_progress:
            print(f"\n✅ Successfully checked {len(files)} Python files")

        return total_errors, error_summary

    def _get_max_errors_for_file(self, file_path: Path) -> int:
        """Get maximum allowed errors for a specific file."""
        try:
            relative_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            # File is outside project root, use absolute path
            relative_path = str(file_path)

        file_specific_limits = self.config.get("limits.file_specific", {})

        for pattern, limit in file_specific_limits.items():
            if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(
                file_path.name, pattern
            ):
                return limit

        return self.config.get("limits.max_errors_per_file", 10)

    def _build_file_tree(self, error_summary: Dict[str, int]) -> str:
        """Build a tree visualization of files with errors."""
        if not error_summary:
            return ""

        # Organize files by directory structure
        tree_data = {}

        for file_path, errors in error_summary.items():
            # Convert to Path and get parts
            path_obj = Path(file_path)
            parts = path_obj.parts

            # Build nested structure
            current = tree_data
            for part in parts[:-1]:  # All but the file name
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Add the file with error info
            filename = parts[-1]
            try:
                if file_path.startswith("/"):
                    full_path = Path(file_path)
                else:
                    full_path = self.project_root / file_path
                max_errors = self._get_max_errors_for_file(full_path)
            except:
                max_errors = self.config.get("limits.max_errors_per_file", 10)

            status = "⚠️" if errors > max_errors else "📝"
            current[filename] = {
                "_errors": errors,
                "_status": status,
                "_max_errors": max_errors,
            }

        # Generate tree string
        return self._render_tree(tree_data)

    def _render_tree(
        self,
        tree_data: dict,
        prefix: str = "",
        is_last: bool = True,
        is_root: bool = True,
    ) -> str:
        """Render tree structure with proper formatting."""
        lines = []

        items = list(tree_data.items())
        for i, (name, value) in enumerate(items):
            is_last_item = i == len(items) - 1

            if isinstance(value, dict) and "_errors" in value:
                # This is a file with error information
                connector = "└── " if is_last_item else "├── "
                status = value["_status"]
                errors = value["_errors"]
                max_errors = value["_max_errors"]

                # Format: connector + status + filename + (spaces) + error_count
                line = f"{prefix}{connector}{status} {name}"
                # Add padding to align error counts
                padding_needed = max(0, 60 - len(line))
                padding = " " * padding_needed
                line += f"{padding}({errors} errors, limit: {max_errors})"
                lines.append(line)
            else:
                # This is a directory
                connector = "└── " if is_last_item else "├── "
                lines.append(f"{prefix}{connector}{name}/")

                # Prepare prefix for children
                extension = "    " if is_last_item else "│   "
                child_prefix = prefix + extension

                # Recursively render children
                if value:  # Only if directory has contents
                    child_tree = self._render_tree(
                        value, child_prefix, is_last_item, False
                    )
                    lines.append(child_tree)

        return "\n".join(lines)

    def print_summary(
        self, total_errors: int, error_summary: Dict[str, int], files_count: int
    ):
        """Print summary of results."""
        if not self.config.get("output.show_summary", True):
            return

        print(f"\n{'=' * 60}")
        print("📋 CODE QUALITY SUMMARY")
        print(f"{'=' * 60}")
        print(f"Files checked: {files_count}")
        print(f"Total errors: {total_errors}")

        max_total_errors = self.config.get("limits.max_total_errors", 0)
        print(f"Error limit: {max_total_errors}")

        if error_summary:
            print("\n📁 Files with errors:")
            tree_view = self._build_file_tree(error_summary)
            print(tree_view)

        # Determine overall status
        if total_errors == 0:
            print("\n✅ Perfect code quality! No style issues found.")
        elif total_errors <= max_total_errors:
            print(
                f"\n✅ Code quality within acceptable limits ({total_errors}/{max_total_errors} errors)"
            )
        elif total_errors <= 10:
            print(f"\n⚠️  Minor code quality issues ({total_errors} errors)")
        elif total_errors <= 50:
            print(f"\n⚠️  Moderate code quality issues ({total_errors} errors)")
        else:
            print(f"\n❌ Poor code quality - many issues found ({total_errors} errors)")

        # Show suggestions if enabled
        if self.config.get("output.show_suggestions", True) and total_errors > 0:
            self._show_suggestions()

        print(f"{'=' * 60}")

    def _show_suggestions(self):
        """Show improvement suggestions."""
        print("\n💡 Suggestions:")

        # Modern tools (2025 recommendations)
        if self.config.get("tools.suggest_ruff", True):
            print(
                "   • 🚀 Use 'ruff check .' for ultra-fast linting (modern replacement for flake8)"
            )
            print(
                "   • 🚀 Use 'ruff format .' for ultra-fast formatting (modern replacement for black)"
            )

        # Traditional tools (still popular)
        if self.config.get("tools.suggest_black", True):
            print("   • Run 'black .' to auto-format code (PEP 8 compliant)")

        if self.config.get("tools.suggest_isort", True):
            print("   • Run 'isort .' to organize imports")

        # Type checking (important for modern Python)
        if self.config.get("tools.suggest_mypy", True):
            print("   • Add 'mypy .' for static type checking")

        # Less common but still useful
        if self.config.get("tools.suggest_flake8", False):
            print("   • Consider using 'flake8' for additional checks")

        if self.config.get("tools.suggest_pylint", False):
            print("   • Consider using 'pylint' for comprehensive analysis")

        # Configuration and automation
        print("   • Set up pre-commit hooks for automatic checking")
        print("   • Create or update .scli-quality.yml for custom configuration")

        # Modern workflow suggestions
        if self.config.get("compatibility.ruff_compatible", True):
            print(
                "   • 💡 Consider migrating to Ruff for 10-100x faster linting + formatting"
            )

        if self.config.get("compatibility.black_compatible", True):
            print(
                "   • ✨ Your configuration is Black-compatible for seamless integration"
            )


def generate_shortcut_command(
    mode: str, verbose: bool, config_file: Optional[str] = None
) -> str:
    """Generate equivalent command line for the current selection."""
    cmd_parts = ["uv run python scli code_quality_checker"]

    cmd_parts.append(f"--mode {mode}")

    if verbose:
        cmd_parts.append("--verbose")
    else:
        cmd_parts.append("--no-verbose")

    if config_file and config_file != ".scli-quality.yml":
        cmd_parts.append(f"--config {config_file}")

    return " ".join(cmd_parts)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Code quality checker for Python files using pycodestyle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s --mode all --verbose              # Check all files verbosely
  %(prog)s --mode staged --no-verbose        # Check staged files quietly
  %(prog)s --mode modified                   # Check modified files
""",
    )

    parser.add_argument(
        "--mode",
        "-m",
        choices=["all", "staged", "unstaged", "modified", "tracked"],
        help='File evaluation mode (default: from config or "all")',
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output (shows details for each file)",
    )

    parser.add_argument(
        "--no-verbose", action="store_true", help="Disable verbose output"
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file (default: .scli-quality.yml)",
    )

    return parser.parse_args()


class CodeQualityCheckerCommand(InteractiveCommand):
    """Code quality checker command implementation"""
    
    # Set the validation model
    event_model = CodeQualityCheckerModel
    
    def __init__(self):
        super().__init__(name="code_quality_checker", description=DESCRIPTION)
        self.validated_data = None
        self.quality_checker = None
    
    def preload(self, *args, **kwargs) -> bool:
        """
        Preload and validate command arguments using Pydantic model.
        """
        try:
            # Call parent preload first
            if not super().preload(*args, **kwargs):
                return False
            
            # Convert args to a dictionary for validation
            data = {}
            
            # Parse command line arguments if provided
            if args:
                i = 0
                while i < len(args):
                    arg = args[i]
                    if arg == '--mode' and i + 1 < len(args):
                        data['mode'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--mode='):
                        data['mode'] = arg.split('=', 1)[1]
                    elif arg == '--verbose':
                        data['verbose'] = True
                    elif arg == '--no-verbose':
                        data['verbose'] = False
                    elif arg == '--config' and i + 1 < len(args):
                        data['config_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--config='):
                        data['config_file'] = arg.split('=', 1)[1]
                    elif arg == '--project-root' and i + 1 < len(args):
                        data['project_root'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--project-root='):
                        data['project_root'] = arg.split('=', 1)[1]
                    elif arg == '--directory' and i + 1 < len(args):
                        data['project_root'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--directory='):
                        data['project_root'] = arg.split('=', 1)[1]
                    elif arg == '--max-errors' and i + 1 < len(args):
                        data['max_errors'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--max-errors='):
                        data['max_errors'] = int(arg.split('=', 1)[1])
                    elif arg == '--respect-gitignore':
                        data['respect_gitignore'] = True
                    elif arg == '--no-respect-gitignore':
                        data['respect_gitignore'] = False
                    i += 1
            
            # Add any kwargs
            data.update(kwargs)
            
            # Set defaults
            if 'mode' not in data:
                data['mode'] = 'all'
            if 'verbose' not in data:
                data['verbose'] = False
            
            # Validate using Pydantic model
            self.validated_data = self.event_model(**data)
            
            self.logger.debug(f"Arguments validated successfully: {self.validated_data.to_dict()}")
            return True
            
        except Exception as e:
            self.print_error(f"Argument validation failed: {e}")
            self.logger.error(f"Preload validation error: {e}")
            return False
    
    def requirements(self, *args, **kwargs) -> bool:
        """Check if pycodestyle is available"""
        try:
            # Check if pycodestyle is available
            if not pycodestyle:
                self.print_error("pycodestyle not installed. Install with: pip install pycodestyle")
                return False
            
            self.print_success("pycodestyle is available")
            return True
            
        except Exception as e:
            self.print_error(f"Requirements check failed: {e}")
            return False
    
    def validation(self, *args, **kwargs) -> bool:
        """Validate git requirements for git-based modes"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Check git availability for git-dependent modes
            if self.validated_data.requires_git():
                project_root = self.validated_data.get_project_root_path()
                
                # Check if we're in a git repository
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "--git-dir"],
                        cwd=project_root,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        self.print_warning(f"Mode '{self.validated_data.mode}' requires git, but not in a git repository")
                        self.print_info("Will use 'all' mode instead")
                        # Update mode to 'all' if git is not available
                        self.validated_data.mode = 'all'
                except FileNotFoundError:
                    self.print_warning("Git not found in system. Will use 'all' mode instead")
                    self.validated_data.mode = 'all'
            
            return True
            
        except Exception as e:
            self.print_error(f"Validation failed: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the code quality checker command with smart interactive configuration"""
        try:
            # Check for help request first
            if args and (args[0] == '--help' or args[0] == '-h'):
                self._show_help()
                return True
            
            # Parse provided arguments first
            provided_args = self._parse_provided_arguments(args)
            
            # Interactive/hybrid mode - show configuration menu for missing arguments
            if not self._all_required_args_provided(provided_args):
                print("\n🔧 Code Quality Checker Configuration")
                print("=" * 50)
            
            # Step 1: Directory - ask only if not provided
            if 'project_root' not in provided_args:
                current_dir = str(Path.cwd())
                project_dir = self._select_project_directory(current_dir)
                if not project_dir:
                    self.print_warning("Operation cancelled")
                    return False
            else:
                project_dir = provided_args['project_root']
                print(f"📁 Using provided directory: {project_dir}")
            
            # Step 2: Gitignore handling - ask only if not provided
            if 'respect_gitignore' not in provided_args:
                respect_gitignore = self._select_gitignore_option()
            else:
                respect_gitignore = provided_args['respect_gitignore']
                print(f"📋 Using provided gitignore setting: {'Respect' if respect_gitignore else 'Ignore'} .gitignore")
            
            # Step 3: Config file - ask only if not provided
            if 'config_file' not in provided_args:
                config_file = self._select_config_file()
            else:
                config_file = provided_args['config_file']
                print(f"📝 Using provided config: {config_file or 'Default configuration'}")
            
            # Step 4: Analysis mode - ask only if not provided
            if 'mode' not in provided_args:
                mode = self._select_analysis_mode()
            else:
                mode = provided_args['mode']
                print(f"🔍 Using provided mode: {mode}")
            
            # Step 5: Verbose option - ask only if not provided
            if 'verbose' not in provided_args:
                verbose = self._select_verbose_option()
            else:
                verbose = provided_args['verbose']
                print(f"📊 Using provided verbose setting: {'Yes' if verbose else 'No'}")
            
            # Create temporary validated data with selected options
            temp_data = {
                'mode': mode,
                'verbose': verbose,
                'project_root': project_dir,
                'config_file': config_file,
                'respect_gitignore': respect_gitignore
            }
            
            # Validate the data
            self.validated_data = self.event_model(**temp_data)
            
            # Show command shortcut BEFORE execution
            print("\n" + "="*60)
            print("🚀 COMMAND SHORTCUT FOR NEXT TIME")
            print("="*60)
            self._build_and_show_shortcut(project_dir, mode, verbose, config_file, respect_gitignore)
            
            print("\n🚀 Starting code quality analysis...")
            print("-" * 50)
            print(f"📁 Directory: {project_dir}")
            print(f"📝 Config: {config_file or 'Default configuration'}")
            print(f"🔍 Mode: {mode}")
            print(f"📊 Verbose: {'Yes' if verbose else 'No'}")
            print(f"📋 Respect .gitignore: {'Yes' if respect_gitignore else 'No'}")
            print("-" * 50)
            
            # Execute analysis
            result = self._run_analysis()
            
            return result
            
        except Exception as e:
            self.print_error(f"Failed to execute code quality checker: {e}")
            return False
    
    def _parse_provided_arguments(self, args: tuple) -> Dict[str, Any]:
        """Parse command line arguments and return provided values"""
        provided = {}
        
        if not args:
            return provided
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            # Parse all possible arguments
            if arg == '--mode' and i + 1 < len(args):
                provided['mode'] = args[i + 1]
                i += 1
            elif arg.startswith('--mode='):
                provided['mode'] = arg.split('=', 1)[1]
            elif arg == '--verbose':
                provided['verbose'] = True
            elif arg == '--no-verbose':
                provided['verbose'] = False
            elif arg == '--config' and i + 1 < len(args):
                provided['config_file'] = args[i + 1]
                i += 1
            elif arg.startswith('--config='):
                provided['config_file'] = arg.split('=', 1)[1]
            elif arg == '--project-root' and i + 1 < len(args):
                provided['project_root'] = args[i + 1]
                i += 1
            elif arg.startswith('--project-root='):
                provided['project_root'] = arg.split('=', 1)[1]
            elif arg == '--directory' and i + 1 < len(args):
                provided['project_root'] = args[i + 1]
                i += 1
            elif arg.startswith('--directory='):
                provided['project_root'] = arg.split('=', 1)[1]
            elif arg == '--respect-gitignore':
                provided['respect_gitignore'] = True
            elif arg == '--no-respect-gitignore':
                provided['respect_gitignore'] = False
            elif arg == '--max-errors' and i + 1 < len(args):
                provided['max_errors'] = int(args[i + 1])
                i += 1
            elif arg.startswith('--max-errors='):
                provided['max_errors'] = int(arg.split('=', 1)[1])
            
            i += 1
        
        return provided
    
    def _all_required_args_provided(self, provided_args: Dict[str, Any]) -> bool:
        """Check if all required arguments are provided (for fully non-interactive mode)"""
        required_keys = ['project_root', 'respect_gitignore', 'config_file', 'mode', 'verbose']
        return all(key in provided_args for key in required_keys)
    
    def _build_and_show_shortcut(self, project_dir: str, mode: str, verbose: bool, 
                               config_file: Optional[str], respect_gitignore: bool):
        """Build and show command shortcut"""
        # Build command
        cmd_parts = ["uv run python scli code_quality_checker"]
        cmd_parts.append(f"--directory=\"{project_dir}\"")
        cmd_parts.append(f"--mode={mode}")
        
        if verbose:
            cmd_parts.append("--verbose")
        else:
            cmd_parts.append("--no-verbose")
        
        if config_file:
            cmd_parts.append(f"--config=\"{config_file}\"")
        else:
            cmd_parts.append("--config=")  # Empty config means use defaults
        
        if respect_gitignore:
            cmd_parts.append("--respect-gitignore")
        else:
            cmd_parts.append("--no-respect-gitignore")
        
        command = " ".join(cmd_parts)
        print(f"📋 {command}")
        print()
        print("💡 Copy this command to run the same analysis directly next time!")
        print("=" * 60)
    
    def _show_help(self):
        """Show command-specific help"""
        print(f"\n{DESCRIPTION}")
        print("=" * 60)
        print("📋 USAGE:")
        print("  uv run python scli code_quality_checker [OPTIONS]")
        print()
        print("🔧 OPTIONS:")
        print("  -h, --help                    Show this help message")
        print("  --directory=PATH              Project directory to analyze (default: current)")
        print("  --project-root=PATH           Same as --directory")
        print("  --mode=MODE                   Analysis mode: all, staged, modified, tracked (default: all)")
        print("  --verbose                     Show detailed error output")
        print("  --no-verbose                  Show summary only (default)")
        print("  --config=FILE                 Configuration file path (default: .scli-quality.yml)")
        print("  --respect-gitignore           Respect .gitignore files (default)")
        print("  --no-respect-gitignore        Ignore .gitignore files")
        print("  --max-errors=N                Maximum allowed errors before failing (default: 0)")
        print()
        print("📁 ANALYSIS MODES:")
        print("  all       - Analyze all Python files in project")
        print("  staged    - Analyze only staged files (git)")
        print("  modified  - Analyze only modified files (git)")
        print("  tracked   - Analyze only tracked files (git)")
        print()
        print("💡 EXAMPLES:")
        print("  # Interactive mode")
        print("  uv run python scli code_quality_checker")
        print()
        print("  # Direct execution with specific directory")
        print("  uv run python scli code_quality_checker --directory=/path/to/project")
        print()
        print("  # Full configuration")
        print("  uv run python scli code_quality_checker --directory=. --mode=all --verbose --max-errors=100")
        print()
        print("  # Quick check with higher error tolerance")
        print("  uv run python scli code_quality_checker --mode=staged --max-errors=50")
        print()
        print("🔧 CONFIGURATION:")
        print("  Create .scli-quality.yml in your project root for custom settings.")
        print("  Example configuration includes PEP 8 compliance, Black compatibility,")
        print("  and modern Python best practices.")
        print("=" * 60)
    
    def _execute_direct(self, *args, **kwargs) -> bool:
        """Execute command directly with command line arguments (non-interactive)"""
        if not self.validated_data:
            self.print_error("No validated data available")
            return False
        
        return self._run_analysis()
    
    def _run_analysis(self) -> bool:
        """Run the actual code quality analysis"""
        # Initialize quality checker
        project_root = self.validated_data.get_project_root_path()
        config_path = self.validated_data.get_config_path()
        
        # Load configuration
        config = CodeQualityConfig(config_path)
        self.quality_checker = CodeQualityChecker(project_root, config)
        
        self.print_info(f"Checking code quality in: {project_root}")
        self.print_info(f"Mode: {self.validated_data.mode}")
        if config_path:
            self.print_info(f"Using config: {config_path}")
        
        # Get files to check
        files = self.quality_checker.get_files_to_check(self.validated_data.mode)
        
        if not files:
            self.print_warning("No Python files found to check")
            return True
        
        self.print_info(f"Found {len(files)} Python files to check")
        
        # Run quality check
        total_errors, error_summary = self.quality_checker.check_code_quality(
            files, self.validated_data.verbose
        )
        
        # Print summary
        self.quality_checker.print_summary(total_errors, error_summary, len(files))
        
        # Check against limits
        max_errors = self.validated_data.max_errors or config.get("limits.max_total_errors", 0)
        
        # Store results
        self.set_result("mode", self.validated_data.mode)
        self.set_result("files_checked", len(files))
        self.set_result("total_errors", total_errors)
        self.set_result("max_errors", max_errors)
        self.set_result("error_summary", error_summary)
        self.set_result("validated_args", self.validated_data.to_dict())
        
        # Determine success based on error limits
        if total_errors > max_errors:
            self.print_error(f"Code quality check failed: {total_errors} errors exceed limit of {max_errors}")
            return False
        else:
            if total_errors == 0:
                self.print_success("Code quality check passed: No errors found")
            else:
                self.print_success(f"Code quality check passed: {total_errors} errors within limit of {max_errors}")
            return True
    
    def _select_project_directory(self, current_dir: str) -> Optional[str]:
        """Allow user to select project directory"""
        choices = [
            {"name": f"📁 Current directory: {current_dir}", "value": current_dir},
            {"name": "📂 Select different directory", "value": "custom"},
            {"name": "❌ Cancel", "value": "cancel"}
        ]
        
        selected = interactive_menu("Select project directory to analyze:", choices)
        if not selected or selected["value"] == "cancel":
            return None
        
        if selected["value"] == "custom":
            custom_dir = text_input("Enter directory path:", current_dir)
            if custom_dir and Path(custom_dir).exists():
                return str(Path(custom_dir).absolute())
            else:
                self.print_error(f"Directory does not exist: {custom_dir}")
                return None
        
        return selected["value"]
    
    def _select_gitignore_option(self) -> bool:
        """Select whether to respect .gitignore files"""
        choices = [
            {"name": "✅ Respect .gitignore (recommended)", "value": True},
            {"name": "📋 Analyze all files (ignore .gitignore)", "value": False}
        ]
        
        selected = interactive_menu("How should .gitignore files be handled?", choices)
        return selected["value"] if selected else True
    
    def _select_config_file(self) -> Optional[str]:
        """Select configuration file"""
        default_config = ".scli-quality.yml"
        current_dir = Path.cwd()
        default_path = current_dir / default_config
        
        choices = []
        
        # Check if default config exists
        if default_path.exists():
            choices.append({
                "name": f"📝 Use existing {default_config} (found)",
                "value": str(default_path)
            })
        else:
            choices.append({
                "name": f"📝 Use default {default_config} (will create if needed)",
                "value": str(default_path)
            })
        
        choices.extend([
            {"name": "📂 Select different config file", "value": "custom"},
            {"name": "⚙️ Use built-in defaults (no config file)", "value": None}
        ])
        
        selected = interactive_menu("Select configuration file:", choices)
        if not selected:
            return None
        
        if selected["value"] == "custom":
            custom_config = text_input("Enter config file path:", default_config)
            if custom_config:
                return str(Path(custom_config).absolute())
            return None
        
        return selected["value"]
    
    def _select_analysis_mode(self) -> str:
        """Select analysis mode"""
        choices = [
            {"name": "📁 All files in project", "value": "all"},
            {"name": "📋 Only staged files (git)", "value": "staged"},
            {"name": "📝 Only modified files (git)", "value": "modified"},
            {"name": "🔍 Only tracked files (git)", "value": "tracked"}
        ]
        
        selected = interactive_menu("Select analysis mode:", choices)
        return selected["value"] if selected else "all"
    
    def _select_verbose_option(self) -> bool:
        """Select verbose output option"""
        choices = [
            {"name": "📊 Verbose output (show detailed errors)", "value": True},
            {"name": "📋 Summary only (clean output)", "value": False}
        ]
        
        selected = interactive_menu("Select output detail level:", choices)
        return selected["value"] if selected else False
    
    def _show_command_shortcut(self, project_dir: str, mode: str, verbose: bool, 
                              config_file: Optional[str], respect_gitignore: bool):
        """Show command shortcut for repeating the same analysis"""
        print(f"\n{'='*60}")
        print("🚀 COMMAND SHORTCUT")
        print(f"{'='*60}")
        print("To repeat this exact analysis, use:")
        print()
        
        # Build command
        cmd_parts = ["uv run python scli code_quality_checker"]
        cmd_parts.append(f"--mode={mode}")
        cmd_parts.append(f"--project-root=\"{project_dir}\"")
        
        if verbose:
            cmd_parts.append("--verbose")
        
        if config_file:
            cmd_parts.append(f"--config=\"{config_file}\"")
        
        if respect_gitignore:
            cmd_parts.append("--respect-gitignore")
        
        command = " ".join(cmd_parts)
        print(f"📋 {command}")
        print()
        print("💡 Tip: Copy and paste this command to run the same analysis again!")
        print(f"{'='*60}")
        
        # Ask if user wants to save this command
        if confirm("Save this command to a script file?"):
            script_name = text_input("Enter script filename:", "check_quality.sh")
            if script_name:
                try:
                    with open(script_name, 'w') as f:
                        f.write("#!/bin/bash\n")
                        f.write("# Generated by SCLI Code Quality Checker\n")
                        f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(f"{command}\n")
                    
                    # Make it executable
                    os.chmod(script_name, 0o755)
                    self.print_success(f"Command saved to: {script_name}")
                    self.print_info(f"Make it executable: chmod +x {script_name}")
                except Exception as e:
                    self.print_error(f"Failed to save script: {e}")




# Create command instance for dynamic import
command_instance = CodeQualityCheckerCommand()
