#!/usr/bin/env python3
"""
Pydantic model for cobol_processor command validation
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


class CobolProcessorModel(BaseCommandModel):
    """
    Validation model for cobol_processor command.
    
    Validates COBOL file processing operations.
    """
    
    mode: str = Field(
        default="interactive",
        description="Processing mode: interactive, process, browse"
    )
    
    cpy_file: Optional[str] = Field(
        default=None,
        description="Path to the COBOL copybook file (.cpy)"
    )
    
    txt_file: Optional[str] = Field(
        default=None,
        description="Path to the data file (.txt)"
    )
    
    directory: Optional[str] = Field(
        default=None,
        description="Directory to scan for COBOL files"
    )
    
    output_format: Optional[str] = Field(
        default="csv",
        description="Output format: csv"
    )
    
    csv_separator: Optional[str] = Field(
        default=";",
        description="CSV separator character (default: ;)"
    )
    
    output_file: Optional[str] = Field(
        default=None,
        description="Custom output file name"
    )
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str, info: ValidationInfo) -> str:
        """Validate processing mode"""
        if not isinstance(v, str):
            raise ValueError("Mode must be a string")
        
        v = v.strip().lower()
        valid_modes = ["interactive", "process", "browse"]
        
        if v not in valid_modes:
            raise ValueError(f"Invalid mode '{v}'. Must be one of: {valid_modes}")
        
        return v
    
    @field_validator('cpy_file')
    @classmethod
    def validate_cpy_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate COBOL copybook file exists and is readable"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("CPY file path must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        file_path = Path(v).expanduser()
        
        if not file_path.exists():
            raise ValueError(f"CPY file does not exist: {v}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        
        if not file_path.suffix.lower() == '.cpy':
            raise ValueError(f"File must be a COBOL copybook file (*.cpy): {v}")
        
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"No read permission for file: {v}")
        
        return str(file_path.absolute())
    
    @field_validator('txt_file')
    @classmethod
    def validate_txt_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate data file exists and is readable"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("TXT file path must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        file_path = Path(v).expanduser()
        
        if not file_path.exists():
            raise ValueError(f"TXT file does not exist: {v}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        
        if not file_path.suffix.lower() == '.txt':
            raise ValueError(f"File must be a text file (*.txt): {v}")
        
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"No read permission for file: {v}")
        
        return str(file_path.absolute())
    
    @field_validator('directory')
    @classmethod
    def validate_directory(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate directory exists and is readable"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Directory path must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        dir_path = Path(v).expanduser()
        
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {v}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        
        if not os.access(dir_path, os.R_OK):
            raise ValueError(f"No read permission for directory: {v}")
        
        return str(dir_path.absolute())
    
    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Validate output format"""
        if v is None:
            return "csv"
        
        if not isinstance(v, str):
            raise ValueError("Output format must be a string")
        
        v = v.strip().lower()
        valid_formats = ["csv"]
        
        if v not in valid_formats:
            raise ValueError(f"Invalid output format '{v}'. Must be one of: {valid_formats}")
        
        return v
    
    @field_validator('csv_separator')
    @classmethod
    def validate_csv_separator(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Validate CSV separator"""
        if v is None:
            return ";"
        
        if not isinstance(v, str):
            raise ValueError("CSV separator must be a string")
        
        if len(v) != 1:
            raise ValueError("CSV separator must be a single character")
        
        return v
    
    @field_validator('output_file')
    @classmethod
    def validate_output_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate output file name"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Output file name must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        # Basic validation for file name
        if any(char in v for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            raise ValueError("Output file name contains invalid characters")
        
        return v
    
    def get_cpy_path(self) -> Optional[Path]:
        """Get CPY file path as Path object"""
        if self.cpy_file:
            return Path(self.cpy_file)
        return None
    
    def get_txt_path(self) -> Optional[Path]:
        """Get TXT file path as Path object"""
        if self.txt_file:
            return Path(self.txt_file)
        return None
    
    def get_directory_path(self) -> Optional[Path]:
        """Get directory path as Path object"""
        if self.directory:
            return Path(self.directory)
        return None
    
    def is_interactive_mode(self) -> bool:
        """Check if in interactive mode"""
        return self.mode == "interactive"
    
    def is_process_mode(self) -> bool:
        """Check if in direct processing mode"""
        return self.mode == "process"
    
    def is_browse_mode(self) -> bool:
        """Check if in directory browse mode"""
        return self.mode == "browse"
    
    def requires_both_files(self) -> bool:
        """Check if both CPY and TXT files are required"""
        return self.mode == "process"
    
    def requires_directory(self) -> bool:
        """Check if directory is required"""
        return self.mode == "browse"