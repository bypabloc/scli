from typing import List

try:
    from settings.config import app_config
except ImportError:
    # Fallback configuration if settings not available
    class MockConfig:
        max_args_length = 1000
        validate_named_flags_only = True
        
    app_config = MockConfig()


def validate_named_flags_only(args: List[str]) -> bool:
    """
    Validate that all arguments follow named flag pattern using app_config settings.
    
    Valid patterns:
    - [] (empty)
    - ["--flag"] (flag only)
    - ["--flag", "value"] (flag with value)
    - ["--flag1", "--flag2"] (multiple flags)
    - ["--flag1", "value1", "--flag2", "value2"] (multiple flags with values)
    
    Invalid patterns:
    - ["command"] (positional argument)
    - ["--flag", "val", "positional"] (mixed)
    
    Args:
        args: List of command line arguments
        
    Returns:
        True if all arguments follow named flag pattern, False otherwise
    """
    if not args:  # Empty args are valid
        return True
    
    # Check if named flag validation is enabled in config
    if not app_config.validate_named_flags_only:
        return True  # Skip validation if disabled
    
    # Check argument count limit
    max_length = app_config.max_args_length or 1000
    if len(args) > max_length:
        return False
    
    expecting_value = False
    
    for i, arg in enumerate(args):
        if arg.startswith('--'):
            # This is a long flag
            expecting_value = True  # Next arg could be a value
        elif arg.startswith('-') and len(arg) == 2 and arg[1].isalpha():
            # This is a short flag (like -c, -h, -v)
            expecting_value = True  # Next arg could be a value
        else:
            # This is not a flag
            if expecting_value:
                # This could be a value for the previous flag
                expecting_value = False
            else:
                # This is a positional argument (invalid)
                return False
    
    return True


def parse_args_to_dict(args: List[str]) -> dict:
    """
    Parse named flag arguments into a dictionary using app_config settings.
    
    Args:
        args: List of command line arguments with named flags
        
    Returns:
        Dictionary with flag names as keys and their values
        
    Raises:
        ValueError: If arguments exceed configured limits or contain invalid patterns
    """
    # Check argument count limit
    max_length = app_config.max_args_length or 1000
    if len(args) > max_length:
        raise ValueError(f"Too many arguments: {len(args)} exceeds limit of {max_length}")
    
    parsed_args = {}
    i = 0
    flag_count = 0
    
    while i < len(args):
        if args[i].startswith('--'):
            # Long flag (--flag)
            flag_count += 1
            flag_name = args[i][2:]  # Remove '--' prefix
            
            # Validate flag name is not empty
            if not flag_name:
                raise ValueError("Invalid flag: '--' without flag name")
            
            # Check if next arg is a value (not a flag)
            if i + 1 < len(args) and not args[i + 1].startswith('-'):
                value = args[i + 1]
                
                # Basic value validation (could be extended with more rules from config)
                if len(value) > 1000:  # Reasonable limit for flag values
                    raise ValueError(f"Flag value too long for '--{flag_name}': {len(value)} characters")
                
                parsed_args[flag_name] = value
                i += 2  # Skip both flag and value
            else:
                # Flag without value (boolean flag)
                parsed_args[flag_name] = True
                i += 1
        elif args[i].startswith('-') and len(args[i]) == 2 and args[i][1].isalpha():
            # Short flag (-c, -h, -v, etc.)
            flag_count += 1
            flag_name = args[i][1]  # Remove '-' prefix and get single character
            
            # Check if next arg is a value (not a flag)
            if i + 1 < len(args) and not args[i + 1].startswith('-'):
                value = args[i + 1]
                
                # Basic value validation
                if len(value) > 1000:  # Reasonable limit for flag values
                    raise ValueError(f"Flag value too long for '-{flag_name}': {len(value)} characters")
                
                parsed_args[flag_name] = value
                i += 2  # Skip both flag and value
            else:
                # Flag without value (boolean flag)
                parsed_args[flag_name] = True
                i += 1
        else:
            # This shouldn't happen if validation passed
            i += 1
    
    return parsed_args


def get_argument_validation_config() -> dict:
    """
    Get current argument validation configuration from app_config.
    
    Returns:
        Dictionary with validation settings
    """
    return {
        'max_args_length': app_config.max_args_length or 1000,
        'validate_named_flags_only': app_config.validate_named_flags_only,
        'help_enabled': app_config.help_enabled,
        'version': app_config.version or '1.0.0'
    }