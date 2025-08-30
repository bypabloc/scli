#!/usr/bin/env python3
"""
Base Command Class for SCLI Commands

This module provides the BaseCommand abstract class that all SCLI commands should inherit from.
It defines a standard execution flow with cascading methods for consistent command behavior.
"""

import os
import sys
import traceback
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from logger import get_logger
    from config_loader import get_script_config
    from output_manager import OutputManager
    from menu_utils import confirm, interactive_menu, text_input
except ImportError as e:
    print(f"Warning: Could not import SCLI modules: {e}")
    # Fallback implementations
    def get_logger(name):
        import logging
        return logging.getLogger(name)
    
    def get_script_config(name):
        return {}
    
    class OutputManager:
        def get_output_path(self, script_name, filename, subfolder=""):
            return Path.cwd() / "output" / script_name / filename
    
    def confirm(message, default=False):
        response = input(f"{message} ({'Y/n' if default else 'y/N'}): ")
        if not response:
            return default
        return response.lower().startswith('y')
    
    def interactive_menu(title, options):
        print(f"\n{title}")
        for i, option in enumerate(options, 1):
            name = option.get('name', str(option))
            description = option.get('description', '')
            print(f"  {i}. {name} - {description}")
        
        while True:
            try:
                choice = int(input("Select option: ")) - 1
                if 0 <= choice < len(options):
                    return options[choice]
                else:
                    print("Invalid choice, please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def text_input(prompt, default=""):
        response = input(f"{prompt}: ")
        return response if response else default


class CommandExecutionError(Exception):
    """Custom exception for command execution errors"""
    pass


class BaseCommand(ABC):
    """
    Base class for all SCLI commands.
    
    This class defines a standard execution flow with cascading methods:
    1. preload() - Check dependencies and prepare environment
    2. requirements() - Load configurations and validate requirements  
    3. validation() - Validate inputs and parameters
    4. execute() - Execute the main command logic
    5. output() - Handle output and results
    
    Additional utility methods:
    - setup() - Initial setup specific to the command
    - cleanup() - Clean up resources after execution
    - get_help() - Get command-specific help
    - get_version() - Get command version (if applicable)
    """
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """
        Initialize the base command.
        
        Args:
            name: Command name (defaults to class name)
            description: Command description (can be overridden by DESCRIPTION attribute)
        """
        self.name = name or self.__class__.__name__.lower()
        self.description = description or getattr(self, 'DESCRIPTION', 'No description available')
        self.logger = get_logger(self.name)
        self.config = {}
        self.output_manager = OutputManager()
        self.errors = []
        self.warnings = []
        self.results = {}
        self.is_setup = False
        self.is_validated = False
        self.execution_started = False
        
        # Command metadata
        self.version = getattr(self, 'VERSION', '1.0.0')
        self.author = getattr(self, 'AUTHOR', 'SCLI')
        self.dependencies = getattr(self, 'DEPENDENCIES', [])
        self.optional_dependencies = getattr(self, 'OPTIONAL_DEPENDENCIES', [])
        
        self.logger.debug(f"Initialized command: {self.name}")
    
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main entry point that executes the command with cascading methods.
        
        Returns:
            Dict containing execution results and metadata
        """
        self.logger.info(f"Starting execution of command: {self.name}")
        start_time = self._get_timestamp()
        
        try:
            # Execute cascading methods in order
            self.logger.debug("Step 1: Preload")
            preload_success = self.preload(*args, **kwargs)
            if not preload_success:
                raise CommandExecutionError("Preload failed")
            
            self.logger.debug("Step 2: Requirements")
            requirements_success = self.requirements(*args, **kwargs)
            if not requirements_success:
                raise CommandExecutionError("Requirements check failed")
            
            self.logger.debug("Step 3: Validation")
            validation_success = self.validation(*args, **kwargs)
            if not validation_success:
                raise CommandExecutionError("Validation failed")
            self.is_validated = True
            
            self.logger.debug("Step 4: Execute")
            self.execution_started = True
            execution_success = self.execute(*args, **kwargs)
            if not execution_success:
                raise CommandExecutionError("Command execution failed")
            
            self.logger.debug("Step 5: Output")
            output_success = self.output(*args, **kwargs)
            if not output_success:
                self.logger.warning("Output processing had issues, but command completed")
            
            # Success
            end_time = self._get_timestamp()
            self.logger.info(f"Command {self.name} completed successfully")
            
            return {
                'success': True,
                'command': self.name,
                'description': self.description,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'results': self.results,
                'warnings': self.warnings,
                'errors': []
            }
            
        except Exception as e:
            # Handle errors
            error_msg = str(e)
            self.logger.error(f"Command {self.name} failed: {error_msg}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            self.errors.append(error_msg)
            
            end_time = self._get_timestamp()
            
            return {
                'success': False,
                'command': self.name,
                'description': self.description,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'results': self.results,
                'warnings': self.warnings,
                'errors': self.errors,
                'error_message': error_msg
            }
        
        finally:
            # Always try to cleanup
            try:
                self.cleanup(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"Cleanup failed: {e}")
    
    # Cascading methods (to be implemented by subclasses)
    
    def preload(self, *args, **kwargs) -> bool:
        """
        Step 1: Check dependencies and prepare environment.
        
        This method should:
        - Check for required system dependencies
        - Verify external tools are available
        - Import required modules
        - Prepare the execution environment
        
        Returns:
            bool: True if preload successful, False otherwise
        """
        self.logger.debug("Running default preload")
        
        # Check Python dependencies
        missing_deps = self._check_dependencies()
        if missing_deps:
            self.logger.error(f"Missing required dependencies: {missing_deps}")
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            self._suggest_dependency_installation(missing_deps)
            return False
        
        # Check optional dependencies
        missing_optional = self._check_optional_dependencies()
        if missing_optional:
            self.logger.warning(f"Missing optional dependencies: {missing_optional}")
            print(f"⚠️  Optional dependencies not available: {', '.join(missing_optional)}")
            print("Some features may be limited.")
        
        return True
    
    def requirements(self, *args, **kwargs) -> bool:
        """
        Step 2: Load configurations and validate requirements.
        
        This method should:
        - Load command-specific configuration
        - Validate configuration values
        - Set up necessary parameters
        - Check system requirements
        
        Returns:
            bool: True if requirements met, False otherwise
        """
        self.logger.debug("Running default requirements check")
        
        # Load configuration
        self.config = get_script_config(self.name) or {}
        self.logger.debug(f"Loaded config for {self.name}: {bool(self.config)}")
        
        return True
    
    def validation(self, *args, **kwargs) -> bool:
        """
        Step 3: Validate inputs and parameters.
        
        This method should:
        - Validate user inputs
        - Check parameter format and ranges
        - Verify file paths and permissions
        - Validate external service connectivity
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        self.logger.debug("Running default validation")
        return True
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> bool:
        """
        Step 4: Execute the main command logic.
        
        This is the core method that must be implemented by all subclasses.
        It should contain the main functionality of the command.
        
        Returns:
            bool: True if execution successful, False otherwise
        """
        raise NotImplementedError("execute() method must be implemented by subclasses")
    
    def output(self, *args, **kwargs) -> bool:
        """
        Step 5: Handle output and results.
        
        This method should:
        - Format and display results
        - Save output files if needed
        - Generate reports or summaries
        - Clean up temporary files
        
        Returns:
            bool: True if output processing successful, False otherwise
        """
        self.logger.debug("Running default output processing")
        
        # Display results if available
        if self.results:
            print("\n📊 Command Results:")
            for key, value in self.results.items():
                print(f"  {key}: {value}")
        
        # Display warnings
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        return True
    
    # Additional utility methods
    
    def setup(self, *args, **kwargs) -> bool:
        """
        Initial setup specific to the command.
        Called before the main execution cascade.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        if self.is_setup:
            return True
        
        self.logger.debug("Running command setup")
        self.is_setup = True
        return True
    
    def cleanup(self, *args, **kwargs) -> bool:
        """
        Clean up resources after execution.
        Called after the main execution cascade.
        
        Returns:
            bool: True if cleanup successful, False otherwise  
        """
        self.logger.debug("Running command cleanup")
        return True
    
    def get_help(self) -> str:
        """
        Get command-specific help text.
        
        Returns:
            str: Help text for the command
        """
        help_text = f"""
{self.name} - {self.description}

Version: {self.version}
Author: {self.author}

Dependencies:
"""
        if self.dependencies:
            help_text += f"  Required: {', '.join(self.dependencies)}\n"
        else:
            help_text += "  Required: None\n"
            
        if self.optional_dependencies:
            help_text += f"  Optional: {', '.join(self.optional_dependencies)}\n"
        else:
            help_text += "  Optional: None\n"
        
        return help_text.strip()
    
    def get_version(self) -> str:
        """
        Get command version.
        
        Returns:
            str: Version string
        """
        return self.version
    
    # Internal utility methods
    
    def _check_dependencies(self) -> List[str]:
        """Check required dependencies and return missing ones."""
        missing = []
        for dep in self.dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        return missing
    
    def _check_optional_dependencies(self) -> List[str]:
        """Check optional dependencies and return missing ones."""
        missing = []
        for dep in self.optional_dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        return missing
    
    def _suggest_dependency_installation(self, missing_deps: List[str]):
        """Suggest how to install missing dependencies."""
        print("\n💡 To install missing dependencies:")
        for dep in missing_deps:
            print(f"  uv add {dep}")
        print()
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        self.logger.warning(message)
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.logger.error(message)
    
    def set_result(self, key: str, value: Any):
        """Set a result value."""
        self.results[key] = value
        self.logger.debug(f"Set result {key}: {value}")
    
    def get_result(self, key: str, default: Any = None) -> Any:
        """Get a result value."""
        return self.results.get(key, default)
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")
        self.logger.info(message)
    
    def print_success(self, message: str):
        """Print a success message.""" 
        print(f"✅ {message}")
        self.logger.info(message)
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"⚠️  {message}")
        self.add_warning(message)
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")
        self.add_error(message)


class SimpleCommand(BaseCommand):
    """
    A simplified command class for basic commands that don't need all the complexity.
    
    This class provides default implementations for most cascading methods,
    requiring only the execute() method to be implemented.
    """
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        super().__init__(name, description)
    
    def preload(self, *args, **kwargs) -> bool:
        """Simple preload - just check basic dependencies."""
        return super().preload(*args, **kwargs)
    
    def requirements(self, *args, **kwargs) -> bool:
        """Simple requirements - just load config."""
        return super().requirements(*args, **kwargs)
    
    def validation(self, *args, **kwargs) -> bool:
        """Simple validation - always pass."""
        return True


class InteractiveCommand(BaseCommand):
    """
    A command class for interactive commands that need user input.
    
    This class provides additional utilities for handling user interaction
    while maintaining the standard execution flow.
    """
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        super().__init__(name, description)
        self.user_inputs = {}
        self.parsed_args = {}
        self.validation_model = None
    
    def parse_arguments_to_dict(self, *args) -> Dict[str, Any]:
        """
        Transform command line arguments into a named dictionary.
        
        This method converts positional and named arguments into a structured
        dictionary format that can be validated by Pydantic models.
        
        Args:
            *args: Command line arguments
            
        Returns:
            Dict with parsed arguments using meaningful names
        """
        parsed = {}
        i = 0
        
        while i < len(args):
            arg = str(args[i])
            
            # Handle named arguments with = syntax (--key=value)
            if '=' in arg and arg.startswith('--'):
                key, value = arg.split('=', 1)
                key = key.lstrip('-').replace('-', '_')
                parsed[key] = self._parse_value(value)
            
            # Handle named arguments with separate value (--key value)
            elif arg.startswith('--') and i + 1 < len(args):
                key = arg.lstrip('-').replace('-', '_')
                next_arg = str(args[i + 1])
                
                # If next argument is also a flag, treat current as boolean
                if next_arg.startswith('-'):
                    parsed[key] = True
                else:
                    parsed[key] = self._parse_value(next_arg)
                    i += 1  # Skip next argument as it's the value
            
            # Handle short flags (-v, -f)
            elif arg.startswith('-') and not arg.startswith('--'):
                flags = arg.lstrip('-')
                for flag in flags:
                    # Map common short flags to full names
                    flag_mapping = {
                        'v': 'verbose',
                        'q': 'quiet',
                        'h': 'help',
                        'f': 'force',
                        'd': 'debug',
                        'o': 'output'
                    }
                    flag_name = flag_mapping.get(flag, flag)
                    
                    # Special case for flags that expect values
                    if flag in ['o'] and i + 1 < len(args) and not str(args[i + 1]).startswith('-'):
                        parsed[flag_name] = self._parse_value(str(args[i + 1]))
                        i += 1
                    else:
                        parsed[flag_name] = True
            
            # Handle positional arguments by position
            else:
                # Use generic position-based keys for positional args
                pos_key = f"arg_{i}"
                parsed[pos_key] = self._parse_value(arg)
            
            i += 1
        
        self.logger.debug(f"Parsed arguments: {parsed}")
        return parsed
    
    def _parse_value(self, value: str) -> Any:
        """
        Parse a string value to its appropriate type.
        
        Args:
            value: String value to parse
            
        Returns:
            Parsed value with appropriate type
        """
        if not isinstance(value, str):
            return value
        
        # Handle boolean strings
        if value.lower() in ('true', '1', 'yes', 'y', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'n', 'off'):
            return False
        
        # Handle numeric strings
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # Handle None/null
        if value.lower() in ('none', 'null'):
            return None
        
        # Return as string if no other type matches
        return value
    
    def preload(self, *args, **kwargs) -> bool:
        """
        Enhanced preload method that parses arguments to dict before dependency checks.
        
        This method transforms all arguments to a dictionary with meaningful names
        before processing the first flag (script flag).
        
        Returns:
            bool: True if preload successful, False otherwise
        """
        self.logger.debug("Starting enhanced preload with argument parsing")
        
        # Step 1: Parse arguments to dictionary BEFORE any other processing
        self.parsed_args = self.parse_arguments_to_dict(*args)
        self.logger.info(f"Arguments parsed to dict: {self.parsed_args}")
        
        # Step 2: Continue with standard dependency checking
        return super().preload(*args, **kwargs)
    
    def validation(self, *args, **kwargs) -> bool:
        """
        Enhanced validation method using Pydantic models.
        
        This method must be overridden by subclasses to provide specific
        validation logic using Pydantic models.
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        if self.validation_model is None:
            self.logger.warning("No validation model defined for command")
            return super().validation(*args, **kwargs)
        
        try:
            # Validate using the Pydantic model
            validated_data = self.validation_model(**self.parsed_args)
            
            # Store validated data for use in execute method
            self.parsed_args = validated_data.model_dump()
            
            self.logger.info("Validation successful using Pydantic model")
            return True
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.logger.error(error_msg)
            self.print_error(error_msg)
            return False
    
    def get_user_input(self, prompt: str, default: str = "", validator=None) -> str:
        """Get input from user with optional validation."""
        while True:
            value = text_input(prompt, default)
            if validator is None or validator(value):
                self.user_inputs[prompt] = value
                return value
            else:
                print("❌ Invalid input, please try again.")
    
    def get_user_choice(self, title: str, options: List[Dict]) -> Optional[Dict]:
        """Get user choice from interactive menu."""
        choice = interactive_menu(title, options)
        if choice:
            self.user_inputs[title] = choice
        return choice
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Get user confirmation."""
        result = confirm(message, default)
        self.user_inputs[message] = result
        return result