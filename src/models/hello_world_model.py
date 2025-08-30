#!/usr/bin/env python3
"""
Pydantic validation model for Hello World Command

This model defines the validation schema for the hello_world command arguments.
"""

import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ValidationInfo

# Add the parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from models.base_model import BaseCommandModel


class HelloWorldModel(BaseCommandModel):
    """
    Validation model for Hello World command arguments.
    
    This model validates the specific arguments that the hello_world command accepts.
    """
    
    # Specific fields for hello_world command
    name: Optional[str] = Field(
        default="World",
        description="Name to greet in the hello message"
    )
    
    language: Optional[str] = Field(
        default="english",
        description="Language for the greeting"
    )
    
    emoji: Optional[bool] = Field(
        default=True,
        description="Include emoji in the greeting"
    )
    
    uppercase: Optional[bool] = Field(
        default=False,
        description="Display greeting in uppercase"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str, info: ValidationInfo) -> str:
        """Validate that language is supported"""
        if v is None:
            return "english"
        
        valid_languages = ["english", "spanish", "french", "german", "italian"]
        if v.lower() not in valid_languages:
            raise ValueError(f"Invalid language '{v}'. Supported: {valid_languages}")
        
        return v.lower()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str, info: ValidationInfo) -> str:
        """Validate the name field"""
        if v is None or v.strip() == "":
            return "World"
        
        if len(v.strip()) > 50:
            raise ValueError("Name must be 50 characters or less")
        
        return v.strip()
    
    def get_greeting_message(self) -> str:
        """
        Generate the greeting message based on validated parameters.
        
        Returns:
            Formatted greeting message
        """
        name = self.name or "World"
        
        # Language-specific greetings
        greetings = {
            "english": f"Hello, {name}!",
            "spanish": f"¡Hola, {name}!",
            "french": f"Bonjour, {name}!",
            "german": f"Hallo, {name}!",
            "italian": f"Ciao, {name}!"
        }
        
        message = greetings.get(self.language, f"Hello, {name}!")
        
        # Add emoji if requested
        if self.emoji:
            emoji_map = {
                "english": "🌍",
                "spanish": "🌎",
                "french": "🇫🇷",
                "german": "🇩🇪",
                "italian": "🇮🇹"
            }
            message += f" {emoji_map.get(self.language, '🌍')}"
        
        # Apply uppercase if requested
        if self.uppercase:
            message = message.upper()
        
        return message
    
    @classmethod
    def from_args(cls, args: list, **defaults) -> 'HelloWorldModel':
        """
        Create model instance from command line arguments.
        
        Enhanced version that handles hello_world specific arguments.
        
        Args:
            args: List of command line arguments
            **defaults: Default values to use
            
        Returns:
            Model instance with validated data
        """
        data = defaults.copy()
        
        # Call parent method for common arguments
        base_model = super().from_args(args, **defaults)
        data.update(base_model.to_dict())
        
        # Parse hello_world specific arguments
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg == '--name' and i + 1 < len(args):
                data['name'] = args[i + 1]
                i += 1
            elif arg.startswith('--name='):
                data['name'] = arg.split('=', 1)[1]
            elif arg == '--language' and i + 1 < len(args):
                data['language'] = args[i + 1]
                i += 1
            elif arg.startswith('--language='):
                data['language'] = arg.split('=', 1)[1]
            elif arg in ['--emoji', '--with-emoji']:
                data['emoji'] = True
            elif arg in ['--no-emoji', '--without-emoji']:
                data['emoji'] = False
            elif arg in ['--uppercase', '--upper']:
                data['uppercase'] = True
            elif arg in ['--lowercase', '--lower']:
                data['uppercase'] = False
            
            # Handle positional argument as name
            elif not arg.startswith('-') and i == 0:
                data['name'] = arg
            
            i += 1
        
        return cls(**data)