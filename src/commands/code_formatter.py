#!/usr/bin/env python3
"""
Code Formatter Command - Automatic Python code formatting
"""

import os
import subprocess
import sys
from typing import List

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.code_formatter_model import CodeFormatterModel
from utils.code_formatter_utils import CodeFormatterConfig, CodeFormatter, get_available_format_actions

DESCRIPTION = "🎨 Auto-format Python code based on specific formatting actions"


class CodeFormatterCommand(InteractiveCommand):
    """Code formatter command implementation"""
    
    # Set the validation model
    event_model = CodeFormatterModel
    
    def __init__(self):
        super().__init__(name="code_formatter", description=DESCRIPTION)
        self.validated_data = None
        self.formatter = None
    
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
                    elif arg == '--confirm':
                        data['confirm'] = True
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
                    elif arg == '--only' and i + 1 < len(args):
                        data['only_actions'] = args[i + 1].split(',')
                        i += 1
                    elif arg.startswith('--only='):
                        data['only_actions'] = arg.split('=', 1)[1].split(',')
                    # Handle enable/disable flags
                    elif arg.startswith('--enable-'):
                        action = arg[9:].replace('-', '_')
                        if 'enabled_actions' not in data:
                            data['enabled_actions'] = []
                        data['enabled_actions'].append(action)
                    elif arg.startswith('--disable-'):
                        action = arg[10:].replace('-', '_')
                        if 'disabled_actions' not in data:
                            data['disabled_actions'] = []
                        data['disabled_actions'].append(action)
                    i += 1
            
            # Add any kwargs
            data.update(kwargs)
            
            # Set defaults
            if 'mode' not in data:
                data['mode'] = 'all'
            if 'verbose' not in data:
                data['verbose'] = False
            if 'confirm' not in data:
                data['confirm'] = False
            
            # Validate using Pydantic model
            self.validated_data = self.event_model(**data)
            
            self.logger.debug(f"Arguments validated successfully: {self.validated_data.to_dict()}")
            return True
            
        except Exception as e:
            self.print_error(f"Argument validation failed: {e}")
            self.logger.error(f"Preload validation error: {e}")
            return False
    
    def requirements(self, *args, **kwargs) -> bool:
        """Check if code formatting tools are available"""
        try:
            # Create formatter to check tool availability
            project_root = self.validated_data.get_project_root_path()
            config_path = self.validated_data.get_config_path()
            
            # Load configuration
            config = CodeFormatterConfig(config_path)
            self.formatter = CodeFormatter(project_root, config)
            
            # Check available tools
            available_tools = [tool for tool, available in self.formatter.available_tools.items() if available]
            
            if not available_tools:
                self.print_error("No code formatting tools found!")
                self.print_info("Install tools with:")
                self.print_info("  uv add black isort autopep8 autoflake ruff")
                return False
            
            self.print_success(f"Code formatting tools available: {', '.join(available_tools)}")
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
        """Execute the code formatter command"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Get files to format
            self.print_info(f"Scanning for Python files in: {self.formatter.project_root}")
            self.print_info(f"Mode: {self.validated_data.mode}")
            
            files = self.formatter.get_files_to_format(self.validated_data.mode)
            
            if not files:
                self.print_warning("No Python files found to format")
                return True
            
            self.print_info(f"Found {len(files)} Python files to format")
            
            # Get actions to run
            default_actions = self._get_default_enabled_actions()
            final_actions = self.validated_data.get_final_actions(default_actions)
            
            if not final_actions:
                self.print_warning("No formatting actions enabled")
                return True
            
            self.print_info(f"Formatting actions: {', '.join(final_actions)}")
            
            # Confirm if not auto-confirming
            if not self.validated_data.confirm:
                if not self.confirm_action(f"Format {len(files)} files with {len(final_actions)} actions?"):
                    self.print_info("Operation cancelled")
                    return True
            
            # Apply formatting
            self.print_info("Applying formatting actions...")
            results = self.formatter.apply_format_actions(
                files, final_actions, self.validated_data.verbose
            )
            
            # Print summary
            self.formatter.print_summary(results, len(files))
            
            # Store results
            self.set_result("mode", self.validated_data.mode)
            self.set_result("files_formatted", len(files))
            self.set_result("actions_applied", results.get("actions_applied", []))
            self.set_result("actions_skipped", results.get("actions_skipped", []))
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return results.get("success", True)
        
        except Exception as e:
            self.print_error(f"Failed to execute code formatter: {e}")
            return False
    
    def _get_default_enabled_actions(self) -> List[str]:
        """Get default enabled actions from configuration"""
        format_config = self.formatter.config.get("format", {})
        
        # Get all available actions
        all_actions = get_available_format_actions()
        
        # Filter to only enabled actions based on config
        enabled_actions = []
        for action in all_actions:
            if format_config.get(action, False):
                enabled_actions.append(action)
        
        # If no actions are explicitly enabled in config, use a sensible default
        if not enabled_actions:
            enabled_actions = [
                "sort_imports",
                "remove_unused_imports", 
                "fix_indentation",
                "normalize_strings",
                "fix_line_length",
                "remove_trailing_spaces",
                "fix_whitespace",
                "remove_blank_lines",
                "ensure_newline_eof",
                "convert_tabs_to_spaces"
            ]
        
        return enabled_actions


# Create command instance for dynamic import
command_instance = CodeFormatterCommand()