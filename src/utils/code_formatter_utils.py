#!/usr/bin/env python3
"""
Code Formatter Utilities - Classes and functions for Python code formatting
"""

import argparse
import fnmatch
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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
            "format": {
                # Import management
                "sort_imports": True,
                "group_imports": True,
                "remove_unused_imports": True,
                "single_line_imports": False,
                # Code formatting
                "fix_indentation": True,
                "normalize_strings": True,
                "fix_line_length": True,
                "remove_trailing_spaces": True,
                "add_trailing_comma": True,
                # Whitespace & spacing
                "fix_whitespace": True,
                "remove_blank_lines": True,
                "ensure_newline_eof": True,
                "spaces_around_operators": True,
                # Statement formatting
                "break_long_lines": True,
                "fix_continuation_lines": True,
                "format_docstrings": True,
                # Specific fixes
                "remove_print_statements": False,
                "convert_tabs_to_spaces": True,
                "fix_encoding_declaration": True,
                # Advanced options
                "max_line_length": 88,
                "indent_size": 4,
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
        self.available_tools = self._check_available_tools()
        self.applied_actions = []
        self.skipped_actions = []

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

    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which formatting tools are available."""
        tools = {}

        # Check for required tools
        tool_commands = {
            "isort": ["isort", "--version"],
            "black": ["black", "--version"],
            "ruff": ["ruff", "--version"],
            "autopep8": ["autopep8", "--version"],
            "autoflake": ["autoflake", "--version"],
            "sed": ["sed", "--version"],
        }

        for tool, command in tool_commands.items():
            try:
                result = subprocess.run(command, capture_output=True, text=True)
                tools[tool] = result.returncode == 0
            except (subprocess.SubprocessError, FileNotFoundError):
                tools[tool] = False

        return tools

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

    def _run_command_on_files(
        self, command: List[str], files: Set[Path], description: str
    ) -> bool:
        """Run a command on a set of files."""
        try:
            for file_path in files:
                result = subprocess.run(
                    command + [str(file_path)], capture_output=True, text=True
                )
                if result.returncode != 0 and self.config.get("output.verbose"):
                    print(f"  ⚠️  {description} failed for {file_path.name}")
            return True
        except Exception as e:
            if self.config.get("output.verbose"):
                print(f"  ❌ {description} error: {e}")
            return False

    def apply_format_actions(
        self, files: Set[Path], enabled_actions: List[str], verbose: bool = False
    ) -> Dict[str, Any]:
        """Apply specific formatting actions based on configuration and CLI overrides."""
        if not files:
            print("📝 No Python files found to format.")
            return {"success": False, "actions_applied": [], "actions_skipped": []}

        results = {"success": True, "actions_applied": [], "actions_skipped": []}
        show_progress = self.config.get("output.show_progress", True)

        # Get configuration settings
        format_config = self.config.get("format", {})
        max_line_length = format_config.get("max_line_length", 88)
        indent_size = format_config.get("indent_size", 4)

        # Map actions to specific tool commands
        action_mappings = {
            # Import management
            "sort_imports": {
                "tool": "isort",
                "command": [
                    "isort",
                    "--profile",
                    "black",
                    "--line-length",
                    str(max_line_length),
                ],
                "description": "Sort imports",
            },
            "group_imports": {
                "tool": "isort",
                "command": [
                    "isort",
                    "--profile",
                    "black",
                    "--force-grid-wrap",
                    "0",
                    "--multi-line",
                    "3",
                ],
                "description": "Group imports by type",
            },
            "remove_unused_imports": {
                "tool": "autoflake",
                "command": [
                    "autoflake",
                    "--in-place",
                    "--remove-unused-variables",
                    "--remove-all-unused-imports",
                ],
                "description": "Remove unused imports",
                "fallback_tool": "ruff",
                "fallback_command": ["ruff", "check", "--select", "F401,F841", "--fix"],
            },
            "move_imports_to_top": {
                "tool": "isort",
                "command": ["isort", "--profile", "black", "--float-to-top"],
                "description": "Move imports to top of file (fixes E402)",
                "fallback_tool": "autopep8",
                "fallback_command": ["autopep8", "--in-place", "--select", "E402"],
            },
            # Code formatting
            "fix_indentation": {
                "tool": "autopep8",
                "command": [
                    "autopep8",
                    "--in-place",
                    "--select",
                    "E101,E111,E112,E113,E114,E115,E116,E117",
                    f"--indent-size={indent_size}",
                ],
                "description": "Fix indentation",
            },
            "normalize_strings": {
                "tool": "black",
                "command": ["black", "-l", str(max_line_length)],
                "description": "Normalize string quotes",
            },
            "fix_line_length": {
                "tool": "black",
                "command": ["black", "-l", str(max_line_length)],
                "description": "Fix line length",
                "fallback_tool": "autopep8",
                "fallback_command": [
                    "autopep8",
                    "--in-place",
                    "--max-line-length",
                    str(max_line_length),
                    "--aggressive",
                ],
            },
            "remove_trailing_spaces": {
                "tool": "sed",
                "command": ["sed", "-i", "s/[[:space:]]*$//"],
                "description": "Remove trailing whitespace",
                "fallback_tool": "autopep8",
                "fallback_command": [
                    "autopep8",
                    "--in-place",
                    "--select",
                    "W291,W292,W293",
                ],
            },
            # Whitespace & spacing
            "fix_whitespace": {
                "tool": "autopep8",
                "command": [
                    "autopep8",
                    "--in-place",
                    "--select",
                    "E201,E202,E203,E211,E221,E222,E223,E224,E225,E226,E227,E228",
                ],
                "description": "Fix whitespace around operators",
            },
            "remove_blank_lines": {
                "tool": "autopep8",
                "command": [
                    "autopep8",
                    "--in-place",
                    "--select",
                    "E301,E302,E303,E304,E305,E306",
                ],
                "description": "Remove excessive blank lines",
            },
            "ensure_newline_eof": {
                "tool": "autopep8",
                "command": ["autopep8", "--in-place", "--select", "W292"],
                "description": "Ensure newline at end of file",
            },
            # Statement formatting
            "break_long_lines": {
                "tool": "black",
                "command": ["black", "-l", str(max_line_length)],
                "description": "Break long lines properly",
            },
            "format_docstrings": {
                "tool": "black",
                "command": ["black", "-l", str(max_line_length)],
                "description": "Format docstrings",
            },
            # Specific fixes
            "convert_tabs_to_spaces": {
                "tool": "autopep8",
                "command": ["autopep8", "--in-place", "--select", "W191"],
                "description": "Convert tabs to spaces",
            },
        }

        # Process each enabled action
        for action_name, action_config in action_mappings.items():
            # Check if action is enabled (from enabled_actions list)
            if action_name not in enabled_actions:
                continue

            tool = action_config["tool"]
            command = action_config["command"]
            description = action_config["description"]

            # Check if primary tool is available
            if not self.available_tools.get(tool):
                # Try fallback tool if available
                if "fallback_tool" in action_config:
                    fallback_tool = action_config["fallback_tool"]
                    if self.available_tools.get(fallback_tool):
                        tool = fallback_tool
                        command = action_config["fallback_command"]
                    else:
                        results["actions_skipped"].append(
                            f"{action_name} ({tool} not available)"
                        )
                        continue
                else:
                    results["actions_skipped"].append(
                        f"{action_name} ({tool} not available)"
                    )
                    continue

            # Apply the action
            if show_progress:
                print(f"  ▶ {description}...")

            success = self._run_command_on_files(command, files, description)

            if success:
                results["actions_applied"].append(action_name)
                if verbose:
                    print(f"    ✅ {description} completed")
            else:
                results["actions_skipped"].append(f"{action_name} (failed)")
                if verbose:
                    print(f"    ❌ {description} failed")

        return results

    def print_summary(self, results: Dict[str, Any], files_count: int):
        """Print summary of formatting results."""
        if not self.config.get("output.show_summary", True):
            return

        print(f"\n{'=' * 60}")
        print("📋 FORMATTING SUMMARY")
        print(f"{'=' * 60}")
        print(f"Files processed: {files_count}")

        if results.get("actions_applied"):
            print(f"\n✅ Actions applied ({len(results['actions_applied'])}):")
            for action in results["actions_applied"]:
                print(f"  • {action}")

        if results.get("actions_skipped"):
            print(f"\n⚠️  Actions skipped ({len(results['actions_skipped'])}):")
            for action in results["actions_skipped"]:
                print(f"  • {action}")

        # Show missing tools
        missing_tools = [
            tool for tool, available in self.available_tools.items() if not available
        ]
        if missing_tools:
            print(f"\n💡 Missing tools (install for more features):")
            for tool in missing_tools:
                if tool == "isort":
                    print(f"  • pip install isort  (import sorting)")
                elif tool == "black":
                    print(f"  • pip install black  (code formatting)")
                elif tool == "autopep8":
                    print(f"  • pip install autopep8  (PEP 8 fixes)")
                elif tool == "autoflake":
                    print(f"  • pip install autoflake  (remove unused imports)")
                elif tool == "ruff":
                    print(f"  • pip install ruff  (fast linting and formatting)")

        print(f"{'=' * 60}")


def generate_shortcut_command(
    mode: str,
    verbose: bool,
    config_file: Optional[str] = None,
    skip_prompts: bool = False,
) -> str:
    """Generate equivalent command line for the current selection."""
    cmd_parts = ["uv run python scli code_formatter"]

    cmd_parts.append(f"--mode {mode}")

    if verbose:
        cmd_parts.append("--verbose")
    else:
        cmd_parts.append("--no-verbose")

    if skip_prompts:
        cmd_parts.append("--confirm")

    if config_file and config_file != ".scli-quality.yml":
        cmd_parts.append(f"--config {config_file}")

    return " ".join(cmd_parts)


def get_available_format_actions():
    """Get all available format actions."""
    return [
        # Import management
        "sort_imports",
        "group_imports",
        "remove_unused_imports",
        "move_imports_to_top",
        "single_line_imports",
        # Code formatting
        "fix_indentation",
        "normalize_strings",
        "fix_line_length",
        "remove_trailing_spaces",
        "add_trailing_comma",
        # Whitespace & spacing
        "fix_whitespace",
        "remove_blank_lines",
        "ensure_newline_eof",
        "spaces_around_operators",
        # Statement formatting
        "break_long_lines",
        "fix_continuation_lines",
        "format_docstrings",
        # Specific fixes
        "remove_print_statements",
        "convert_tabs_to_spaces",
        "fix_encoding_declaration",
    ]


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Auto-format Python code based on specific formatting actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s --mode all --confirm              # Format all files, confirm modifications
  %(prog)s --mode staged --verbose           # Format staged files verbosely
  %(prog)s --mode modified --no-verbose --confirm # Format modified files quietly, confirm

  # Enable/disable specific actions (overrides config):
  %(prog)s --mode all --enable-sort_imports --disable-normalize_strings
  %(prog)s --mode all --only-sort_imports,remove_unused_imports

  # List available actions:
  %(prog)s --list-actions

Formatting actions are configured in .scli-quality.yml
Enable/disable specific actions in the 'format:' section or via CLI flags
""",
    )

    parser.add_argument(
        "--mode",
        "-m",
        choices=["all", "staged", "unstaged", "modified", "tracked"],
        help='File selection mode (default: from config or "all")',
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output (shows details for each action)",
    )

    parser.add_argument(
        "--no-verbose", action="store_true", help="Disable verbose output"
    )

    parser.add_argument(
        "--confirm",
        "-y",
        action="store_true",
        help="Automatically confirm file modifications without prompting",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file (default: .scli-quality.yml)",
    )

    parser.add_argument(
        "--list-actions",
        action="store_true",
        help="List all available format actions and exit",
    )

    parser.add_argument(
        "--only",
        type=str,
        help="Only run these specific actions (comma-separated)",
    )

    # Dynamically add enable/disable flags for each action
    available_actions = get_available_format_actions()
    for action in available_actions:
        parser.add_argument(
            f"--enable-{action.replace('_', '-')}",
            dest=f"enable_{action}",
            action="store_true",
            help=f"Enable {action} action (overrides config)",
        )
        parser.add_argument(
            f"--disable-{action.replace('_', '-')}",
            dest=f"disable_{action}",
            action="store_true",
            help=f"Disable {action} action (overrides config)",
        )

    return parser.parse_args()