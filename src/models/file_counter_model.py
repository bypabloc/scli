#!/usr/bin/env python3
"""
Pydantic model for file_counter command validation
"""

import os
import sys
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from models.base_model import BaseCommandModel


class FileCounterModel(BaseCommandModel):
    """
    Validation model for file_counter command.
    
    Validates directory path, recursion settings, and output options.
    """
    
    directory: Optional[str] = Field(
        default=None,
        description="Directory to analyze (defaults to current directory)"
    )
    
    recursive: Optional[bool] = Field(
        default=True,
        description="Include subdirectories in analysis"
    )
    
    show_hidden: Optional[bool] = Field(
        default=False,
        description="Include hidden files and directories"
    )
    
    min_size: Optional[int] = Field(
        default=None,
        description="Minimum file size in bytes"
    )
    
    max_size: Optional[int] = Field(
        default=None,
        description="Maximum file size in bytes"
    )
    
    extensions: Optional[str] = Field(
        default=None,
        description="Comma-separated list of file extensions to include (e.g., 'py,js,txt')"
    )
    
    exclude_extensions: Optional[str] = Field(
        default=None,
        description="Comma-separated list of file extensions to exclude"
    )
    
    @field_validator('directory')
    @classmethod
    def validate_directory(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate directory path exists and is accessible"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Directory must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        directory_path = Path(v).expanduser()
        
        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {v}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        
        if not os.access(directory_path, os.R_OK):
            raise ValueError(f"No read permission for directory: {v}")
        
        return str(directory_path.absolute())
    
    @field_validator('min_size', 'max_size')
    @classmethod
    def validate_size(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate file size limits"""
        if v is None:
            return None
        
        if not isinstance(v, int):
            raise ValueError("Size must be an integer")
        
        if v < 0:
            raise ValueError("Size cannot be negative")
        
        return v
    
    @field_validator('extensions', 'exclude_extensions')
    @classmethod
    def validate_extensions(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate file extensions format"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Extensions must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        # Clean up extensions (remove dots, spaces, etc.)
        extensions = []
        for ext in v.split(','):
            ext = ext.strip().lower()
            if ext:
                # Remove leading dot if present
                if ext.startswith('.'):
                    ext = ext[1:]
                extensions.append(ext)
        
        if not extensions:
            return None
        
        return ','.join(extensions)
    
    def validate_size_range(self):
        """Validate that min_size <= max_size"""
        if self.min_size is not None and self.max_size is not None:
            if self.min_size > self.max_size:
                raise ValueError("min_size cannot be greater than max_size")
    
    def get_directory_path(self) -> Path:
        """Get the directory path as a Path object"""
        if self.directory:
            return Path(self.directory)
        return Path.cwd()
    
    def get_extensions_list(self) -> Optional[list]:
        """Get extensions as a list"""
        if self.extensions:
            return self.extensions.split(',')
        return None
    
    def get_exclude_extensions_list(self) -> Optional[list]:
        """Get excluded extensions as a list"""
        if self.exclude_extensions:
            return self.exclude_extensions.split(',')
        return None
    
    def should_include_file(self, file_path: Path) -> bool:
        """
        Check if a file should be included based on filters.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be included, False otherwise
        """
        # Check hidden files
        if not self.show_hidden and file_path.name.startswith('.'):
            return False
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            
            if self.min_size is not None and file_size < self.min_size:
                return False
            
            if self.max_size is not None and file_size > self.max_size:
                return False
        except (OSError, PermissionError):
            # If we can't get file stats, skip the file
            return False
        
        # Check extensions
        file_ext = file_path.suffix.lower()[1:]  # Remove the dot
        
        # If include extensions specified, file must match
        include_exts = self.get_extensions_list()
        if include_exts and file_ext not in include_exts:
            return False
        
        # If exclude extensions specified, file must not match
        exclude_exts = self.get_exclude_extensions_list()
        if exclude_exts and file_ext in exclude_exts:
            return False
        
        return True