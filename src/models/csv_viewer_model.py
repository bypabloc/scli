#!/usr/bin/env python3
"""
Pydantic model for csv_viewer command validation
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

from pydantic import Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from models.base_model import BaseCommandModel


class CsvViewerModel(BaseCommandModel):
    """
    Validation model for csv_viewer command.
    
    Validates CSV viewer operations.
    """
    
    mode: str = Field(
        default="interactive",
        description="Viewer mode: interactive, view"
    )
    
    csv_file: Optional[str] = Field(
        default=None,
        description="Path to the CSV file to view"
    )
    
    separator: Optional[str] = Field(
        default=None,
        description="CSV separator character (auto-detect if not specified)"
    )
    
    page_size: Optional[int] = Field(
        default=1000,
        description="Number of rows per page (default: 1000)"
    )
    
    visible_columns: Optional[List[str]] = Field(
        default=None,
        description="List of columns to show initially (show all if not specified)"
    )
    
    encoding: Optional[str] = Field(
        default=None,
        description="File encoding (auto-detect if not specified)"
    )
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str, info: ValidationInfo) -> str:
        """Validate viewer mode"""
        if not isinstance(v, str):
            raise ValueError("Mode must be a string")
        
        v = v.strip().lower()
        valid_modes = ["interactive", "view"]
        
        if v not in valid_modes:
            raise ValueError(f"Invalid mode '{v}'. Must be one of: {valid_modes}")
        
        return v
    
    @field_validator('csv_file')
    @classmethod
    def validate_csv_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate CSV file exists and is readable"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("CSV file path must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        file_path = Path(v).expanduser()
        
        if not file_path.exists():
            raise ValueError(f"CSV file does not exist: {v}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        
        if not file_path.suffix.lower() == '.csv':
            raise ValueError(f"File must be a CSV file (*.csv): {v}")
        
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"No read permission for file: {v}")
        
        return str(file_path.absolute())
    
    @field_validator('separator')
    @classmethod
    def validate_separator(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate CSV separator"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Separator must be a string")
        
        if len(v) != 1:
            raise ValueError("Separator must be a single character")
        
        return v
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Validate page size parameter"""
        if v is None:
            return 1000
        
        if not isinstance(v, int):
            raise ValueError("Page size must be an integer")
        
        if not (1 <= v <= 10000):
            raise ValueError("Page size must be between 1 and 10,000")
        
        return v
    
    @field_validator('visible_columns')
    @classmethod
    def validate_visible_columns(cls, v: Optional[List[str]], info: ValidationInfo) -> Optional[List[str]]:
        """Validate visible columns parameter"""
        if v is None:
            return None
        
        if isinstance(v, str):
            # Handle comma-separated string
            v = [col.strip() for col in v.split(',') if col.strip()]
        
        if not isinstance(v, list):
            raise ValueError("Visible columns must be a list or comma-separated string")
        
        # Validate that all columns are strings
        for col in v:
            if not isinstance(col, str):
                raise ValueError("All column names must be strings")
        
        return v
    
    @field_validator('encoding')
    @classmethod
    def validate_encoding(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate encoding parameter"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Encoding must be a string")
        
        v = v.strip().lower()
        valid_encodings = ["utf-8", "latin-1", "cp1252", "ascii", "iso-8859-1"]
        
        if v not in valid_encodings:
            raise ValueError(f"Invalid encoding '{v}'. Must be one of: {valid_encodings}")
        
        return v
    
    def get_csv_path(self) -> Optional[Path]:
        """Get CSV file path as Path object"""
        if self.csv_file:
            return Path(self.csv_file)
        return None
    
    def is_interactive_mode(self) -> bool:
        """Check if in interactive mode"""
        return self.mode == "interactive"
    
    def is_view_mode(self) -> bool:
        """Check if in direct view mode"""
        return self.mode == "view"
    
    def requires_csv_file(self) -> bool:
        """Check if CSV file is required for current mode"""
        return self.mode == "view"
    
    def has_visible_columns(self) -> bool:
        """Check if specific visible columns are specified"""
        return self.visible_columns is not None and len(self.visible_columns) > 0
    
    def get_separator_or_detect(self, default: str = ",") -> str:
        """Get separator or return default for auto-detection"""
        return self.separator if self.separator else default
    
    def get_encoding_or_detect(self, default: str = "utf-8") -> str:
        """Get encoding or return default for auto-detection"""
        return self.encoding if self.encoding else default