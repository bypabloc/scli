"""
Main entry point for SCLI application
"""

import sys
from typing import List

from src.utils.logger import logger
from src.utils.argument_parser import validate_named_flags_only, parse_args_to_dict


def main(args: List[str] = None) -> int:
    """
    Main function for the SCLI application.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:] if None)
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    if args is None:
        args = sys.argv[1:]
    
    logger.success("🚀 SCLI - Python CLI Project")
    logger.debug("Arguments received", detail={"args": args})
    
    # Validate that only named flags are used
    if not validate_named_flags_only(args):
        logger.error("❌ Error: Only named flags (--option) are allowed.")
        logger.error("Use --help for usage information.")
        return 1
    
    # Parse arguments to dictionary and display
    parsed_args = parse_args_to_dict(args)
    logger.info("Parsed arguments", detail={"parsed_args": parsed_args})
    
    return 0


if __name__ == "__main__":
    sys.exit(main())