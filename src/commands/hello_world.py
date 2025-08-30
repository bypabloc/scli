#!/usr/bin/env python3
"""
Hello World Command - Enhanced example of a SCLI command with Pydantic validation
"""

import sys
import os

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.hello_world_model import HelloWorldModel

DESCRIPTION = "Print a customizable hello world message with validation"


class HelloWorldCommand(InteractiveCommand):
    """Enhanced hello world command with Pydantic validation"""
    
    def __init__(self):
        super().__init__(name="hello_world", description=DESCRIPTION)
        # Set the validation model for this command
        self.validation_model = HelloWorldModel
    
    def validation(self, *args, **kwargs) -> bool:
        """
        Enhanced validation using Pydantic model.
        
        This method validates all arguments using the HelloWorldModel
        and stores the validated data for use in execute().
        """
        try:
            # Create model instance from parsed arguments
            validated_model = HelloWorldModel(**self.parsed_args)
            
            # Store the validated model instance for use in execute
            self.validated_data = validated_model
            
            # Update parsed_args with validated data
            self.parsed_args = validated_model.model_dump()
            
            self.logger.info("HelloWorld command validation successful")
            return True
            
        except Exception as e:
            error_msg = f"Hello World validation failed: {str(e)}"
            self.logger.error(error_msg)
            self.print_error(error_msg)
            
            # Show usage help on validation error
            self._show_usage_help()
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the hello world command with validated parameters"""
        
        # Use validated data from validation step
        validated_model = getattr(self, 'validated_data', None)
        
        if validated_model is None:
            # Fallback if validation wasn't run properly
            validated_model = HelloWorldModel(**self.parsed_args)
        
        # Generate greeting message using the model
        greeting_message = validated_model.get_greeting_message()
        
        # Display the greeting
        self.print_success(greeting_message)
        
        # Show command info if verbose
        if validated_model.is_verbose():
            self.print_info("This is an enhanced SCLI command with Pydantic validation")
            self.print_info(f"Language: {validated_model.language}")
            self.print_info(f"Name: {validated_model.name}")
            self.print_info(f"Emoji enabled: {validated_model.emoji}")
            self.print_info(f"Uppercase: {validated_model.uppercase}")
        
        # Set results for reporting
        self.set_result("message", greeting_message)
        self.set_result("language", validated_model.language)
        self.set_result("name", validated_model.name)
        self.set_result("emoji_enabled", validated_model.emoji)
        self.set_result("uppercase", validated_model.uppercase)
        self.set_result("command_type", "enhanced_with_validation")
        
        return True
    
    def _show_usage_help(self):
        """Show usage help for the command"""
        self.print_info("Usage: scli -s hello_world [OPTIONS] [NAME]")
        self.print_info("")
        self.print_info("Options:")
        self.print_info("  --name NAME           Name to greet (default: World)")
        self.print_info("  --language LANG       Language for greeting (english, spanish, french, german, italian)")
        self.print_info("  --emoji / --no-emoji  Include emoji (default: true)")
        self.print_info("  --uppercase           Display in uppercase")
        self.print_info("  --verbose, -v         Show detailed information")
        self.print_info("")
        self.print_info("Examples:")
        self.print_info("  scli -s hello_world")
        self.print_info("  scli -s hello_world --name Alice --language spanish")
        self.print_info("  scli -s hello_world Alice --uppercase --no-emoji")
        self.print_info("  scli -s hello_world --verbose")
    
    def get_help(self) -> str:
        """Get detailed help for the command"""
        help_text = super().get_help()
        help_text += "\n\nCommand-specific options:\n"
        help_text += "  --name NAME           Name to greet (default: World)\n"
        help_text += "  --language LANG       Language (english, spanish, french, german, italian)\n"  
        help_text += "  --emoji / --no-emoji  Include emoji (default: true)\n"
        help_text += "  --uppercase           Display in uppercase\n"
        help_text += "\nSupported languages: english, spanish, french, german, italian\n"
        
        return help_text


# Create command instance for the new system
command_instance = HelloWorldCommand()
