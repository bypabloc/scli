#!/usr/bin/env python3
"""
Pydantic model for log_analyzer command validation
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


class LogAnalyzerModel(BaseCommandModel):
    """
    Validation model for log_analyzer command.
    
    Validates CSV file path and analysis options.
    """
    
    csv_file: str = Field(
        ...,
        description="Path to the CSV log file to analyze"
    )
    
    output_file: Optional[str] = Field(
        default=None,
        description="Output file for JSON results (optional)"
    )
    
    top_n: Optional[int] = Field(
        default=10,
        description="Number of top entries to show in each category"
    )
    
    analysis_type: Optional[str] = Field(
        default="all",
        description="Type of analysis to perform (all, daily, hourly, minute)"
    )
    
    @field_validator('csv_file')
    @classmethod
    def validate_csv_file(cls, v: str, info: ValidationInfo) -> str:
        """Validate CSV file exists and is readable"""
        if not isinstance(v, str):
            raise ValueError("CSV file path must be a string")
        
        v = v.strip()
        if not v:
            raise ValueError("CSV file path cannot be empty")
        
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
    
    @field_validator('output_file')
    @classmethod
    def validate_output_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate output file path"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Output file path must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        output_path = Path(v).expanduser()
        
        # Check if parent directory exists and is writable
        parent_dir = output_path.parent
        if not parent_dir.exists():
            raise ValueError(f"Parent directory does not exist: {parent_dir}")
        
        if not os.access(parent_dir, os.W_OK):
            raise ValueError(f"No write permission for directory: {parent_dir}")
        
        return str(output_path.absolute())
    
    @field_validator('top_n')
    @classmethod
    def validate_top_n(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Validate top_n parameter"""
        if v is None:
            return 10
        
        if not isinstance(v, int):
            raise ValueError("top_n must be an integer")
        
        if v < 1:
            raise ValueError("top_n must be at least 1")
        
        if v > 100:
            raise ValueError("top_n cannot be more than 100")
        
        return v
    
    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Validate analysis type"""
        if v is None:
            return "all"
        
        if not isinstance(v, str):
            raise ValueError("Analysis type must be a string")
        
        v = v.strip().lower()
        valid_types = ["all", "daily", "hourly", "minute", "summary"]
        
        if v not in valid_types:
            raise ValueError(f"Invalid analysis type '{v}'. Must be one of: {valid_types}")
        
        return v
    
    def get_csv_path(self) -> Path:
        """Get CSV file path as Path object"""
        return Path(self.csv_file)
    
    def get_output_path(self) -> Optional[Path]:
        """Get output file path as Path object"""
        if self.output_file:
            return Path(self.output_file)
        return None
    
    def should_analyze_daily(self) -> bool:
        """Check if daily analysis should be performed"""
        return self.analysis_type in ["all", "daily"]
    
    def should_analyze_hourly(self) -> bool:
        """Check if hourly analysis should be performed"""
        return self.analysis_type in ["all", "hourly"]
    
    def should_analyze_minute(self) -> bool:
        """Check if minute analysis should be performed"""
        return self.analysis_type in ["all", "minute"]