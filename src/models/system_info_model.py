#!/usr/bin/env python3
"""
Pydantic model for system_info command validation
"""

import sys
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from models.base_model import BaseCommandModel


class SystemInfoModel(BaseCommandModel):
    """
    Validation model for system_info command.
    
    Validates system information gathering options and output settings.
    """
    
    categories: Optional[str] = Field(
        default="all",
        description="Comma-separated list of info categories to display (system,python,time,directories,user,environment)"
    )
    
    include_sensitive: Optional[bool] = Field(
        default=False,
        description="Include potentially sensitive information (full paths, environment variables)"
    )
    
    export_file: Optional[str] = Field(
        default=None,
        description="Export system info to a file"
    )
    
    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Validate system info categories"""
        if v is None:
            return "all"
        
        if not isinstance(v, str):
            raise ValueError("Categories must be a string")
        
        v = v.strip().lower()
        if not v:
            return "all"
        
        valid_categories = {
            "all", "system", "python", "time", "directories", 
            "user", "environment", "network", "hardware"
        }
        
        if v == "all":
            return v
        
        # Parse comma-separated categories
        categories = []
        for category in v.split(','):
            category = category.strip()
            if category:
                if category not in valid_categories:
                    raise ValueError(
                        f"Invalid category '{category}'. "
                        f"Valid categories: {', '.join(sorted(valid_categories))}"
                    )
                categories.append(category)
        
        if not categories:
            return "all"
        
        return ','.join(categories)
    
    @field_validator('export_file')
    @classmethod 
    def validate_export_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate export file path"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Export file must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        export_path = Path(v).expanduser()
        
        # Check if parent directory exists
        parent_dir = export_path.parent
        if not parent_dir.exists():
            raise ValueError(f"Parent directory does not exist: {parent_dir}")
        
        if not parent_dir.is_dir():
            raise ValueError(f"Parent path is not a directory: {parent_dir}")
        
        # Check write permissions on parent directory
        import os
        if not os.access(parent_dir, os.W_OK):
            raise ValueError(f"No write permission for directory: {parent_dir}")
        
        return str(export_path.absolute())
    
    def get_categories_list(self) -> List[str]:
        """Get categories as a list"""
        if self.categories == "all":
            return ["system", "python", "time", "directories", "user", "environment"]
        
        return [cat.strip() for cat in self.categories.split(',') if cat.strip()]
    
    def should_include_category(self, category: str) -> bool:
        """Check if a category should be included"""
        categories = self.get_categories_list()
        return category.lower() in categories
    
    def get_export_path(self) -> Optional[Path]:
        """Get export file path as Path object"""
        if self.export_file:
            return Path(self.export_file)
        return None
    
    def is_sensitive_mode(self) -> bool:
        """Check if sensitive information should be included"""
        return self.include_sensitive or False