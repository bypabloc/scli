from sys import argv as sys_argv
from sys import exit as sys_exit
from typing import List

from settings.config import app_config
from src.utils.logger import logger
from src.utils.argument_parser import validate_named_flags_only
from src.utils.argument_parser import parse_args_to_dict


def main(args: List[str] = None) -> int:
    """
    Main function for the SCLI application.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:] if None)
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    if args is None:
        args = sys_argv[1:]
    
    # Log startup with configuration context
    logger.success("🚀 SCLI - Python CLI Project")
    logger.debug("Application startup", detail={
        "version": app_config.version,
        "environment": app_config.environment,
        "debug_mode": app_config.debug_mode,
        "args": args
    })
    
    # Handle help request if enabled
    if app_config.help_enabled and (not args or "--help" in args or "-h" in args):
        logger.info("Help requested", detail={"help_enabled": app_config.help_enabled})
        print(f"SCLI v{app_config.version} - Interactive CLI Application")
        print("Usage: scli [--option value] [--flag]")
        print("Only named flags are supported (--option value)")
        return 0
    
    # Handle version request
    if "--version" in args or "-v" in args:
        print(f"SCLI v{app_config.version}")
        return 0
    
    # Validate argument length if configured
    if len(args) > app_config.max_args_length:
        logger.error("Too many arguments", detail={
            "provided": len(args),
            "max_allowed": app_config.max_args_length
        })
        return 1
    
    # Validate that only named flags are used (if enabled in config)
    if app_config.validate_named_flags_only and not validate_named_flags_only(args):
        logger.error("❌ Error: Only named flags (--option) are allowed.")
        if app_config.help_enabled:
            logger.error("Use --help for usage information.")
        return 1
    
    # Parse arguments to dictionary
    parsed_args = parse_args_to_dict(args)
    
    # Handle test-spinner command early (before other logging)
    if "test-spinner" in parsed_args:
        return _handle_spinner_test()
    
    # Log arguments after handling special commands
    logger.info("Arguments processed successfully", detail={
        "parsed_args": parsed_args,
        "output_format": app_config.output_format
    })
    
    # Display output based on configured format
    if app_config.output_format == "json":
        from json import dumps as json_dumps
        print(json_dumps(parsed_args, indent=2))
    elif app_config.output_format == "table":
        if parsed_args:
            for key, value in parsed_args.items():
                print(f"  {key}: {value}")
        else:
            print("No arguments provided")
    else:  # simple format
        if parsed_args:
            print(f"Processed {len(parsed_args)} arguments")
        else:
            print("No arguments")
    
    logger.success("Application completed successfully")
    return 0


def _handle_spinner_test() -> int:
    """
    Handle --test-spinner command to demonstrate spinner functionality.
    
    Returns:
        Exit code (0 for success)
    """
    from time import sleep as time_sleep
    from src.utils.spinner import create_spinner
    
    logger.info("Starting spinner test demonstration")
    
    # Create spinner using app_config settings
    spinner = create_spinner("Initializing test")
    
    try:
        spinner.start()
        
        # First 2 seconds - Initialization
        time_sleep(2)
        spinner.update_text("Loading configuration")
        
        # Second 2 seconds - Processing
        time_sleep(2)
        spinner.update_text("Processing data")
        
        # Third 2 seconds - Finalizing
        time_sleep(2)
        spinner.update_text("Finalizing operations")
        
        # Fourth 2 seconds - Completion
        time_sleep(2)
        
        # Complete
        spinner.stop()
        
    except Exception as e:
        spinner.stop("❌ Spinner test failed")
        logger.error("Spinner test error", detail={"error": str(e)})
        return 1
    
    logger.success("Spinner test demonstration completed")
    return 0


if __name__ == "__main__":
    sys_exit(main())