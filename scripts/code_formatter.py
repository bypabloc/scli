import argparse
import fnmatch
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from menu_utils import confirm, simple_menu

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

DESCRIPTION = "🎨 Auto-format Python code based on specific formatting actions"

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


def main():
    """Main entry point for code formatter."""
    # Always parse command line arguments
    # When called from SCLI, sys.argv will be set properly by the script loader
    try:
        args = parse_arguments()
    except SystemExit:
        # argparse calls sys.exit() on error or help, re-raise it
        raise
    except Exception:
        # If parsing fails for any other reason, use defaults
        args = argparse.Namespace(
            mode=None,
            verbose=False,
            no_verbose=False,
            config=None,
            confirm=False,
            list_actions=False,
            only=None,
        )
        # Add dynamic action flags
        for action in get_available_format_actions():
            setattr(args, f"enable_{action}", False)
            setattr(args, f"disable_{action}", False)

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

    # Handle --list-actions flag
    if args.list_actions:
        print("📋 Available Format Actions:")
        print("=" * 50)

        categories = {
            "Import Management": [
                "sort_imports",
                "group_imports",
                "remove_unused_imports",
                "single_line_imports",
            ],
            "Code Formatting": [
                "fix_indentation",
                "normalize_strings",
                "fix_line_length",
                "remove_trailing_spaces",
                "add_trailing_comma",
            ],
            "Whitespace & Spacing": [
                "fix_whitespace",
                "remove_blank_lines",
                "ensure_newline_eof",
                "spaces_around_operators",
            ],
            "Statement Formatting": [
                "break_long_lines",
                "fix_continuation_lines",
                "format_docstrings",
            ],
            "Specific Fixes": [
                "remove_print_statements",
                "convert_tabs_to_spaces",
                "fix_encoding_declaration",
            ],
        }

        for category, actions in categories.items():
            print(f"\n{category}:")
            for action in actions:
                flag_name = action.replace("_", "-")
                print(f"  • {action}")
                print(f"    Enable:  --enable-{flag_name}")
                print(f"    Disable: --disable-{flag_name}")

        print("\nUsage examples:")
        print("  # Enable only specific actions:")
        print("  --only sort_imports,remove_unused_imports")
        print("\n  # Override config for specific actions:")
        print("  --enable-sort-imports --disable-normalize-strings")
        return

    print("🎨 Code Formatter")
    print(f"📁 Project: {project_root}")

    if config_file.exists():
        print(f"⚙️  Config: {config_file.name}")
    else:
        print("⚙️  Config: Default (create .scli-quality.yml to customize)")

    if formatter.git_root != project_root:
        print(f"🔗 Git root: {formatter.git_root}")

    # Show available tools
    print("\n📦 Available tools:")
    tool_status = {
        "isort": "Import sorting",
        "black": "Code formatting",
        "autopep8": "PEP 8 fixes",
        "autoflake": "Remove unused imports",
        "ruff": "Fast linting/formatting",
        "sed": "Text processing",
    }

    for tool, description in tool_status.items():
        status = "✅" if formatter.available_tools.get(tool) else "❌"
        print(f"  {status} {tool} ({description})")

    # Process CLI overrides for format actions
    format_config = config.get("format", {})

    # Handle --only flag
    if args.only:
        # If --only is specified, disable all actions first
        only_actions = [a.strip() for a in args.only.split(",")]
        enabled_actions = only_actions
    else:
        # Start with config settings
        enabled_actions = [
            k for k, v in format_config.items() if isinstance(v, bool) and v
        ]

        # Apply CLI enable/disable overrides
        for action in get_available_format_actions():
            if getattr(args, f"enable_{action}", False):
                if action not in enabled_actions:
                    enabled_actions.append(action)
            elif getattr(args, f"disable_{action}", False):
                if action in enabled_actions:
                    enabled_actions.remove(action)

    if enabled_actions:
        print(f"\n🔧 Enabled format actions ({len(enabled_actions)}):")

        # Group actions by category
        import_actions = [
            "sort_imports",
            "group_imports",
            "remove_unused_imports",
            "single_line_imports",
        ]
        code_actions = [
            "fix_indentation",
            "normalize_strings",
            "fix_line_length",
            "remove_trailing_spaces",
            "add_trailing_comma",
        ]
        whitespace_actions = [
            "fix_whitespace",
            "remove_blank_lines",
            "ensure_newline_eof",
            "spaces_around_operators",
        ]
        statement_actions = [
            "break_long_lines",
            "fix_continuation_lines",
            "format_docstrings",
        ]
        specific_actions = [
            "remove_print_statements",
            "convert_tabs_to_spaces",
            "fix_encoding_declaration",
        ]

        categories = [
            ("Import Management", import_actions),
            ("Code Formatting", code_actions),
            ("Whitespace & Spacing", whitespace_actions),
            ("Statement Formatting", statement_actions),
            ("Specific Fixes", specific_actions),
        ]

        for category_name, category_actions in categories:
            category_enabled = [a for a in category_actions if a in enabled_actions]
            if category_enabled:
                print(f"  📌 {category_name}:")
                for action in category_enabled:
                    print(f"     • {action}")
    else:
        print("\n⚠️  No format actions enabled in configuration!")
        print("💡 Enable actions in .scli-quality.yml under 'format:' section")
        return

    # Track if we used interactive mode for shortcut generation
    interactive_mode = False
    skip_prompts = args.confirm  # Use --confirm flag to confirm modifications

    # Determine evaluation mode
    if args.mode:
        mode = args.mode
    else:
        if skip_prompts:
            # Use default from config if --confirm is specified
            mode = config.get("default_mode", "all")
        else:
            interactive_mode = True
            # Get default mode from config
            config.get("default_mode", "all")

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
                return

            mode = mode_mapping[selected_mode]

    # Determine verbose mode
    if args.verbose:
        verbose = True
    elif args.no_verbose:
        verbose = False
    else:
        if skip_prompts:
            # Use default from config if --confirm is specified
            verbose = config.get("output.verbose", False)
        else:
            if not interactive_mode:
                interactive_mode = True
            # Ask for verbose mode (use config default)
            default_verbose = config.get("output.verbose", False)
            verbose = confirm(
                "Enable verbose output? (shows details for each action)",
                default=default_verbose,
            )

    # Show configuration details
    print(f"\n📋 Configuration:")
    print(f"   Max line length: {format_config.get('max_line_length', 88)}")
    print(f"   Indent size: {format_config.get('indent_size', 4)} spaces")

    # Confirm before formatting
    print(f"\n📝 Ready to format files:")
    print(f"   Mode: {mode}")
    print(f"   Actions: {len(enabled_actions)} enabled")
    print(f"   Verbose: {'Yes' if verbose else 'No'}")

    if skip_prompts:
        print("\n✅ Auto-confirmed (--confirm flag)")
    else:
        if not confirm("\n⚠️  This will modify your files. Continue?", default=True):
            print("Operation cancelled.")
            sys.exit(0)

    # Show shortcut command if interactive mode was used (after confirmation)
    if interactive_mode:
        config_name = (
            config_file.name
            if config_file.exists() and config_file.name != ".scli-quality.yml"
            else None
        )
        shortcut_cmd = generate_shortcut_command(
            mode,
            verbose,
            config_name,
            True,  # Always include --confirm in shortcut
        )
        print("\n💡 Shortcut for next time:")
        print(f"   {shortcut_cmd}")

    start_time = time.time()
    start_time_str = datetime.now().strftime("%H:%M:%S")

    print(f"\n⏰ Starting at {start_time_str}")

    # Get files and format them
    files = formatter.get_files_to_format(mode)

    if not files:
        print("📝 No Python files found to format.")
        sys.exit(0)

    print(f"📂 Found {len(files)} Python files to format")
    print("\n🔧 Applying format actions...")

    results = formatter.apply_format_actions(files, enabled_actions, verbose)

    # Print results with completion time
    elapsed_time = time.time() - start_time
    end_time_str = datetime.now().strftime("%H:%M:%S")
    print(f"\n⏱️  Completed at {end_time_str} ({elapsed_time:.2f} seconds)")

    formatter.print_summary(results, len(files))

    # Determine exit code
    if results.get("success"):
        print(f"\n✅ Formatting completed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Formatting completed with some issues")
        sys.exit(1)
