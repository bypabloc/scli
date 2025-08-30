#!/usr/bin/env python3
"""
Pydantic model for code_quality_checker command validation
"""

import sys
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from models.base_model import BaseCommandModel


class CodeQualityCheckerModel(BaseCommandModel):
    """
    Validation model for code_quality_checker command.
    
    Validates code quality checking operations.
    """
    
    mode: str = Field(
        default="all",
        description="File evaluation mode: all, staged, unstaged, modified, tracked"
    )
    
    verbose: Optional[bool] = Field(
        default=False,
        description="Enable verbose output showing details for each file"
    )
    
    config_file: Optional[str] = Field(
        default=None,
        description="Path to configuration file (default: .scli-quality.yml)"
    )
    
    project_root: Optional[str] = Field(
        default=None,
        description="Project root directory to check (default: current directory)"
    )
    
    max_errors: Optional[int] = Field(
        default=None,
        description="Maximum allowed errors before failing"
    )
    
    respect_gitignore: Optional[bool] = Field(
        default=True,
        description="Whether to respect .gitignore files when scanning (default: True)"
    )
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str, info: ValidationInfo) -> str:
        """Validate file evaluation mode"""
        if not isinstance(v, str):
            raise ValueError("Mode must be a string")
        
        v = v.strip().lower()
        valid_modes = ["all", "staged", "unstaged", "modified", "tracked"]
        
        if v not in valid_modes:
            raise ValueError(f"Invalid mode '{v}'. Must be one of: {valid_modes}")
        
        return v
    
    @field_validator('config_file')
    @classmethod
    def validate_config_file(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate configuration file path"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Config file path must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        config_path = Path(v).expanduser()
        
        # File doesn't need to exist (will use defaults), but if it exists, it should be readable
        if config_path.exists():
            if not config_path.is_file():
                raise ValueError(f"Config path is not a file: {v}")
            
            if not config_path.suffix.lower() in ['.yml', '.yaml']:
                raise ValueError(f"Config file must be YAML (*.yml or *.yaml): {v}")
        
        return str(config_path.absolute())
    
    @field_validator('project_root')
    @classmethod
    def validate_project_root(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate project root directory"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Project root must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        root_path = Path(v).expanduser()
        
        if not root_path.exists():
            raise ValueError(f"Project root directory does not exist: {v}")
        
        if not root_path.is_dir():
            raise ValueError(f"Project root is not a directory: {v}")
        
        return str(root_path.absolute())
    
    @field_validator('max_errors')
    @classmethod
    def validate_max_errors(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate max errors parameter"""
        if v is None:
            return None
        
        if not isinstance(v, int):
            raise ValueError("Max errors must be an integer")
        
        if v < 0:
            raise ValueError("Max errors cannot be negative")
        
        return v
    
    def get_config_path(self) -> Optional[Path]:
        """Get configuration file path as Path object"""
        if self.config_file:
            return Path(self.config_file)
        return None
    
    def get_project_root_path(self) -> Path:
        """Get project root path as Path object"""
        if self.project_root:
            return Path(self.project_root)
        return Path.cwd()
    
    def is_all_mode(self) -> bool:
        """Check if checking all files"""
        return self.mode == "all"
    
    def is_staged_mode(self) -> bool:
        """Check if checking staged files only"""
        return self.mode == "staged"
    
    def is_unstaged_mode(self) -> bool:
        """Check if checking unstaged files only"""
        return self.mode == "unstaged"
    
    def is_modified_mode(self) -> bool:
        """Check if checking all modified files"""
        return self.mode == "modified"
    
    def is_tracked_mode(self) -> bool:
        """Check if checking all tracked files"""
        return self.mode == "tracked"
    
    def requires_git(self) -> bool:
        """Check if the current mode requires git"""
        return self.mode in ["staged", "unstaged", "modified", "tracked"]
    
    def should_respect_gitignore(self) -> bool:
        """Check if .gitignore files should be respected"""
        return self.respect_gitignore if self.respect_gitignore is not None else True