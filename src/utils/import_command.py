#!/usr/bin/env python3
"""
Dynamic command importer for SCLI commands

Provides dynamic import functionality for commands based on command names.
Similar to import_controller but adapted for CLI commands.
"""

import sys
from importlib import import_module
from pathlib import Path
from traceback import format_exc as traceback_format_exc
from typing import Any, Dict

# Add the current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from utils.logger import get_logger


def snake_to_pascal(snake_str: str) -> str:
    """
    Convert snake_case to PascalCase.
    
    Args:
        snake_str: String in snake_case format
        
    Returns:
        String in PascalCase format
        
    Example:
        >>> snake_to_pascal("hello_world")
        'HelloWorld'
    """
    return ''.join(word.capitalize() for word in snake_str.split('_'))


def import_command(command_name: str) -> Dict[str, Any]:
    """
    Dynamically import a command based on the command name.
    
    Args:
        command_name: Name of the command to import (in snake_case)
        
    Returns:
        Dictionary with import result:
        - is_valid: True if successful, False otherwise
        - data: Command information if successful, error info if failed
        - code: 0 for success, 1+ for errors
        
    Example:
        >>> result = import_command("hello_world")
        >>> result['is_valid']  # True
        >>> result['data']['command_class']  # HelloWorldCommand class
    """
    logger = get_logger("import_command")
    
    if not command_name:
        return {
            'is_valid': False,
            'data': {
                'error_code': 'INVALID_COMMAND_NAME',
                'message': 'Command name cannot be empty',
                'command_name': command_name
            },
            'code': 1
        }
    
    # Convert command name to class name
    class_name = snake_to_pascal(command_name) + "Command"
    
    # Try to import the command module
    try:
        module = import_module(f"commands.{command_name}")
        logger.debug(f"Successfully imported module: commands.{command_name}")
        
    except (ImportError, ModuleNotFoundError) as e:
        logger.error(
            f"Failed to import command module '{command_name}'",
            extra={
                'command_name': command_name,
                'error': str(e),
                'traceback': traceback_format_exc(),
            }
        )
        return {
            'is_valid': False,
            'data': {
                'error_code': 'MODULE_NOT_FOUND',
                'message': f"Command module '{command_name}' not found",
                'command_name': command_name,
                'expected_module': f"commands.{command_name}",
                'error_details': str(e)
            },
            'code': 1
        }
        
    except Exception as e:
        logger.error(
            f"Unexpected error importing command module '{command_name}'",
            extra={
                'command_name': command_name,
                'error': str(e),
                'traceback': traceback_format_exc(),
            }
        )
        return {
            'is_valid': False,
            'data': {
                'error_code': 'IMPORT_ERROR',
                'message': "Unexpected error importing command",
                'command_name': command_name,
                'error_details': str(e)
            },
            'code': 1
        }
    
    # Try to get the command class from the module
    try:
        command_class = getattr(module, class_name)
        logger.debug(f"Successfully found command class: {class_name}")
        
    except AttributeError:
        # Try to get command_instance as fallback
        command_instance = getattr(module, 'command_instance', None)
        if command_instance:
            logger.debug(f"Found command_instance in module: {command_name}")
            command_class = command_instance.__class__
        else:
            logger.error(
                f"Command class '{class_name}' not found in module '{command_name}'",
                extra={
                    'command_name': command_name,
                    'class_name': class_name,
                    'module_attributes': [attr for attr in dir(module) if not attr.startswith('_')],
                    'traceback': traceback_format_exc(),
                }
            )
            return {
                'is_valid': False,
                'data': {
                    'error_code': 'CLASS_NOT_FOUND',
                    'message': f"Command class '{class_name}' not found in module '{command_name}'",
                    'command_name': command_name,
                    'expected_class': class_name,
                    'available_attributes': [attr for attr in dir(module) if not attr.startswith('_')]
                },
                'code': 1
            }
    
    # Get additional command information
    description = getattr(module, 'DESCRIPTION', f"Command: {command_name}")
    main_func = getattr(module, 'main', None)
    command_instance = getattr(module, 'command_instance', None)
    
    # Determine command type
    if command_instance:
        command_type = "command_class"
        # Use existing instance
        final_command_instance = command_instance
    elif hasattr(command_class, 'run'):
        command_type = "command_class"
        # Create new instance
        try:
            final_command_instance = command_class()
        except Exception as e:
            logger.error(f"Failed to instantiate command class {class_name}: {e}")
            return {
                'is_valid': False,
                'data': {
                    'error_code': 'INSTANTIATION_ERROR',
                    'message': f"Failed to instantiate command class '{class_name}'",
                    'command_name': command_name,
                    'error_details': str(e)
                },
                'code': 1
            }
    elif main_func:
        command_type = "legacy"
        final_command_instance = None
    else:
        logger.error(f"No valid command interface found in module '{command_name}'")
        return {
            'is_valid': False,
            'data': {
                'error_code': 'INVALID_COMMAND_INTERFACE',
                'message': f"No valid command interface found in module '{command_name}'",
                'command_name': command_name,
                'details': "Command must have either command_instance, a class with run method, or main function"
            },
            'code': 1
        }
    
    # Success - return all command information
    data = {
        'command_name': command_name,
        'class_name': class_name,
        'module': module,
        'command_class': command_class,
        'command_instance': final_command_instance,
        'description': description,
        'main_func': main_func,
        'type': command_type,
        'module_path': getattr(module, '__file__', None)
    }
    
    logger.info(f"Successfully imported command: {command_name} (type: {command_type})")
    
    return {
        'is_valid': True,
        'data': data,
        'code': 0
    }


def list_available_commands() -> Dict[str, Any]:
    """
    List all available commands by scanning the commands directory.
    
    Returns:
        Dictionary with list of available commands
    """
    logger = get_logger("import_command")
    
    try:
        # Get the commands directory path
        current_file = Path(__file__)
        commands_dir = current_file.parent.parent / "commands"
        
        if not commands_dir.exists():
            return {
                'is_valid': False,
                'data': {
                    'error_code': 'COMMANDS_DIR_NOT_FOUND',
                    'message': f"Commands directory not found: {commands_dir}",
                    'expected_path': str(commands_dir)
                },
                'code': 1
            }
        
        # Scan for Python files
        command_files = []
        for file_path in commands_dir.glob("*.py"):
            if file_path.name != "__init__.py":
                command_name = file_path.stem
                command_files.append({
                    'name': command_name,
                    'file_path': str(file_path),
                    'class_name': snake_to_pascal(command_name) + "Command"
                })
        
        logger.debug(f"Found {len(command_files)} command files")
        
        return {
            'is_valid': True,
            'data': {
                'commands': command_files,
                'total': len(command_files),
                'commands_dir': str(commands_dir)
            },
            'code': 0
        }
        
    except Exception as e:
        logger.error(f"Error listing available commands: {e}")
        return {
            'is_valid': False,
            'data': {
                'error_code': 'SCAN_ERROR',
                'message': f"Error scanning commands directory: {e}",
                'error_details': str(e)
            },
            'code': 1
        }


def validate_command_exists(command_name: str) -> bool:
    """
    Quick validation to check if a command exists without importing it.
    
    Args:
        command_name: Name of the command to check
        
    Returns:
        True if command exists, False otherwise
    """
    available_result = list_available_commands()
    if not available_result['is_valid']:
        return False
    
    commands = available_result['data']['commands']
    return any(cmd['name'] == command_name for cmd in commands)