#!/usr/bin/env python3
"""
Pydantic model for network_tools command validation
"""

import re
import sys
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from models.base_model import BaseCommandModel


class NetworkToolsModel(BaseCommandModel):
    """
    Validation model for network_tools command.
    
    Validates network diagnostic operations.
    """
    
    tool: str = Field(
        default="interactive",
        description="Network tool to use: interactive, ping, port, dns, interfaces"
    )
    
    host: Optional[str] = Field(
        default=None,
        description="Hostname or IP address for network operations"
    )
    
    port: Optional[int] = Field(
        default=None,
        description="Port number for port checking (1-65535)"
    )
    
    timeout: Optional[int] = Field(
        default=5,
        description="Timeout in seconds for network operations"
    )
    
    count: Optional[int] = Field(
        default=1,
        description="Number of ping attempts"
    )
    
    @field_validator('tool')
    @classmethod
    def validate_tool(cls, v: str, info: ValidationInfo) -> str:
        """Validate network tool"""
        if not isinstance(v, str):
            raise ValueError("Tool must be a string")
        
        v = v.strip().lower()
        valid_tools = ["interactive", "ping", "port", "dns", "interfaces"]
        
        if v not in valid_tools:
            raise ValueError(f"Invalid tool '{v}'. Must be one of: {valid_tools}")
        
        return v
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate hostname or IP address"""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Host must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        # Basic validation for hostname/IP
        # Allow letters, numbers, dots, hyphens
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError("Host contains invalid characters")
        
        # Basic IP address format check
        if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', v):
            # Validate IP address ranges
            parts = v.split('.')
            for part in parts:
                if not (0 <= int(part) <= 255):
                    raise ValueError("Invalid IP address format")
        
        return v
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate port number"""
        if v is None:
            return None
        
        if not isinstance(v, int):
            raise ValueError("Port must be an integer")
        
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Validate timeout parameter"""
        if v is None:
            return 5
        
        if not isinstance(v, int):
            raise ValueError("Timeout must be an integer")
        
        if not (1 <= v <= 60):
            raise ValueError("Timeout must be between 1 and 60 seconds")
        
        return v
    
    @field_validator('count')
    @classmethod
    def validate_count(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Validate count parameter"""
        if v is None:
            return 1
        
        if not isinstance(v, int):
            raise ValueError("Count must be an integer")
        
        if not (1 <= v <= 10):
            raise ValueError("Count must be between 1 and 10")
        
        return v
    
    def is_interactive_mode(self) -> bool:
        """Check if in interactive mode"""
        return self.tool == "interactive"
    
    def is_ping_mode(self) -> bool:
        """Check if in ping mode"""
        return self.tool == "ping"
    
    def is_port_mode(self) -> bool:
        """Check if in port checking mode"""
        return self.tool == "port"
    
    def is_dns_mode(self) -> bool:
        """Check if in DNS lookup mode"""
        return self.tool == "dns"
    
    def is_interfaces_mode(self) -> bool:
        """Check if in network interfaces mode"""
        return self.tool == "interfaces"
    
    def requires_host(self) -> bool:
        """Check if host is required for the current tool"""
        return self.tool in ["ping", "port", "dns"]
    
    def requires_port(self) -> bool:
        """Check if port is required for the current tool"""
        return self.tool == "port"