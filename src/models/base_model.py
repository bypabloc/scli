#!/usr/bin/env python3
"""
Base Pydantic model for SCLI commands

Provides common validation patterns and utilities for command models.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))


class BaseCommandModel(BaseModel):
    """
    Base Pydantic model for all SCLI command validations.
    
    Provides common validation patterns and utilities that can be
    extended by specific command models.
    """
    
    # Common fields that many commands might use
    verbose: Optional[bool] = Field(
        default=False,
        description="Enable verbose output"
    )
    
    dry_run: Optional[bool] = Field(
        default=False,
        description="Perform a dry run without making changes"
    )
    
    output_format: Optional[str] = Field(
        default="console",
        description="Output format for results"
    )
    
    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v: str, info: ValidationInfo) -> str:
        """Validate output format is supported"""
        if v is None:
            return "console"
        
        valid_formats = ["console", "json", "yaml", "table", "csv"]
        if v not in valid_formats:
            raise ValueError(f"Invalid output format '{v}'. Must be one of: {valid_formats}")
        
        return v
    
    @classmethod
    def from_args(cls, args: List[str], **defaults) -> 'BaseCommandModel':
        """
        Create model instance from command line arguments.
        
        Args:
            args: List of command line arguments
            **defaults: Default values to use
            
        Returns:
            Model instance with validated data
        """
        data = defaults.copy()
        
        # Simple argument parsing for common flags
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg in ['--verbose', '-v']:
                data['verbose'] = True
            elif arg in ['--dry-run', '--dry']:
                data['dry_run'] = True
            elif arg in ['--quiet', '-q']:
                data['verbose'] = False
            elif arg == '--output-format' and i + 1 < len(args):
                data['output_format'] = args[i + 1]
                i += 1
            elif arg.startswith('--output-format='):
                data['output_format'] = arg.split('=', 1)[1]
            
            i += 1
        
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseCommandModel':
        """
        Create model instance from dictionary.
        
        Args:
            data: Dictionary with command data
            
        Returns:
            Model instance with validated data
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        return self.model_dump(exclude_none=True)
    
    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled"""
        return self.verbose or False
    
    def is_dry_run(self) -> bool:
        """Check if dry run mode is enabled"""
        return self.dry_run or False
    
    def get_output_format(self) -> str:
        """Get the output format"""
        return self.output_format or "console"
    
    # Model configuration
    model_config = {
        'extra': 'forbid',  # Don't allow extra fields
        'str_strip_whitespace': True,  # Strip whitespace from strings
        'validate_assignment': True,  # Validate on assignment
        'use_enum_values': True,  # Use enum values instead of enum objects
    }