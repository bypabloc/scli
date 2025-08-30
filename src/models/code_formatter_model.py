#!/usr/bin/env python3
"""
Pydantic model for code_formatter command validation
"""

import sys
from pathlib import Path
from typing import Optional, List

from pydantic import Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from models.base_model import BaseCommandModel


class CodeFormatterModel(BaseCommandModel):
    """
    Validation model for code_formatter command.
    
    Validates code formatting operations.
    """
    
    mode: str = Field(
        default="all",
        description="File selection mode: all, staged, unstaged, modified, tracked"
    )
    
    verbose: Optional[bool] = Field(
        default=False,
        description="Enable verbose output showing details for each action"
    )
    
    confirm: Optional[bool] = Field(
        default=False,
        description="Automatically confirm file modifications without prompting"
    )
    
    config_file: Optional[str] = Field(
        default=None,
        description="Path to configuration file (default: .scli-quality.yml)"
    )
    
    project_root: Optional[str] = Field(
        default=None,
        description="Project root directory to format (default: current directory)"
    )
    
    only_actions: Optional[List[str]] = Field(
        default=None,
        description="Only run these specific actions (comma-separated list)"
    )
    
    enabled_actions: Optional[List[str]] = Field(
        default_factory=list,
        description="List of actions to enable (overrides config)"
    )
    
    disabled_actions: Optional[List[str]] = Field(
        default_factory=list,
        description="List of actions to disable (overrides config)"
    )
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str, info: ValidationInfo) -> str:
        """Validate file selection mode"""
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
    
    @field_validator('only_actions')
    @classmethod
    def validate_only_actions(cls, v: Optional[List[str]], info: ValidationInfo) -> Optional[List[str]]:
        """Validate only_actions parameter"""
        if v is None:
            return None
        
        if isinstance(v, str):
            # Handle comma-separated string
            v = [action.strip() for action in v.split(',') if action.strip()]
        
        if not isinstance(v, list):
            raise ValueError("Only actions must be a list or comma-separated string")
        
        # Validate that all actions are strings
        for action in v:
            if not isinstance(action, str):
                raise ValueError("All actions must be strings")
        
        return v
    
    @field_validator('enabled_actions')
    @classmethod
    def validate_enabled_actions(cls, v: Optional[List[str]], info: ValidationInfo) -> List[str]:
        """Validate enabled_actions parameter"""
        if v is None:
            return []
        
        if isinstance(v, str):
            # Handle comma-separated string
            v = [action.strip() for action in v.split(',') if action.strip()]
        
        if not isinstance(v, list):
            raise ValueError("Enabled actions must be a list or comma-separated string")
        
        # Validate that all actions are strings
        for action in v:
            if not isinstance(action, str):
                raise ValueError("All actions must be strings")
        
        return v
    
    @field_validator('disabled_actions')
    @classmethod
    def validate_disabled_actions(cls, v: Optional[List[str]], info: ValidationInfo) -> List[str]:
        """Validate disabled_actions parameter"""
        if v is None:
            return []
        
        if isinstance(v, str):
            # Handle comma-separated string
            v = [action.strip() for action in v.split(',') if action.strip()]
        
        if not isinstance(v, list):
            raise ValueError("Disabled actions must be a list or comma-separated string")
        
        # Validate that all actions are strings
        for action in v:
            if not isinstance(action, str):
                raise ValueError("All actions must be strings")
        
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
        """Check if formatting all files"""
        return self.mode == "all"
    
    def is_staged_mode(self) -> bool:
        """Check if formatting staged files only"""
        return self.mode == "staged"
    
    def is_unstaged_mode(self) -> bool:
        """Check if formatting unstaged files only"""
        return self.mode == "unstaged"
    
    def is_modified_mode(self) -> bool:
        """Check if formatting all modified files"""
        return self.mode == "modified"
    
    def is_tracked_mode(self) -> bool:
        """Check if formatting all tracked files"""
        return self.mode == "tracked"
    
    def requires_git(self) -> bool:
        """Check if the current mode requires git"""
        return self.mode in ["staged", "unstaged", "modified", "tracked"]
    
    def has_only_actions(self) -> bool:
        """Check if only specific actions should be run"""
        return self.only_actions is not None and len(self.only_actions) > 0
    
    def get_final_actions(self, default_actions: List[str]) -> List[str]:
        """Get final list of actions considering only, enabled, and disabled filters"""
        # Start with only_actions if specified, otherwise use default
        if self.has_only_actions():
            actions = list(self.only_actions)
        else:
            actions = list(default_actions)
        
        # Add enabled actions
        for action in self.enabled_actions:
            if action not in actions:
                actions.append(action)
        
        # Remove disabled actions
        actions = [action for action in actions if action not in self.disabled_actions]
        
        return actions