import os
import sys
import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
import fnmatch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from menu_utils import simple_menu, confirm

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
            'pycodestyle': {
                # Modern 2025 best practices - Black compatibility + PEP 8 compliance
                'ignore': [
                    # Black compatibility (essential for modern Python)
                    'E203',  # Whitespace before ':' (conflicts with Black)
                    'W503',  # Line break before binary operator (Black style, PEP 8 compliant since 2016)
                    'W504',  # Line break after binary operator (mutually exclusive with W503)
                    
                    # Commonly ignored for practical reasons
                    'E501',  # Line too long (handled by max-line-length)
                    'E701',  # Multiple statements on one line (sometimes needed)
                    'E731',  # Do not assign lambda (sometimes useful)
                    
                    # Deprecated or controversial rules
                    'E121',  # Continuation line under-indented
                    'E123',  # Closing bracket does not match indentation
                    'E126',  # Continuation line over-indented for hanging indent
                    'E133',  # Closing bracket is missing indentation
                    'E226',  # Missing whitespace around arithmetic operator
                    'E241',  # Multiple spaces after ','
                    'E242',  # Tab after ','
                    'E704',  # Multiple statements on one line (def)
                    'W505',  # Doc line too long (handled by max-doc-length)
                ],
                'max_line_length': 88,  # Black standard, modern Python best practice
                'max_doc_length': 100,   # Slightly longer for documentation
                'indent_size': 4,        # PEP 8 standard
                'show_source': False,
                'show_pep8': False,
                'statistics': True,
                'count': True,
                'hang_closing': False,   # Compatible with Black
                'aggressive': 0,         # For autopep8 compatibility
                'experimental': False,   # For autopep8 compatibility
            },
            'exclusions': {
                'patterns': [
                    # Python cache and compiled files
                    '__pycache__', '*.pyc', '*.pyo', '*.pyd', '*.so',
                    
                    # Version control
                    '.git', '.hg', '.svn', '.bzr',
                    
                    # Virtual environments
                    '.venv', 'venv', '.env', 'env', '.virtualenv',
                    
                    # Package management
                    'node_modules', '.npm', '.yarn',
                    
                    # Python packaging
                    '*.egg-info', '*.egg', 'dist', 'build', '.eggs',
                    
                    # Testing and coverage
                    '.pytest_cache', '.coverage', 'htmlcov', '.tox',
                    
                    # IDE and editor files
                    '.vscode', '.idea', '*.swp', '*.swo', '*~',
                    
                    # OS files
                    '.DS_Store', 'Thumbs.db',
                    
                    # Documentation
                    'docs/_build', 'doc/_build', '_build',
                    
                    # Common generated directories
                    'migrations', 'locale', 'static/CACHE',
                ],
                'directories': [
                    'vendor', 'third_party', 'external', 'lib', 'libs',
                    'node_modules', 'bower_components', 'jspm_packages'
                ],
                'files': [
                    'settings_local.py', 'local_settings.py', 'config_local.py',
                    'manage.py', 'setup.py', 'conftest.py'
                ]
            },
            'limits': {
                'max_total_errors': 0,      # Strict by default for quality
                'max_errors_per_file': 10,  # Reasonable limit per file
                'file_specific': {
                    # Test files can be more lenient
                    'test_*.py': 25,
                    '*_test.py': 25,
                    'tests/*.py': 25,
                    'test*.py': 25,
                    
                    # Django migrations and management
                    'migrations/*.py': 100,
                    'manage.py': 50,
                    
                    # Configuration files
                    'settings*.py': 30,
                    'config*.py': 30,
                    'setup.py': 50,
                    'conftest.py': 30,
                    
                    # Scripts and utilities
                    'scripts/*.py': 20,
                    'utils/*.py': 15,
                    'tools/*.py': 20,
                }
            },
            'default_mode': 'all',
            'output': {
                'verbose': False,
                'show_summary': True,
                'show_suggestions': True,
                'use_colors': True,
                'show_progress': True,
                'show_error_codes': True,
                'show_statistics': True,
            },
            'git': {
                'auto_detect': True,
                'respect_gitignore': True,
                'include_untracked': True
            },
            'tools': {
                'suggest_black': True,
                'suggest_isort': True,
                'suggest_ruff': True,     # Modern recommendation for 2025
                'suggest_flake8': False,  # Less relevant with Ruff available
                'suggest_pylint': False,
                'suggest_mypy': True,     # Type checking is important
                'auto_format': False,
            },
            'compatibility': {
                'black_compatible': True,  # Ensure Black compatibility
                'ruff_compatible': True,   # Modern tool compatibility
                'pep8_compliant': True,    # PEP 8 compliance
            }
        }
        
        if config_file and config_file.exists() and yaml:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        default_config.update(user_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load config file {config_file}: {e}")
                print("📝 Using default configuration")
        elif config_file and config_file.exists() and not yaml:
            print("⚠️  Warning: YAML support not available. Install with: pip install pyyaml")
            print("📝 Using default configuration")
        
        return default_config
    
    def get(self, key: str, default=None):
        """Get configuration value using dot notation."""
        keys = key.split('.')
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
            if (current / '.git').exists():
                return current
            current = current.parent
        return self.project_root
    
    def _load_gitignore_patterns(self) -> List[str]:
        """Load patterns from .gitignore file and configuration."""
        patterns = []
        
        # Load from config first
        config_patterns = self.config.get('exclusions.patterns', [])
        patterns.extend(config_patterns)
        
        # Add gitignore patterns if enabled
        if self.config.get('git.respect_gitignore', True):
            gitignore_file = self.git_root / '.gitignore'
            if gitignore_file.exists():
                try:
                    with open(gitignore_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                patterns.append(line)
                except Exception as e:
                    print(f"⚠️  Warning: Could not read .gitignore: {e}")
        
        # Add configured directories and files
        directories = self.config.get('exclusions.directories', [])
        files = self.config.get('exclusions.files', [])
        patterns.extend(directories)
        patterns.extend(files)
        
        return patterns
    
    def _is_ignored(self, file_path: Path) -> bool:
        """Check if file should be ignored based on .gitignore patterns."""
        relative_path = file_path.relative_to(self.git_root)
        path_str = str(relative_path)
        
        for pattern in self.gitignore_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True
            # Check if any parent directory matches
            for parent in relative_path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True
        
        return False
    
    def _get_git_files(self, status_filter: str = 'all') -> Set[Path]:
        """Get Python files from git based on status."""
        files = set()
        
        try:
            if status_filter == 'staged':
                # Get staged files
                result = subprocess.run(
                    ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True
                )
            elif status_filter == 'unstaged':
                # Get unstaged files
                result = subprocess.run(
                    ['git', 'diff', '--name-only', '--diff-filter=ACM'],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True
                )
            elif status_filter == 'modified':
                # Get all modified files (staged + unstaged)
                staged = subprocess.run(
                    ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True
                )
                unstaged = subprocess.run(
                    ['git', 'diff', '--name-only', '--diff-filter=ACM'],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True
                )
                
                result = type('Result', (), {})()
                result.stdout = staged.stdout + unstaged.stdout
                result.returncode = 0
            else:
                # Get all tracked files
                result = subprocess.run(
                    ['git', 'ls-files'],
                    cwd=self.git_root,
                    capture_output=True,
                    text=True
                )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and line.endswith('.py'):
                        file_path = self.git_root / line
                        if file_path.exists():
                            files.add(file_path)
            
        except subprocess.SubprocessError as e:
            print(f"⚠️  Git command failed: {e}")
        
        return files
    
    def _get_all_python_files(self) -> Set[Path]:
        """Get all Python files in the project recursively."""
        files = set()
        
        for file_path in self.project_root.rglob('*.py'):
            if file_path.is_file() and not self._is_ignored(file_path):
                files.add(file_path)
        
        return files
    
    def get_files_to_check(self, mode: str) -> Set[Path]:
        """Get files to check based on mode."""
        if self.git_root == self.project_root and mode != 'all':
            return self._get_git_files(mode)
        else:
            if mode != 'all':
                print("⚠️  Not in a git repository or git root not found. Using all files mode.")
            return self._get_all_python_files()
    
    def check_code_quality(self, files: Set[Path], verbose: Optional[bool] = None) -> Tuple[int, Dict[str, int]]:
        """Check code quality using pycodestyle."""
        if not pycodestyle:
            print("❌ pycodestyle not installed. Install with: pip install pycodestyle")
            return 0, {}
        
        if not files:
            print("📝 No Python files found to check.")
            return 0, {}
        
        # Use config verbose if not specified
        if verbose is None:
            verbose = self.config.get('output.verbose', False)
        
        show_progress = self.config.get('output.show_progress', True)
        
        # Configure style checker from config with full options support
        ignore_rules = self.config.get('pycodestyle.ignore', [])
        select_rules = self.config.get('pycodestyle.select', [])
        max_line_length = self.config.get('pycodestyle.max_line_length', 88)
        max_doc_length = self.config.get('pycodestyle.max_doc_length', 100)
        indent_size = self.config.get('pycodestyle.indent_size', 4)
        show_source = self.config.get('pycodestyle.show_source', False)
        show_pep8 = self.config.get('pycodestyle.show_pep8', False)
        statistics = self.config.get('pycodestyle.statistics', True)
        count = self.config.get('pycodestyle.count', True)
        hang_closing = self.config.get('pycodestyle.hang_closing', False)
        
        # Build style guide arguments
        style_args = {
            'quiet': not verbose,
            'max_line_length': max_line_length,
            'show_source': show_source,
            'show_pep8': show_pep8,
            'statistics': statistics,
            'count': count,
            'hang_closing': hang_closing,
            'indent_size': indent_size,
        }
        
        # Add ignore or select (mutually exclusive)
        if select_rules:
            style_args['select'] = select_rules
        elif ignore_rules:
            style_args['ignore'] = ignore_rules
        
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
                
                progress_msg = f"🔍 Processing [{i}/{len(sorted_files)}]: {display_path_str}"
                
                # Only use dynamic updating in non-verbose mode to avoid issues
                if verbose:
                    print(progress_msg)
                else:
                    # Clear line and print new progress (only in non-verbose)
                    # Use simple carriage return to overwrite current line
                    print(f"\r{progress_msg.ljust(80)}", end='', flush=True)
            
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
                        print(f"⚠️  {relative_path}: {file_errors} errors (limit: {max_errors_per_file})")
        
        # Clear the final progress line and add newline (only in non-verbose)
        if show_progress and not verbose:
            print(f"\r{' ' * 80}", end='\r', flush=True)
        
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
        
        file_specific_limits = self.config.get('limits.file_specific', {})
        
        for pattern, limit in file_specific_limits.items():
            if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return limit
        
        return self.config.get('limits.max_errors_per_file', 10)
    
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
                if file_path.startswith('/'):
                    full_path = Path(file_path)
                else:
                    full_path = self.project_root / file_path
                max_errors = self._get_max_errors_for_file(full_path)
            except:
                max_errors = self.config.get('limits.max_errors_per_file', 10)
            
            status = "⚠️" if errors > max_errors else "📝"
            current[filename] = {
                '_errors': errors,
                '_status': status,
                '_max_errors': max_errors
            }
        
        # Generate tree string
        return self._render_tree(tree_data)
    
    def _render_tree(self, tree_data: dict, prefix: str = "", is_last: bool = True, is_root: bool = True) -> str:
        """Render tree structure with proper formatting."""
        lines = []
        
        items = list(tree_data.items())
        for i, (name, value) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            
            if isinstance(value, dict) and '_errors' in value:
                # This is a file with error information
                connector = "└── " if is_last_item else "├── "
                status = value['_status']
                errors = value['_errors']
                max_errors = value['_max_errors']
                
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
                    child_tree = self._render_tree(value, child_prefix, is_last_item, False)
                    lines.append(child_tree)
        
        return "\n".join(lines)
    
    def print_summary(self, total_errors: int, error_summary: Dict[str, int], files_count: int):
        """Print summary of results."""
        if not self.config.get('output.show_summary', True):
            return
        
        print(f"\n{'='*60}")
        print("📋 CODE QUALITY SUMMARY")
        print(f"{'='*60}")
        print(f"Files checked: {files_count}")
        print(f"Total errors: {total_errors}")
        
        max_total_errors = self.config.get('limits.max_total_errors', 0)
        print(f"Error limit: {max_total_errors}")
        
        if error_summary:
            print(f"\n📁 Files with errors:")
            tree_view = self._build_file_tree(error_summary)
            print(tree_view)
        
        # Determine overall status
        if total_errors == 0:
            print("\n✅ Perfect code quality! No style issues found.")
        elif total_errors <= max_total_errors:
            print(f"\n✅ Code quality within acceptable limits ({total_errors}/{max_total_errors} errors)")
        elif total_errors <= 10:
            print(f"\n⚠️  Minor code quality issues ({total_errors} errors)")
        elif total_errors <= 50:
            print(f"\n⚠️  Moderate code quality issues ({total_errors} errors)")
        else:
            print(f"\n❌ Poor code quality - many issues found ({total_errors} errors)")
        
        # Show suggestions if enabled
        if self.config.get('output.show_suggestions', True) and total_errors > 0:
            self._show_suggestions()
        
        print(f"{'='*60}")
    
    def _show_suggestions(self):
        """Show improvement suggestions."""
        print(f"\n💡 Suggestions:")
        
        # Modern tools (2025 recommendations)
        if self.config.get('tools.suggest_ruff', True):
            print("   • 🚀 Use 'ruff check .' for ultra-fast linting (modern replacement for flake8)")
            print("   • 🚀 Use 'ruff format .' for ultra-fast formatting (modern replacement for black)")
        
        # Traditional tools (still popular)
        if self.config.get('tools.suggest_black', True):
            print("   • Run 'black .' to auto-format code (PEP 8 compliant)")
        
        if self.config.get('tools.suggest_isort', True):
            print("   • Run 'isort .' to organize imports")
        
        # Type checking (important for modern Python)
        if self.config.get('tools.suggest_mypy', True):
            print("   • Add 'mypy .' for static type checking")
        
        # Less common but still useful
        if self.config.get('tools.suggest_flake8', False):
            print("   • Consider using 'flake8' for additional checks")
        
        if self.config.get('tools.suggest_pylint', False):
            print("   • Consider using 'pylint' for comprehensive analysis")
        
        # Configuration and automation
        print("   • Set up pre-commit hooks for automatic checking")
        print("   • Create or update .scli-quality.yml for custom configuration")
        
        # Modern workflow suggestions
        if self.config.get('compatibility.ruff_compatible', True):
            print("   • 💡 Consider migrating to Ruff for 10-100x faster linting + formatting")
        
        if self.config.get('compatibility.black_compatible', True):
            print("   • ✨ Your configuration is Black-compatible for seamless integration")


def generate_shortcut_command(mode: str, verbose: bool, config_file: Optional[str] = None) -> str:
    """Generate equivalent command line for the current selection."""
    cmd_parts = ["uv run python scripts/code_quality_checker.py"]
    
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
        description='Code quality checker for Python files using pycodestyle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s --mode all --verbose              # Check all files verbosely
  %(prog)s --mode staged --no-verbose        # Check staged files quietly
  %(prog)s --mode modified                   # Check modified files
"""
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['all', 'staged', 'unstaged', 'modified', 'tracked'],
        help='File evaluation mode (default: from config or "all")'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output (shows details for each file)'
    )
    
    parser.add_argument(
        '--no-verbose',
        action='store_true',
        help='Disable verbose output'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (default: .scli-quality.yml)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for code quality checker."""
    if not pycodestyle:
        print("❌ Error: pycodestyle is required for this script")
        print("📦 Install with: pip install pycodestyle")
        if __name__ == "__main__":
            sys.exit(1)
        else:
            return
    
    # Parse command line arguments only if run directly
    if __name__ == "__main__":
        args = parse_arguments()
    else:
        # Create dummy args when run through SCLI
        args = argparse.Namespace(mode=None, verbose=False, no_verbose=False, config=None)
    
    project_root = Path.cwd()
    
    # Look for configuration file
    if args.config:
        config_file = Path(args.config)
    else:
        config_file = project_root / '.scli-quality.yml'
        if not config_file.exists():
            config_file = project_root / '.scli-quality.yaml'
    
    config = CodeQualityConfig(config_file if config_file.exists() else None)
    checker = CodeQualityChecker(project_root, config)
    
    print("🔍 Code Quality Checker")
    print(f"📁 Project: {project_root}")
    
    if config_file.exists():
        print(f"⚙️  Config: {config_file.name}")
    else:
        print("⚙️  Config: Default (create .scli-quality.yml to customize)")
    
    if checker.git_root != project_root:
        print(f"🔗 Git root: {checker.git_root}")
    
    # Track if we used interactive mode for shortcut generation
    interactive_mode = False
    
    # Determine evaluation mode
    if args.mode:
        mode = args.mode
    else:
        interactive_mode = True
        # Get default mode from config
        default_mode = config.get('default_mode', 'all')
        
        # Ask for evaluation mode if not specified
        modes = [
            "📁 All Python files in project",
            "📋 Git staged files only",
            "📝 Git unstaged files only", 
            "🔄 Git modified files (staged + unstaged)",
            "🗂️  Git tracked files only"
        ]
        
        mode_mapping = {
            "📁 All Python files in project": 'all',
            "📋 Git staged files only": 'staged',
            "📝 Git unstaged files only": 'unstaged',
            "🔄 Git modified files (staged + unstaged)": 'modified',
            "🗂️  Git tracked files only": 'tracked'
        }
        
        selected_mode = simple_menu("Select evaluation mode:", modes)
        if selected_mode is None:
            print("Operation cancelled.")
            if __name__ == "__main__":
                sys.exit(0)
            else:
                return
        
        mode = mode_mapping[selected_mode]
    
    # Determine verbose mode
    if args.verbose:
        verbose = True
    elif args.no_verbose:
        verbose = False
    else:
        if not interactive_mode:
            interactive_mode = True
        # Ask for verbose mode (use config default)
        default_verbose = config.get('output.verbose', False)
        verbose = confirm(f"Enable verbose output? (shows details for each file)", default=default_verbose)
    
    # Show shortcut command if interactive mode was used
    if interactive_mode:
        config_name = config_file.name if config_file.exists() and config_file.name != ".scli-quality.yml" else None
        shortcut_cmd = generate_shortcut_command(mode, verbose, config_name)
        print(f"\n💡 Shortcut for next time:")
        print(f"   {shortcut_cmd}")
    
    start_time = time.time()
    start_time_str = datetime.now().strftime('%H:%M:%S')
    
    # Get files and check quality
    files = checker.get_files_to_check(mode)
    total_errors, error_summary = checker.check_code_quality(files, verbose)
    
    # Print results with completion time
    elapsed_time = time.time() - start_time
    end_time_str = datetime.now().strftime('%H:%M:%S')
    print(f"⏱️  Finalizado a las {end_time_str} ({elapsed_time:.2f} segundos)")
    
    checker.print_summary(total_errors, error_summary, len(files))
    
    # Check if we should exit with error code based on limits
    max_total_errors = config.get('limits.max_total_errors', 0)
    if total_errors > max_total_errors:
        print(f"\n❌ Quality check failed: {total_errors} errors exceed limit of {max_total_errors}")
        if __name__ == "__main__":
            sys.exit(1)
    else:
        print(f"\n✅ Quality check passed: {total_errors} errors within limit of {max_total_errors}")
        if __name__ == "__main__":
            sys.exit(0)


if __name__ == "__main__":
    main()