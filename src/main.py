from sys import argv as sys_argv
from sys import exit as sys_exit
from typing import List
from typing import Dict
from typing import Any
from json import dumps as json_dumps

from settings.config import app_config
from src.utils.logger import logger
from src.utils.argument_parser import validate_named_flags_only
from src.utils.argument_parser import parse_args_to_dict
from src.utils.dynamic_importer import execute_command_cycle
from src.utils.interactive_selector import select_command_interactively


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
    
    # Handle help request if enabled (but not for empty args - that goes to interactive selection)
    if app_config.help_enabled and ("--help" in args or "-h" in args):
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
    
    # Handle dynamic command execution system  
    if "command" in parsed_args or "c" in parsed_args:
        return _handle_dynamic_command(parsed_args)
    
    # Handle interactive command selection if no command specified
    if not parsed_args or (len(parsed_args) == 0):
        return _handle_interactive_selection()
    
    # Log arguments after handling special commands
    logger.info("Arguments processed successfully", detail={
        "parsed_args": parsed_args,
        "output_format": app_config.output_format
    })
    
    # Display output based on configured format
    if app_config.output_format == "json":
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


def _handle_dynamic_command(parsed_args: Dict[str, Any]) -> int:
    """
    Handle dynamic command execution using the import system.
    
    Expects 'command' or 'c' key with the command name to execute.
    Uses the dynamic importer to load and execute the command.
    
    Parameters
    ----------
    parsed_args : Dict[str, Any]
        Argumentos parseados que incluyen 'command' o 'c' con el nombre del comando
        
    Returns
    -------
    int
        Exit code (0 for success, 1+ for error)
        
    Examples
    --------
    scli --command hello_world --name Usuario
    scli -c hello_world --name Usuario
    scli --command test_spinner --duration 5
    scli -c test_spinner --duration 5
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    command_name = parsed_args.get("command") or parsed_args.get("c")
    
    if not command_name:
        logger.error("No command name provided", detail={
            "parsed_args": parsed_args,
            "expected_usage": "scli --command <command_name> [--option value] OR scli -c <command_name> [--option value]"
        })
        return 1
    
    logger.info("Executing dynamic command", detail={
        "command_name": command_name,
        "args_provided": len(parsed_args) - 1,  # Exclude 'command' key
        "all_args": parsed_args
    })
    
    # Remover 'command' y 'c' de los argumentos para pasarlos al comando
    command_args = {k: v for k, v in parsed_args.items() if k not in ("command", "c")}
    
    # Ejecutar comando dinámicamente
    try:
        exit_code = execute_command_cycle(command_name, command_args)
        logger.debug("Dynamic command completed", detail={
            "command_name": command_name,
            "exit_code": exit_code
        })
        return exit_code
    except Exception:
        logger.critical("Error during dynamic command execution", detail={
            "command_name": command_name,
            "args": command_args
        })
        return 1


def _handle_interactive_selection() -> int:
    """
    Maneja la selección interactiva cuando no se especifica comando.
    
    Muestra una interfaz para que el usuario seleccione un comando
    de la lista de comandos disponibles.
    
    Returns
    -------
    int
        Exit code (0 for success, 1 for error)
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    logger.info("Iniciando selección interactiva de comando")
    
    try:
        selected_command = select_command_interactively()
        
        if selected_command:
            logger.info("Ejecutando comando seleccionado interactivamente", detail={
                "command": selected_command
            })
            # Ejecutar comando sin argumentos adicionales
            return execute_command_cycle(selected_command, {})
        else:
            logger.info("Selección cancelada por usuario")
            return 0
            
    except KeyboardInterrupt:
        logger.info("Selección interrumpida por usuario (Ctrl+C)")
        return 0
    except Exception:
        logger.critical("Error durante selección interactiva")
        return 1


if __name__ == "__main__":
    sys_exit(main())