#!/usr/bin/env python3
"""
Pydantic model for pdf_converter command validation
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


class PdfConverterModel(BaseCommandModel):
    """
    Validation model for pdf_converter command.
    
    Validates PDF conversion operations.
    """
    
    mode: str = Field(
        default="interactive",
        description="Conversion mode: interactive, convert"
    )
    
    pdf_file: Optional[str] = Field(
        default=None,
        description="Path to the PDF file to convert"
    )
    
    output_format: Optional[str] = Field(
        default=None,
        description="Output format: txt, png, jpg"
    )
    
    output_path: Optional[str] = Field(
        default=None,
        description="Custom output path (optional)"
    )
    
    dpi: Optional[int] = Field(
        default=200,
        description="DPI for image conversion (default: 200)"
    )
    
    quality: Optional[int] = Field(
        default=85,
        description="JPEG quality (1-100, default: 85)"
    )
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str, info: ValidationInfo) -> str:
        """Validate conversion mode"""
        if not isinstance(v, str):
            raise ValueError("Mode must be a string")
        
        v = v.strip().lower()
        valid_modes = ["interactive", "convert"]
        
        if v not in valid_modes:
            raise ValueError(f"Invalid mode '{v}'. Must be one of: {valid_modes}")
        
        return v
    
    @field_validator('pdf_file')
    @classmethod
    def validate_pdf_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate PDF file exists and is readable"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("PDF file path must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        file_path = Path(v).expanduser()
        
        if not file_path.exists():
            raise ValueError(f"PDF file does not exist: {v}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF file (*.pdf): {v}")
        
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"No read permission for file: {v}")
        
        return str(file_path.absolute())
    
    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate output format"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Output format must be a string")
        
        v = v.strip().lower()
        valid_formats = ["txt", "png", "jpg", "jpeg"]
        
        if v not in valid_formats:
            raise ValueError(f"Invalid output format '{v}'. Must be one of: {valid_formats}")
        
        # Normalize jpeg to jpg
        if v == "jpeg":
            v = "jpg"
        
        return v
    
    @field_validator('output_path')
    @classmethod
    def validate_output_path(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate output path"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Output path must be a string")
        
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
    
    @field_validator('dpi')
    @classmethod
    def validate_dpi(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Validate DPI parameter"""
        if v is None:
            return 200
        
        if not isinstance(v, int):
            raise ValueError("DPI must be an integer")
        
        if not (50 <= v <= 600):
            raise ValueError("DPI must be between 50 and 600")
        
        return v
    
    @field_validator('quality')
    @classmethod
    def validate_quality(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Validate JPEG quality parameter"""
        if v is None:
            return 85
        
        if not isinstance(v, int):
            raise ValueError("Quality must be an integer")
        
        if not (1 <= v <= 100):
            raise ValueError("Quality must be between 1 and 100")
        
        return v
    
    def get_pdf_path(self) -> Optional[Path]:
        """Get PDF file path as Path object"""
        if self.pdf_file:
            return Path(self.pdf_file)
        return None
    
    def get_output_path_obj(self) -> Optional[Path]:
        """Get output path as Path object"""
        if self.output_path:
            return Path(self.output_path)
        return None
    
    def is_interactive_mode(self) -> bool:
        """Check if in interactive mode"""
        return self.mode == "interactive"
    
    def is_convert_mode(self) -> bool:
        """Check if in direct conversion mode"""
        return self.mode == "convert"
    
    def is_text_format(self) -> bool:
        """Check if output format is text"""
        return self.output_format == "txt"
    
    def is_image_format(self) -> bool:
        """Check if output format is image"""
        return self.output_format in ["png", "jpg"]
    
    def requires_pdf_file(self) -> bool:
        """Check if PDF file is required for current mode"""
        return self.mode == "convert"
    
    def requires_output_format(self) -> bool:
        """Check if output format is required for current mode"""
        return self.mode == "convert"