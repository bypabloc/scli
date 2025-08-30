#!/usr/bin/env python3
"""
Command event model for SCLI dynamic command execution

Similar to EventModel but adapted for CLI commands with dynamic import.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from utils.import_command import import_command


class CommandModel(BaseModel):
    """
    Validation model for SCLI command events.
    
    Validates the required structure and returns complete command information:
    {
        "command": "hello_world",
        "args": ["--verbose", "--output=json"],
        "data": {
            "key": "value"
        }
    }
    
    Attributes:
        command_info: Complete command information obtained from import_command
        command_args: Prepared arguments for the command (without command name)
        command_data: Additional data for the command
    """
    
    command_info: Any = Field(
        ...,
        description="Command information obtained from import_command. Contains class_name, module, and command_class.",
        examples=[{
            'command_name': 'hello_world',
            'class_name': 'HelloWorldCommand',
            'module': '<module>',
            'command_class': '<class>',
        }]
    )
    
    command_args: list = Field(
        default_factory=list,
        description="Arguments prepared for the command (without command name)"
    )
    
    command_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional data for the command"
    )
    
    @classmethod
    def validate_command_event(cls, event: Dict[str, Any]) -> 'CommandModel':
        """
        Validate the command event and prepare data for command execution.
        
        Args:
            event: Complete event with command, args, and optional data
            
        Returns:
            CommandModel instance with command_info and prepared data
            
        Raises:
            ValueError: If the event is not valid
            
        Example:
            >>> event = {
            ...     "command": "hello_world",
            ...     "args": ["--verbose"],
            ...     "data": {"key": "value"}
            ... }
            >>> model = CommandModel.validate_command_event(event)
        """
        # Validate basic structure
        if not isinstance(event, dict):
            raise ValueError('Event must be a valid JSON object')
        
        if 'command' not in event:
            raise ValueError('Command is required')
        
        command_name = event['command']
        
        # Validate command name
        if command_name is None:
            raise ValueError('Command cannot be null')
        
        if not isinstance(command_name, str):
            raise ValueError('Command must be a string')
        
        if not command_name or not command_name.strip():
            raise ValueError('Command cannot be empty')
        
        command_name = command_name.strip()
        
        # Get args and data
        args = event.get('args', [])
        data = event.get('data', {})
        
        # Validate args
        if args is not None and not isinstance(args, list):
            raise ValueError('Args must be a list')
        
        # Validate data
        if data is not None and not isinstance(data, dict):
            raise ValueError('Data must be a JSON object')
        
        # Validate that the command exists and get its information
        command_result = import_command(command_name)
        
        if not command_result.get('is_valid'):
            error_data = command_result.get('data', {})
            message = error_data.get(
                'message',
                f"Command '{command_name}' not found"
            )
            
            raise ValueError(f"Command '{command_name}' is not valid: {message}")
        
        # Create instance with prepared data
        return cls(
            command_info=command_result,
            command_args=args or [],
            command_data=data or {}
        )
    
    def get_command_name(self) -> str:
        """
        Extract the command name from the command result.
        
        Returns:
            Command name in snake_case format (e.g., 'hello_world')
        """
        if isinstance(self.command_info, dict):
            command_data = self.command_info.get('data', {})
            return command_data.get('command_name', 'unknown')
        return 'unknown'
    
    def get_command_class(self):
        """
        Get the command class for instantiation.
        
        Returns:
            Command class object
        """
        if isinstance(self.command_info, dict):
            command_data = self.command_info.get('data', {})
            return command_data.get('command_class')
        return None
    
    def get_command_instance(self):
        """
        Get the command instance if available.
        
        Returns:
            Command instance or None
        """
        if isinstance(self.command_info, dict):
            command_data = self.command_info.get('data', {})
            return command_data.get('command_instance')
        return None
    
    def get_command_type(self) -> str:
        """
        Get the command type (command_class or legacy).
        
        Returns:
            Command type string
        """
        if isinstance(self.command_info, dict):
            command_data = self.command_info.get('data', {})
            return command_data.get('type', 'unknown')
        return 'unknown'
    
    def get_description(self) -> str:
        """
        Get the command description.
        
        Returns:
            Command description string
        """
        if isinstance(self.command_info, dict):
            command_data = self.command_info.get('data', {})
            return command_data.get('description', 'No description available')
        return 'No description available'
    
    def is_valid_command(self) -> bool:
        """
        Check if the command import was successful.
        
        Returns:
            True if command is valid, False otherwise
        """
        if isinstance(self.command_info, dict):
            return self.command_info.get('is_valid', False)
        return False
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """
        Override model_dump for custom serialization.
        
        Returns format compatible with command execution.
        """
        return {
            'command': self.get_command_name(),
            'args': self.command_args,
            'data': self.command_data,
        }
    
    def model_dump_json(self, **kwargs) -> str:
        """
        Override model_dump_json for custom JSON serialization.
        
        Uses custom model_dump() to avoid serialization issues
        with non-serializable objects (modules, classes).
        """
        data = self.model_dump(**kwargs)
        return json.dumps(data)
    
    # Model configuration
    model_config = {
        'extra': 'forbid',  # Don't allow extra fields
        'str_strip_whitespace': True,  # Strip whitespace from strings
        'validate_assignment': True,  # Validate on assignment
    }