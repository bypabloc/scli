#!/usr/bin/env python3
"""
Pydantic model for consumer_debt_checker command validation
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


class ConsumerDebtCheckerModel(BaseCommandModel):
    """
    Validation model for consumer_debt_checker command.
    
    Validates consumer debt checker operations with various modes.
    """
    
    mode: str = Field(
        default="interactive",
        description="Operation mode: interactive, csv, single, test"
    )
    
    csv_file: Optional[str] = Field(
        default=None,
        description="Path to the CSV file with credit numbers (for csv mode)"
    )
    
    credit_number: Optional[str] = Field(
        default=None,
        description="Single credit number to query (for single mode)"
    )
    
    delay: Optional[float] = Field(
        default=1.0,
        description="Delay between API requests in seconds"
    )
    
    max_records: Optional[int] = Field(
        default=None,
        description="Maximum number of records to process from CSV"
    )
    
    output_format: Optional[str] = Field(
        default="csv",
        description="Output format: csv, json"
    )
    
    test_auth: Optional[bool] = Field(
        default=False,
        description="Test API authentication only"
    )
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str, info: ValidationInfo) -> str:
        """Validate operation mode"""
        if not isinstance(v, str):
            raise ValueError("Mode must be a string")
        
        v = v.strip().lower()
        valid_modes = ["interactive", "csv", "single", "test"]
        
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
    
    @field_validator('credit_number')
    @classmethod
    def validate_credit_number(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate credit number format"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Credit number must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        if not v.isdigit():
            raise ValueError("Credit number must contain only digits")
        
        if len(v) < 10:
            raise ValueError("Credit number must be at least 10 digits")
        
        if len(v) > 20:
            raise ValueError("Credit number cannot be more than 20 digits")
        
        return v
    
    @field_validator('delay')
    @classmethod
    def validate_delay(cls, v: Optional[float], info: ValidationInfo) -> float:
        """Validate delay parameter"""
        if v is None:
            return 1.0
        
        if not isinstance(v, (int, float)):
            raise ValueError("Delay must be a number")
        
        if v < 0.1:
            raise ValueError("Delay must be at least 0.1 seconds")
        
        if v > 30:
            raise ValueError("Delay cannot be more than 30 seconds")
        
        return float(v)
    
    @field_validator('max_records')
    @classmethod
    def validate_max_records(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate max records parameter"""
        if v is None:
            return None
        
        if not isinstance(v, int):
            raise ValueError("Max records must be an integer")
        
        if v < 1:
            raise ValueError("Max records must be at least 1")
        
        if v > 10000:
            raise ValueError("Max records cannot be more than 10,000")
        
        return v
    
    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Validate output format"""
        if v is None:
            return "csv"
        
        if not isinstance(v, str):
            raise ValueError("Output format must be a string")
        
        v = v.strip().lower()
        valid_formats = ["csv", "json"]
        
        if v not in valid_formats:
            raise ValueError(f"Invalid output format '{v}'. Must be one of: {valid_formats}")
        
        return v
    
    def get_csv_path(self) -> Optional[Path]:
        """Get CSV file path as Path object"""
        if self.csv_file:
            return Path(self.csv_file)
        return None
    
    def is_interactive_mode(self) -> bool:
        """Check if in interactive mode"""
        return self.mode == "interactive"
    
    def is_csv_mode(self) -> bool:
        """Check if in CSV processing mode"""
        return self.mode == "csv"
    
    def is_single_mode(self) -> bool:
        """Check if in single credit mode"""
        return self.mode == "single"
    
    def is_test_mode(self) -> bool:
        """Check if in test mode"""
        return self.mode == "test"
    
    def requires_csv_file(self) -> bool:
        """Check if CSV file is required for the current mode"""
        return self.mode == "csv"
    
    def requires_credit_number(self) -> bool:
        """Check if credit number is required for the current mode"""
        return self.mode == "single"