#!/usr/bin/env python3
"""
Command Handler for SCLI

Generic command handler that provides a framework for executing commands using:
- Argument validation using validation system
- Controller-based architecture with phases (preload -> validate -> execute)
- Dynamic command loading based on command name
- Comprehensive logging and observability
- Result handling with success/error responses

Inspired by lambda handler patterns but adapted for CLI usage.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from script_loader import CommandLoader
from utils.logger import get_logger
from utils.validation import ValidationCore, ValidationResult, validate_command_args, ValidationErrorMapping

__version__ = '1.0.0'


class CommandHandler:
    """
    Generic command handler for SCLI commands.
    
    Provides a standardized way to execute commands with validation,
    logging, and error handling.
    """
    
    def __init__(self):
        self.logger = get_logger("command_handler")
        self.loader = CommandLoader()
        
    def execute_command(
        self,
        command_name: str,
        args: List[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute a command with full validation and error handling.
        
        Args:
            command_name: Name of the command to execute
            args: Command line arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Dictionary containing execution results and metadata
        """
        start_time = time.time()
        
        self.logger.info(f"Command execution started: {command_name}")
        
        try:
            # Discover available commands
            commands = self.loader.discover_commands()
            
            if not commands:
                error_msg = "No commands found in the commands directory"
                self.logger.error(error_msg)
                return self._create_error_response(
                    error_msg, 
                    start_time,
                    command_name
                )
            
            # Validate command exists
            if command_name not in commands:
                available = list(commands.keys())
                error_msg = f"Command '{command_name}' not found. Available: {available}"
                self.logger.error(error_msg)
                return self._create_error_response(
                    error_msg,
                    start_time, 
                    command_name
                )
            
            command_info = commands[command_name]
            
            # Execute based on command type
            if command_info["type"] == "command_class":
                return self._execute_command_class(
                    command_info, 
                    command_name,
                    args or [],
                    start_time
                )
            else:
                return self._execute_legacy_command(
                    command_info,
                    command_name, 
                    args or [],
                    start_time
                )
        
        except Exception as e:
            error_msg = f"Unexpected error executing command '{command_name}': {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_response(
                error_msg,
                start_time,
                command_name
            )
    
    def _execute_command_class(
        self,
        command_info: Dict[str, Any],
        command_name: str,
        args: List[str],
        start_time: float
    ) -> Dict[str, Any]:
        """Execute a command using the new command class format"""
        
        command_instance = command_info["command_instance"]
        
        try:
            self.logger.info(f"Executing command class: {command_name}")
            
            # Execute the command with cascading methods
            result = command_instance.run(*args)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Enhance result with metadata
            result.update({
                'command': command_name,
                'command_type': 'command_class',
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'args': args
            })
            
            if result.get("success", False):
                self.logger.info(f"Command {command_name} completed successfully in {duration:.2f}s")
            else:
                self.logger.error(f"Command {command_name} failed after {duration:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing command class {command_name}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_response(error_msg, start_time, command_name)
    
    def _execute_legacy_command(
        self,
        command_info: Dict[str, Any],
        command_name: str,
        args: List[str],
        start_time: float
    ) -> Dict[str, Any]:
        """Execute a command using the legacy format"""
        
        try:
            self.logger.info(f"Executing legacy command: {command_name}")
            
            # Execute using the command loader
            success = self.loader.execute_command(command_name, {command_name: command_info}, args)
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                'success': success,
                'command': command_name,
                'command_type': 'legacy',
                'description': command_info.get('description', ''),
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'args': args,
                'results': {},
                'warnings': [],
                'errors': []
            }
            
            if success:
                self.logger.info(f"Legacy command {command_name} completed successfully in {duration:.2f}s")
            else:
                error_msg = f"Legacy command {command_name} failed"
                result['errors'].append(error_msg)
                self.logger.error(f"{error_msg} after {duration:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing legacy command {command_name}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_response(error_msg, start_time, command_name)
    
    def _create_error_response(
        self,
        error_message: str,
        start_time: float,
        command_name: str = "unknown"
    ) -> Dict[str, Any]:
        """Create a standardized error response"""
        
        end_time = time.time()
        
        return {
            'success': False,
            'command': command_name,
            'command_type': 'unknown',
            'description': '',
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'results': {},
            'warnings': [],
            'errors': [error_message],
            'error_message': error_message
        }
    
    def validate_command_arguments(
        self,
        args: Dict[str, Any],
        validation_schema: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate command arguments using the validation system.
        
        Args:
            args: Arguments to validate
            validation_schema: Validation rules
            
        Returns:
            ValidationResult with validation outcome
        """
        try:
            # Run validations
            validation_results = validate_command_args(args, validation_schema)
            
            # Check if all validations passed
            failed_validations = [r for r in validation_results if not r.is_valid]
            
            if failed_validations:
                # Format error message
                error_message = ValidationErrorMapping.format_validation_errors(failed_validations)
                
                return ValidationResult(
                    is_valid=False,
                    error_message=error_message,
                    data={'validation_errors': failed_validations},
                    code=1
                )
            
            # Extract validated data
            validated_data = {}
            for result in validation_results:
                if result.is_valid and result.field:
                    validated_data[result.field] = result.data
            
            return ValidationResult(
                is_valid=True,
                data=validated_data,
                code=0
            )
            
        except Exception as e:
            error_msg = f"Validation error: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            return ValidationResult(
                is_valid=False,
                error_message=error_msg,
                code=1
            )
    
    def list_commands(self) -> Dict[str, Any]:
        """
        List all available commands with their information.
        
        Returns:
            Dictionary containing command information
        """
        try:
            commands = self.loader.discover_commands()
            
            command_list = []
            for name, info in commands.items():
                command_list.append({
                    'name': name,
                    'description': info.get('description', ''),
                    'type': info.get('type', 'unknown'),
                    'path': str(info.get('path', ''))
                })
            
            return {
                'success': True,
                'commands': command_list,
                'total': len(command_list)
            }
            
        except Exception as e:
            error_msg = f"Error listing commands: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error_message': error_msg,
                'commands': [],
                'total': 0
            }
    
    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """
        Get help information for a specific command.
        
        Args:
            command_name: Name of the command
            
        Returns:
            Dictionary containing help information
        """
        try:
            commands = self.loader.discover_commands()
            
            if command_name not in commands:
                return {
                    'success': False,
                    'error_message': f"Command '{command_name}' not found",
                    'help_text': ''
                }
            
            help_text = self.loader.get_command_help(command_name, commands)
            
            return {
                'success': True,
                'command': command_name,
                'help_text': help_text,
                'type': commands[command_name].get('type', 'unknown')
            }
            
        except Exception as e:
            error_msg = f"Error getting help for command '{command_name}': {e}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error_message': error_msg,
                'help_text': ''
            }


def command_handler(
    command_name: str,
    args: List[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Main command handler function.
    
    Generic handler for SCLI commands with validation and error handling.
    
    Args:
        command_name: Name of the command to execute
        args: List of command arguments
        **kwargs: Additional keyword arguments
        
    Returns:
        Dictionary containing execution results and metadata
        
    Example:
        >>> result = command_handler("hello_world", [])
        >>> print(result['success'])  # True
        >>> print(result['duration'])  # 0.05
    """
    handler = CommandHandler()
    return handler.execute_command(command_name, args, **kwargs)