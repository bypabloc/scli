#!/usr/bin/env python3
"""
Dynamic Command Handler for SCLI

Generic command handler that uses dynamic import and provides a framework for executing commands using:
- Dynamic command loading based on command name
- Argument validation using CommandModel and Pydantic
- Command-based architecture with phases (preload -> validate -> execute)
- Comprehensive logging and observability
- Result handling with success/error responses

Inspired by lambda handler patterns but adapted for CLI usage with dynamic imports.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add the current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from models.command_model import CommandModel
from utils.logger import get_logger
from utils.import_command import import_command, list_available_commands

__version__ = '1.0.0'


class DynamicCommandHandler:
    """
    Dynamic command handler for SCLI commands.
    
    Provides a standardized way to execute commands with dynamic import,
    validation, logging, and error handling.
    """
    
    def __init__(self):
        self.logger = get_logger("dynamic_command_handler")
        
    def execute_command_event(
        self,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a command from an event dictionary.
        
        Similar to lambda_handler but for CLI commands.
        
        Args:
            event: Dictionary containing:
                - command: Name of the command to execute
                - args: List of command arguments (optional)
                - data: Additional data for the command (optional)
                
        Returns:
            Dictionary containing execution results and metadata
            
        Example:
            >>> event = {
            ...     "command": "hello_world",
            ...     "args": ["--verbose"],
            ...     "data": {"key": "value"}
            ... }
            >>> result = handler.execute_command_event(event)
        """
        start_time = time.time()
        
        self.logger.info("Command execution started")
        self.logger.info(f"Command event received: {event}")
        
        try:
            # Validate event structure using CommandModel
            validation_result = self._validate_command_event(event)
            if not validation_result.get('is_valid'):
                validation_data = validation_result.get('data', {})
                error_response = validation_data.get('error_response')
                if error_response:
                    return error_response
                
                # Fallback error response
                return self._create_error_response(
                    'Event validation failed',
                    start_time,
                    'unknown'
                )
            
            validated_event = validation_result.get('data')
            
            # Extract command information
            command_name = validated_event.get_command_name()
            command_type = validated_event.get_command_type()
            
            self.logger.info(f"Executing command: {command_name} (type: {command_type})")
            
            # Execute command based on type
            if command_type == "command_class":
                return self._execute_command_class(
                    validated_event,
                    command_name,
                    start_time
                )
            else:
                return self._execute_legacy_command(
                    validated_event,
                    command_name,
                    start_time
                )
        
        except Exception as e:
            error_msg = f"Unexpected error executing command: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_response(
                error_msg,
                start_time,
                event.get('command', 'unknown')
            )
    
    def execute_command_from_args(
        self,
        command_name: str,
        args: List[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a command from command name and arguments.
        
        Args:
            command_name: Name of the command to execute
            args: List of command arguments
            
        Returns:
            Dictionary containing execution results and metadata
        """
        event = {
            'command': command_name,
            'args': args or [],
            'data': {}
        }
        
        return self.execute_command_event(event)
    
    def _validate_command_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate command event using CommandModel.
        
        Args:
            event: Event dictionary to validate
            
        Returns:
            Validation result dictionary
        """
        try:
            # Validate using CommandModel
            validated_event = CommandModel.validate_command_event(event)
            
            return {
                'is_valid': True,
                'data': validated_event,
                'code': 0
            }
            
        except ValueError as ve:
            self.logger.error(f"Command validation error: {ve}")
            return {
                'is_valid': False,
                'data': {
                    'error_response': self._create_error_response(
                        str(ve),
                        time.time(),
                        event.get('command', 'unknown')
                    )
                },
                'code': 1
            }
        
        except Exception as e:
            self.logger.error(f"Unexpected validation error: {e}", exc_info=True)
            return {
                'is_valid': False,
                'data': {
                    'error_response': self._create_error_response(
                        f"Validation error: {e}",
                        time.time(),
                        event.get('command', 'unknown')
                    )
                },
                'code': 1
            }
    
    def _execute_command_class(
        self,
        validated_event: CommandModel,
        command_name: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Execute a command using the new command class format"""
        
        try:
            # Get command instance
            command_instance = validated_event.get_command_instance()
            
            if not command_instance:
                # Create new instance if not available
                command_class = validated_event.get_command_class()
                if not command_class:
                    error_msg = f"No command class or instance available for {command_name}"
                    self.logger.error(error_msg)
                    return self._create_error_response(error_msg, start_time, command_name)
                
                command_instance = command_class()
            
            # Execute the command with cascading methods
            self.logger.info(f"Executing command class: {command_name}")
            
            # Prepare arguments for the command
            args = validated_event.command_args
            kwargs = validated_event.command_data
            
            result = command_instance.run(*args, **kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Enhance result with metadata
            result.update({
                'command': command_name,
                'command_type': 'command_class',
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'args': args,
                'data': kwargs,
                'validated_event': validated_event.model_dump()
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
        validated_event: CommandModel,
        command_name: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Execute a command using the legacy format"""
        
        try:
            self.logger.info(f"Executing legacy command: {command_name}")
            
            # Get main function
            command_info = validated_event.command_info.get('data', {})
            main_func = command_info.get('main_func')
            
            if not main_func:
                error_msg = f"No main function available for legacy command {command_name}"
                self.logger.error(error_msg)
                return self._create_error_response(error_msg, start_time, command_name)
            
            # Prepare arguments
            args = validated_event.command_args
            
            # Execute legacy command
            original_argv = sys.argv.copy()
            try:
                # Set command arguments
                sys.argv = [f"scli_{command_name}"] + args
                
                # Execute main function
                main_func()
                success = True
                
            finally:
                # Restore original argv
                sys.argv = original_argv
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                'success': success,
                'command': command_name,
                'command_type': 'legacy',
                'description': validated_event.get_description(),
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'args': args,
                'results': {},
                'warnings': [],
                'errors': [],
                'validated_event': validated_event.model_dump()
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
    
    def list_commands(self) -> Dict[str, Any]:
        """
        List all available commands using dynamic discovery.
        
        Returns:
            Dictionary containing command information
        """
        try:
            # Use dynamic command listing
            commands_result = list_available_commands()
            
            if not commands_result['is_valid']:
                error_data = commands_result['data']
                return {
                    'success': False,
                    'error_message': error_data.get('message', 'Failed to list commands'),
                    'commands': [],
                    'total': 0
                }
            
            commands_data = commands_result['data']
            command_files = commands_data['commands']
            
            # Try to import each command to get detailed info
            command_list = []
            for cmd_file in command_files:
                command_name = cmd_file['name']
                
                try:
                    import_result = import_command(command_name)
                    if import_result['is_valid']:
                        cmd_data = import_result['data']
                        command_list.append({
                            'name': command_name,
                            'description': cmd_data.get('description', ''),
                            'type': cmd_data.get('type', 'unknown'),
                            'class_name': cmd_data.get('class_name', ''),
                            'file_path': cmd_file['file_path']
                        })
                    else:
                        # Add with limited info if import failed
                        command_list.append({
                            'name': command_name,
                            'description': f"Import failed: {import_result['data'].get('message', 'Unknown error')}",
                            'type': 'error',
                            'class_name': cmd_file['class_name'],
                            'file_path': cmd_file['file_path']
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error getting info for command {command_name}: {e}")
                    command_list.append({
                        'name': command_name,
                        'description': f"Error: {e}",
                        'type': 'error',
                        'class_name': cmd_file['class_name'],
                        'file_path': cmd_file['file_path']
                    })
            
            return {
                'success': True,
                'commands': command_list,
                'total': len(command_list),
                'commands_dir': commands_data.get('commands_dir', '')
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
        Get help information for a specific command using dynamic import.
        
        Args:
            command_name: Name of the command
            
        Returns:
            Dictionary containing help information
        """
        try:
            # Import command dynamically
            import_result = import_command(command_name)
            
            if not import_result['is_valid']:
                error_data = import_result['data']
                return {
                    'success': False,
                    'error_message': error_data.get('message', f"Command '{command_name}' not found"),
                    'help_text': ''
                }
            
            cmd_data = import_result['data']
            
            # Try to get help from command instance
            help_text = ""
            command_instance = cmd_data.get('command_instance')
            
            if command_instance and hasattr(command_instance, 'get_help'):
                try:
                    help_text = command_instance.get_help()
                except Exception as e:
                    self.logger.warning(f"Failed to get help from command instance: {e}")
            
            # Fallback to basic information
            if not help_text:
                help_text = f"""
{command_name} - {cmd_data.get('description', 'No description available')}

Type: {cmd_data.get('type', 'unknown')}
Class: {cmd_data.get('class_name', 'N/A')}
Module: {cmd_data.get('module_path', 'N/A')}
"""
            
            return {
                'success': True,
                'command': command_name,
                'help_text': help_text,
                'type': cmd_data.get('type', 'unknown'),
                'description': cmd_data.get('description', ''),
                'class_name': cmd_data.get('class_name', '')
            }
            
        except Exception as e:
            error_msg = f"Error getting help for command '{command_name}': {e}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error_message': error_msg,
                'help_text': ''
            }


def dynamic_command_handler(
    command_name: str,
    args: List[str] = None,
    **data: Any
) -> Dict[str, Any]:
    """
    Main dynamic command handler function.
    
    Generic handler for SCLI commands with dynamic import and validation.
    
    Args:
        command_name: Name of the command to execute
        args: List of command arguments
        **data: Additional keyword arguments
        
    Returns:
        Dictionary containing execution results and metadata
        
    Example:
        >>> result = dynamic_command_handler("hello_world", ["--verbose"])
        >>> print(result['success'])  # True
        >>> print(result['duration'])  # 0.05
    """
    handler = DynamicCommandHandler()
    return handler.execute_command_from_args(command_name, args)


def dynamic_event_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamic event handler for command events.
    
    Args:
        event: Event dictionary with command, args, and data
        
    Returns:
        Dictionary containing execution results and metadata
    """
    handler = DynamicCommandHandler()
    return handler.execute_command_event(event)