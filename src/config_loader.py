"""
Configuration loader for SCLI
Handles loading of YAML configuration files for scripts
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConfigLoader:
    """Configuration loader for SCLI scripts"""
    
    project_root: Path = field(init=False)
    global_config: Dict[str, Any] = field(default_factory=dict, init=False)
    script_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """Initialize the configuration loader"""
        # Find project root (directory containing pyproject.toml)
        current_dir = Path(__file__).parent
        while current_dir.parent != current_dir:
            if (current_dir / "pyproject.toml").exists():
                self.project_root = current_dir
                break
            current_dir = current_dir.parent
        else:
            # Fallback to current working directory
            self.project_root = Path.cwd()
        
        logger.info(f"Project root detected: {self.project_root}")
        self.load_global_config()
    
    def load_global_config(self) -> None:
        """Load global configuration from config.yml"""
        config_path = self.project_root / "config.yml"
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.global_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded global config from {config_path}")
                logger.debug(f"Global config keys: {list(self.global_config.keys())}")
            except Exception as e:
                logger.error(f"Error loading global config: {e}")
                self.global_config = {}
        else:
            logger.info(f"No global config file found at {config_path}")
            self.global_config = {}
    
    def load_script_config(self, script_name: str) -> Dict[str, Any]:
        """Load configuration for a specific script"""
        if script_name in self.script_configs:
            return self.script_configs[script_name]
        
        # Try script-specific config file
        script_config_path = self.project_root / f"config_{script_name}.yml"
        script_config = {}
        
        if script_config_path.exists():
            try:
                with open(script_config_path, 'r', encoding='utf-8') as f:
                    script_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded script config from {script_config_path}")
                logger.debug(f"Script config for {script_name}: {script_config}")
            except Exception as e:
                logger.error(f"Error loading script config for {script_name}: {e}")
                script_config = {}
        else:
            logger.info(f"No script config file found at {script_config_path}")
        
        # Merge with global config (script config takes precedence)
        merged_config = {}
        if script_name in self.global_config:
            merged_config.update(self.global_config[script_name])
        merged_config.update(script_config)
        
        # Cache the result
        self.script_configs[script_name] = merged_config
        logger.debug(f"Final merged config for {script_name}: {merged_config}")
        
        return merged_config
    
    def get_config(self, script_name: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value for a script"""
        script_config = self.load_script_config(script_name)
        
        if key is None:
            return script_config
        
        # Support nested keys using dot notation (e.g., 'api.base_url')
        keys = key.split('.')
        value = script_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                logger.debug(f"Config key '{key}' not found for {script_name}, using default: {default}")
                return default
        
        logger.debug(f"Config value for {script_name}.{key}: {value}")
        return value
    
    def has_config(self, script_name: str, key: str = None) -> bool:
        """Check if configuration exists for a script"""
        try:
            config = self.get_config(script_name, key)
            return config is not None
        except:
            return False
    
    def create_sample_config(self, script_name: str, sample_config: Dict[str, Any]) -> Path:
        """Create a sample configuration file for a script"""
        config_path = self.project_root / f"config_{script_name}.yml"
        
        if not config_path.exists():
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False, indent=2)
                logger.info(f"Created sample config at {config_path}")
                return config_path
            except Exception as e:
                logger.error(f"Error creating sample config: {e}")
                raise
        else:
            logger.info(f"Config file already exists at {config_path}")
            return config_path
    
    def get_project_root(self) -> Path:
        """Get the project root directory"""
        return self.project_root


# Global instance
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_script_config(script_name: str, key: str = None, default: Any = None) -> Any:
    """Convenience function to get script configuration"""
    return get_config_loader().get_config(script_name, key, default)


def has_script_config(script_name: str, key: str = None) -> bool:
    """Convenience function to check if script configuration exists"""
    return get_config_loader().has_config(script_name, key)


def create_sample_script_config(script_name: str, sample_config: Dict[str, Any]) -> Path:
    """Convenience function to create sample script configuration"""
    return get_config_loader().create_sample_config(script_name, sample_config)