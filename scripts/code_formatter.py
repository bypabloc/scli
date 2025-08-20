import argparse
import fnmatch
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
from menu_utils import confirm, simple_menu

DESCRIPTION = "🎨 Auto-format Python code using Black, isort, Ruff and other tools"

try:
    import yaml
except ImportError:
    yaml = None


class CodeFormatterConfig:
    """Configuration for code formatter."""

    def __init__(self, config_file: Optional[Path] = None):
        self.config = self._load_config(config_file)

    def _load_config(self, config_file: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        default_config = {
            "pycodestyle": {
                "ignore": [
                    "E203",
                    "W503",
                    "W504",
                    "E501",
                    "E701",
                    "E731",
                    "E121",
                    "E123",
                    "E126",
                    "E133",
                    "E226",
                    "E241",
                    "E242",
                    "E704",
                    "W505",
                ],
                "max_line_length": 88,
                "max_doc_length": 100,
                "indent_size": 4,
                "aggressive": 0,
                "experimental": False,
            },
            "exclusions": {
                "patterns": [
                    "__pycache__",
                    "*.pyc",
                    "*.pyo",
                    "*.pyd",
                    "*.so",
                    ".git",
                    ".hg",
                    ".svn",
                    ".bzr",
                    ".venv",
                    "venv",
                    ".env",
                    "env",
                    ".virtualenv",
                    "node_modules",
                    ".npm",
                    ".yarn",
                    "*.egg-info",
                    "*.egg",
                    "dist",
                    "build",
                    ".eggs",
                    ".pytest_cache",
                    ".coverage",
                    "htmlcov",
                    ".tox",
                    ".vscode",
                    ".idea",
                    "*.swp",
                    "*.swo",
                    "*~",
                    ".DS_Store",
                    "Thumbs.db",
                    "docs/_build",
                    "doc/_build",
                    "_build",
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
            "default_mode": "all",
            "output": {
                "verbose": False,
                "show_summary": True,
                "use_colors": True,
                "show_progress": True,
            },
            "git": {
                "auto_detect": True,
                "respect_gitignore": True,
                "include_untracked": True,
            },
            "tools": {
                "suggest_black": True,
                "suggest_isort": True,
                "suggest_ruff": True,
                "suggest_flake8": False,
                "suggest_pylint": False,
                "suggest_mypy": True,
                "auto_format": False,
            },
            "formatters": {
                "ruff": {
                    "enabled": True,
                    "priority": 1,
                    "fix_unsafe": False,
                    "format": True,
                },
                "black": {
                    "enabled": True,
                    "priority": 2,
                    "line_length": 88,
                    "skip_string_normalization": False,
                },
                "isort": {
                    "enabled": True,
                    "priority": 3,
                    "profile": "black",
                    "line_length": 88,
                },
                "autopep8": {
                    "enabled": False,
                    "priority": 4,
                    "aggressive": 1,
                    "max_line_length": 88,
                },
            },
            "compatibility": {
                "black_compatible": True,
                "ruff_compatible": True,
                "pep8_compliant": True,
            },
        }

        if config_file and config_file.exists() and yaml:
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        # Deep merge user config into default
                        self._deep_merge(default_config, user_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load config file {config_file}: {e}")
                print("📝 Using default configuration")
        elif config_file and config_file.exists() and not yaml:
            print(
                "⚠️  Warning: YAML support not available. Install with: pip install pyyaml"
            )
            print("📝 Using default configuration")

        return default_config

    def _deep_merge(self, base: dict, override: dict) -> None:
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

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


class CodeFormatter:
    """Code formatter for Python files."""

    def __init__(
        self, project_root: Path, config: Optional[CodeFormatterConfig] = None
    ):
        self.project_root = project_root
        self.config = config or CodeFormatterConfig()
        self.git_root = self._find_git_root()
        self.gitignore_patterns = self._load_gitignore_patterns()
        self.available_formatters = self._check_available_formatters()

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

        config_patterns = self.config.get("exclusions.patterns", [])
        patterns.extend(config_patterns)

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
            for parent in relative_path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True

        return False

    def _check_available_formatters(self) -> Dict[str, bool]:
        """Check which formatters are available."""
        formatters = {}

        # Check Ruff (modern, ultra-fast formatter)
        try:
            result = subprocess.run(
                ["ruff", "--version"], capture_output=True, text=True
            )
            formatters["ruff"] = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            formatters["ruff"] = False

        # Check Black
        try:
            result = subprocess.run(
                ["black", "--version"], capture_output=True, text=True
            )
            formatters["black"] = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            formatters["black"] = False

        # Check isort
        try:
            result = subprocess.run(
                ["isort", "--version"], capture_output=True, text=True
            )
            formatters["isort"] = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            formatters["isort"] = False

        # Check autopep8
        try:
            result = subprocess.run(
                ["autopep8", "--version"], capture_output=True, text=True
            )
            formatters["autopep8"] = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            formatters["autopep8"] = False

        return formatters

    def _get_git_files(self, status_filter: str = "all") -> Set[Path]:
        """Get Python files from git based on status."""
        files = set()

        try:
            if status_filter == "staged":
                result = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True,
                )
            elif status_filter == "unstaged":
                result = subprocess.run(
                    ["git", "diff", "--name-only", "--diff-filter=ACM"],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True,
                )
            elif status_filter == "modified":
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

    def get_files_to_format(self, mode: str) -> Set[Path]:
        """Get files to format based on mode."""
        if self.git_root == self.project_root and mode != "all":
            return self._get_git_files(mode)
        else:
            if mode != "all":
                print(
                    "⚠️  Not in a git repository or git root not found. Using all files mode."
                )
            return self._get_all_python_files()

    def _run_ruff_format(
        self, files: Set[Path], verbose: bool = False
    ) -> Tuple[int, int]:
        """Run Ruff formatter and fixer."""
        formatted = 0
        failed = 0

        if not self.available_formatters.get("ruff"):
            return formatted, failed

        # First run ruff check --fix for linting fixes
        if self.config.get("formatters.ruff.enabled", True):
            fix_args = ["ruff", "check", "--fix"]

            if self.config.get("formatters.ruff.fix_unsafe", False):
                fix_args.append("--unsafe-fixes")

            for file_path in files:
                try:
                    result = subprocess.run(
                        fix_args + [str(file_path)], capture_output=True, text=True
                    )
                    if result.returncode != 0 and verbose:
                        print(
                            f"⚠️  Ruff fix issues for {file_path.name}: {result.stderr}"
                        )
                except Exception as e:
                    if verbose:
                        print(f"❌ Ruff fix failed for {file_path.name}: {e}")
                    failed += 1

        # Then run ruff format for formatting
        if self.config.get("formatters.ruff.format", True):
            for file_path in files:
                try:
                    result = subprocess.run(
                        ["ruff", "format", str(file_path)],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        formatted += 1
                        if verbose:
                            print(f"✅ Ruff formatted: {file_path.name}")
                    else:
                        failed += 1
                        if verbose:
                            print(
                                f"❌ Ruff format failed for {file_path.name}: {result.stderr}"
                            )
                except Exception as e:
                    failed += 1
                    if verbose:
                        print(f"❌ Ruff format error for {file_path.name}: {e}")

        return formatted, failed

    def _run_black_format(
        self, files: Set[Path], verbose: bool = False
    ) -> Tuple[int, int]:
        """Run Black formatter."""
        formatted = 0
        failed = 0

        if not self.available_formatters.get("black"):
            return formatted, failed

        if not self.config.get("formatters.black.enabled", True):
            return formatted, failed

        black_args = ["black"]

        line_length = self.config.get("formatters.black.line_length", 88)
        black_args.extend(["-l", str(line_length)])

        if self.config.get("formatters.black.skip_string_normalization", False):
            black_args.append("-S")

        for file_path in files:
            try:
                result = subprocess.run(
                    black_args + [str(file_path)], capture_output=True, text=True
                )
                if result.returncode == 0:
                    if "reformatted" in result.stderr:
                        formatted += 1
                        if verbose:
                            print(f"✅ Black formatted: {file_path.name}")
                else:
                    failed += 1
                    if verbose:
                        print(f"❌ Black failed for {file_path.name}: {result.stderr}")
            except Exception as e:
                failed += 1
                if verbose:
                    print(f"❌ Black error for {file_path.name}: {e}")

        return formatted, failed

    def _run_isort_format(
        self, files: Set[Path], verbose: bool = False
    ) -> Tuple[int, int]:
        """Run isort formatter."""
        formatted = 0
        failed = 0

        if not self.available_formatters.get("isort"):
            return formatted, failed

        if not self.config.get("formatters.isort.enabled", True):
            return formatted, failed

        isort_args = ["isort"]

        profile = self.config.get("formatters.isort.profile", "black")
        isort_args.extend(["--profile", profile])

        line_length = self.config.get("formatters.isort.line_length", 88)
        isort_args.extend(["--line-length", str(line_length)])

        for file_path in files:
            try:
                # Check if changes are needed first
                check_result = subprocess.run(
                    isort_args + ["--check-only", "--diff", str(file_path)],
                    capture_output=True,
                    text=True,
                )

                if check_result.returncode != 0:
                    # File needs formatting
                    result = subprocess.run(
                        isort_args + [str(file_path)], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        formatted += 1
                        if verbose:
                            print(f"✅ isort formatted: {file_path.name}")
                    else:
                        failed += 1
                        if verbose:
                            print(
                                f"❌ isort failed for {file_path.name}: {result.stderr}"
                            )
            except Exception as e:
                failed += 1
                if verbose:
                    print(f"❌ isort error for {file_path.name}: {e}")

        return formatted, failed

    def _run_autopep8_format(
        self, files: Set[Path], verbose: bool = False
    ) -> Tuple[int, int]:
        """Run autopep8 formatter."""
        formatted = 0
        failed = 0

        if not self.available_formatters.get("autopep8"):
            return formatted, failed

        if not self.config.get("formatters.autopep8.enabled", False):
            return formatted, failed

        autopep8_args = ["autopep8", "--in-place"]

        aggressive = self.config.get("formatters.autopep8.aggressive", 1)
        for _ in range(aggressive):
            autopep8_args.append("-a")

        max_line_length = self.config.get("formatters.autopep8.max_line_length", 88)
        autopep8_args.extend(["--max-line-length", str(max_line_length)])

        # Add ignore rules from pycodestyle config
        ignore_rules = self.config.get("pycodestyle.ignore", [])
        if ignore_rules:
            autopep8_args.extend(["--ignore", ",".join(ignore_rules)])

        for file_path in files:
            try:
                result = subprocess.run(
                    autopep8_args + [str(file_path)], capture_output=True, text=True
                )
                if result.returncode == 0:
                    formatted += 1
                    if verbose:
                        print(f"✅ autopep8 formatted: {file_path.name}")
                else:
                    failed += 1
                    if verbose:
                        print(
                            f"❌ autopep8 failed for {file_path.name}: {result.stderr}"
                        )
            except Exception as e:
                failed += 1
                if verbose:
                    print(f"❌ autopep8 error for {file_path.name}: {e}")

        return formatted, failed

    def format_files(
        self, files: Set[Path], formatters: List[str], verbose: bool = False
    ) -> Dict[str, Dict[str, int]]:
        """Format files using specified formatters."""
        if not files:
            print("📝 No Python files found to format.")
            return {}

        results = {}
        show_progress = self.config.get("output.show_progress", True)

        # Get formatter configs and sort by priority
        formatter_configs = []
        for formatter in formatters:
            if formatter in ["ruff", "black", "isort", "autopep8"]:
                priority = self.config.get(f"formatters.{formatter}.priority", 99)
                formatter_configs.append((priority, formatter))

        formatter_configs.sort()

        # Run formatters in priority order
        for priority, formatter in formatter_configs:
            if show_progress:
                print(f"\n🔧 Running {formatter}...")

            if formatter == "ruff":
                formatted, failed = self._run_ruff_format(files, verbose)
            elif formatter == "black":
                formatted, failed = self._run_black_format(files, verbose)
            elif formatter == "isort":
                formatted, failed = self._run_isort_format(files, verbose)
            elif formatter == "autopep8":
                formatted, failed = self._run_autopep8_format(files, verbose)
            else:
                continue

            results[formatter] = {
                "formatted": formatted,
                "failed": failed,
                "total": len(files),
            }

            if show_progress and not verbose:
                if formatted > 0:
                    print(f"  ✅ Formatted {formatted}/{len(files)} files")
                if failed > 0:
                    print(f"  ⚠️  Failed to format {failed} files")

        return results

    def print_summary(self, results: Dict[str, Dict[str, int]], files_count: int):
        """Print summary of formatting results."""
        if not self.config.get("output.show_summary", True):
            return

        print(f"\n{'=' * 60}")
        print("📋 FORMATTING SUMMARY")
        print(f"{'=' * 60}")
        print(f"Files processed: {files_count}")

        if results:
            print("\n🔧 Formatter Results:")

            total_formatted = 0
            total_failed = 0

            for formatter, stats in results.items():
                formatted = stats["formatted"]
                failed = stats["failed"]
                total = stats["total"]

                total_formatted = max(total_formatted, formatted)
                total_failed = max(total_failed, failed)

                status = "✅" if failed == 0 else "⚠️"

                print(
                    f"  {status} {formatter.capitalize()}: {formatted} formatted, {failed} failed"
                )

            print("\n📊 Overall:")
            if total_failed == 0:
                print(f"  ✅ Successfully formatted {total_formatted} files")
            else:
                print(
                    f"  ⚠️  Formatted {total_formatted} files with {total_failed} failures"
                )
        else:
            print("\n❌ No formatters were run")

        self._show_suggestions()

        print(f"{'=' * 60}")

    def _show_suggestions(self):
        """Show suggestions for missing formatters."""
        print("\n💡 Suggestions:")

        if not self.available_formatters.get("ruff"):
            print("   • 🚀 Install Ruff for ultra-fast formatting: pip install ruff")

        if not self.available_formatters.get("black"):
            print("   • Install Black for PEP 8 formatting: pip install black")

        if not self.available_formatters.get("isort"):
            print("   • Install isort for import sorting: pip install isort")

        if not self.available_formatters.get("autopep8"):
            print(
                "   • Install autopep8 for automatic PEP 8 fixes: pip install autopep8"
            )

        all_available = all(self.available_formatters.values())
        if all_available:
            print("   • ✅ All formatters are installed and ready to use")
            print("   • Consider setting up pre-commit hooks for automatic formatting")
            print("   • Run 'code_quality_checker.py' to verify formatting results")


def generate_shortcut_command(
    mode: str, formatters: List[str], verbose: bool, config_file: Optional[str] = None
) -> str:
    """Generate equivalent command line for the current selection."""
    cmd_parts = ["uv run python scripts/code_formatter.py"]

    cmd_parts.append(f"--mode {mode}")

    if formatters:
        cmd_parts.append(f"--formatters {','.join(formatters)}")

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
        description="Auto-format Python code using Black, isort, Ruff and other tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s --mode all --formatters ruff,black # Format all files with ruff and black
  %(prog)s --mode staged --verbose            # Format staged files verbosely
  %(prog)s --mode modified --formatters isort # Format modified files with isort only
""",
    )

    parser.add_argument(
        "--mode",
        "-m",
        choices=["all", "staged", "unstaged", "modified", "tracked"],
        help='File selection mode (default: from config or "all")',
    )

    parser.add_argument(
        "--formatters",
        "-f",
        type=str,
        help="Comma-separated list of formatters to use (ruff,black,isort,autopep8)",
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


def main():
    """Main entry point for code formatter."""
    # Parse command line arguments only if run directly
    if __name__ == "__main__":
        args = parse_arguments()
    else:
        # Create dummy args when run through SCLI
        args = argparse.Namespace(
            mode=None, formatters=None, verbose=False, no_verbose=False, config=None
        )

    project_root = Path.cwd()

    # Look for configuration file
    if args.config:
        config_file = Path(args.config)
    else:
        config_file = project_root / ".scli-quality.yml"
        if not config_file.exists():
            config_file = project_root / ".scli-quality.yaml"

    config = CodeFormatterConfig(config_file if config_file.exists() else None)
    formatter = CodeFormatter(project_root, config)

    print("🎨 Code Formatter")
    print(f"📁 Project: {project_root}")

    if config_file.exists():
        print(f"⚙️  Config: {config_file.name}")
    else:
        print("⚙️  Config: Default (create .scli-quality.yml to customize)")

    if formatter.git_root != project_root:
        print(f"🔗 Git root: {formatter.git_root}")

    # Show available formatters
    print("\n📦 Available formatters:")
    for name, available in formatter.available_formatters.items():
        status = "✅" if available else "❌"
        enabled = config.get(f"formatters.{name}.enabled", False)
        if available:
            if enabled:
                print(f"  {status} {name} (enabled)")
            else:
                print(f"  {status} {name} (disabled in config)")
        else:
            print(f"  {status} {name} (not installed)")

    # Check if any formatter is available
    if not any(formatter.available_formatters.values()):
        print("\n❌ No formatters are installed!")
        print("📦 Install at least one formatter:")
        print("   • pip install ruff   (recommended - ultra-fast)")
        print("   • pip install black  (popular formatter)")
        print("   • pip install isort  (import sorting)")
        print("   • pip install autopep8 (PEP 8 fixes)")
        if __name__ == "__main__":
            sys.exit(1)
        else:
            return

    # Track if we used interactive mode for shortcut generation
    interactive_mode = False

    # Determine evaluation mode
    if args.mode:
        mode = args.mode
    else:
        interactive_mode = True
        # Get default mode from config
        default_mode = config.get("default_mode", "all")

        # Ask for evaluation mode if not specified
        modes = [
            "📁 All Python files in project",
            "📋 Git staged files only",
            "📝 Git unstaged files only",
            "🔄 Git modified files (staged + unstaged)",
            "🗂️  Git tracked files only",
        ]

        mode_mapping = {
            "📁 All Python files in project": "all",
            "📋 Git staged files only": "staged",
            "📝 Git unstaged files only": "unstaged",
            "🔄 Git modified files (staged + unstaged)": "modified",
            "🗂️  Git tracked files only": "tracked",
        }

        selected_mode = simple_menu("Select files to format:", modes)
        if selected_mode is None:
            print("Operation cancelled.")
            if __name__ == "__main__":
                sys.exit(0)
            else:
                return

        mode = mode_mapping[selected_mode]

    # Determine which formatters to use
    if args.formatters:
        selected_formatters = args.formatters.split(",")
    else:
        interactive_mode = True
        # Build list of available and enabled formatters
        formatter_options = []
        formatter_mapping = {}

        for name in ["ruff", "black", "isort", "autopep8"]:
            if formatter.available_formatters.get(name):
                enabled = config.get(f"formatters.{name}.enabled", False)
                if name == "ruff":
                    label = "🚀 Ruff (ultra-fast linter + formatter)"
                elif name == "black":
                    label = "⚫ Black (PEP 8 formatter)"
                elif name == "isort":
                    label = "📦 isort (import sorting)"
                elif name == "autopep8":
                    label = "🔧 autopep8 (PEP 8 fixes)"
                else:
                    label = name

                if enabled:
                    label += " [enabled in config]"

                formatter_options.append(label)
                formatter_mapping[label] = name

        if not formatter_options:
            print("\n❌ No formatters available to select!")
            if __name__ == "__main__":
                sys.exit(1)
            else:
                return

        print("\nSelect formatters to use (space to select, enter to confirm):")
        print("(Formatters will run in priority order from config)")

        # For simplicity, let's ask one by one
        selected_formatters = []
        for option in formatter_options:
            formatter_name = formatter_mapping[option]
            default = config.get(f"formatters.{formatter_name}.enabled", False)
            if confirm(f"Use {option}?", default=default):
                selected_formatters.append(formatter_name)

        if not selected_formatters:
            print("No formatters selected. Operation cancelled.")
            if __name__ == "__main__":
                sys.exit(0)
            else:
                return

    # Validate selected formatters
    valid_formatters = []
    for fmt in selected_formatters:
        if fmt not in formatter.available_formatters:
            print(f"⚠️  Unknown formatter: {fmt}")
        elif not formatter.available_formatters[fmt]:
            print(f"⚠️  Formatter not installed: {fmt}")
        else:
            valid_formatters.append(fmt)

    if not valid_formatters:
        print("❌ No valid formatters selected!")
        if __name__ == "__main__":
            sys.exit(1)
        else:
            return

    # Determine verbose mode
    if args.verbose:
        verbose = True
    elif args.no_verbose:
        verbose = False
    else:
        if not interactive_mode:
            interactive_mode = True
        # Ask for verbose mode (use config default)
        default_verbose = config.get("output.verbose", False)
        verbose = confirm(
            "Enable verbose output? (shows details for each file)",
            default=default_verbose,
        )

    # Show shortcut command if interactive mode was used
    if interactive_mode:
        config_name = (
            config_file.name
            if config_file.exists() and config_file.name != ".scli-quality.yml"
            else None
        )
        shortcut_cmd = generate_shortcut_command(
            mode, valid_formatters, verbose, config_name
        )
        print("\n💡 Shortcut for next time:")
        print(f"   {shortcut_cmd}")

    # Confirm before formatting
    print("\n📝 Ready to format files:")
    print(f"   Mode: {mode}")
    print(f"   Formatters: {', '.join(valid_formatters)}")
    print(f"   Verbose: {'Yes' if verbose else 'No'}")

    if not confirm("\n⚠️  This will modify your files. Continue?", default=True):
        print("Operation cancelled.")
        if __name__ == "__main__":
            sys.exit(0)
        else:
            return

    start_time = time.time()
    start_time_str = datetime.now().strftime("%H:%M:%S")

    print(f"\n⏰ Starting at {start_time_str}")

    # Get files and format them
    files = formatter.get_files_to_format(mode)

    if not files:
        print("📝 No Python files found to format.")
        if __name__ == "__main__":
            sys.exit(0)
        else:
            return

    print(f"📂 Found {len(files)} Python files to format")

    results = formatter.format_files(files, valid_formatters, verbose)

    # Print results with completion time
    elapsed_time = time.time() - start_time
    end_time_str = datetime.now().strftime("%H:%M:%S")
    print(f"\n⏱️  Completed at {end_time_str} ({elapsed_time:.2f} seconds)")

    formatter.print_summary(results, len(files))

    # Determine exit code
    total_failed = sum(r.get("failed", 0) for r in results.values())
    if total_failed > 0:
        print(f"\n⚠️  Formatting completed with {total_failed} failures")
        if __name__ == "__main__":
            sys.exit(1)
    else:
        print("\n✅ Formatting completed successfully!")
        if __name__ == "__main__":
            sys.exit(0)


if __name__ == "__main__":
    main()
