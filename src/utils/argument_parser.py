"""
Argument parsing utilities for SCLI application

Functions for validating and parsing command-line arguments with named flag patterns.
"""

from typing import List


def validate_named_flags_only(args: List[str]) -> bool:
    """
    Validate that all arguments follow named flag pattern.
    
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
    
    expecting_value = False
    
    for i, arg in enumerate(args):
        if arg.startswith('--'):
            # This is a flag
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
    Parse named flag arguments into a dictionary.
    
    Args:
        args: List of command line arguments with named flags
        
    Returns:
        Dictionary with flag names as keys and their values
    """
    parsed_args = {}
    i = 0
    
    while i < len(args):
        if args[i].startswith('--'):
            flag_name = args[i][2:]  # Remove '--' prefix
            
            # Check if next arg is a value (not a flag)
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                parsed_args[flag_name] = args[i + 1]
                i += 2  # Skip both flag and value
            else:
                # Flag without value (boolean flag)
                parsed_args[flag_name] = True
                i += 1
        else:
            # This shouldn't happen if validation passed
            i += 1
            
    return parsed_args