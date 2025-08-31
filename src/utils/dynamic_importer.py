from importlib import import_module
from traceback import format_exc as traceback_format_exc

from src.utils.logger import logger
from src.utils.result_types import ResultDict
from src.utils.result_types import error
from src.utils.result_types import success
from src.utils.string_converter import convert_case_style


def import_command(operation: str) -> ResultDict:
    """
    Importa dinámicamente un comando basado en la operación.
    
    Busca e importa una clase de comando desde src/commands/ basándose en el
    nombre de la operación proporcionado. Convierte automáticamente de
    snake_case a PascalCase para el nombre de la clase.
    
    Parameters
    ----------
    operation : str
        Nombre de la operación a importar (en snake_case)
        
    Returns
    -------
    ResultDict
        Dict con is_valid = True y datos del comando o is_valid = False si falla
        Incluye claves: 'class', 'class_name', 'module', 'command_class'
        
    Examples
    --------
    >>> result = import_command("hello_world")
    >>> result['is_valid']
    True
    >>> result['class'].__name__
    'HelloWorld'
    
    >>> result = import_command("non_existent")
    >>> result['is_valid']
    False
    >>> result['data']['error_code']
    'MODULE_NOT_FOUND'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not operation:
        result = error(
            code=1,
            data={
                'error_code': 'INVALID_OPERATION',
                'message': 'Operation name cannot be empty',
            },
        )
        result['class'] = None  # Compatibility for direct access
        return result
    
    # Convertir snake_case a PascalCase para nombre de clase
    try:
        class_name = convert_case_style(operation, 'PascalCase')
    except Exception:
        logger.critical("Error al convertir nombre de operación a PascalCase", detail={
            'operation': operation,
            'traceback': traceback_format_exc()
        })
        result = error(
            code=1,
            data={
                'error_code': 'CASE_CONVERSION_ERROR',
                'message': f"Could not convert operation name '{operation}' to PascalCase",
            },
        )
        result['class'] = None
        return result
    
    logger.debug("Iniciando importación dinámica de comando", detail={
        'operation': operation,
        'class_name': class_name,
        'module_path': f"src.commands.{operation}"
    })
    
    # Intentar importar el módulo del comando
    try:
        module = import_module(f"src.commands.{operation}")
        logger.debug("Módulo importado exitosamente", detail={
            'operation': operation,
            'module_name': module.__name__
        })
    except (ImportError, ModuleNotFoundError):
        logger.critical("Error al importar módulo de comando", detail={
            'operation': operation,
            'module_path': f"src.commands.{operation}",
            'traceback': traceback_format_exc()
        })
        result = error(
            code=1,
            data={
                'error_code': 'MODULE_NOT_FOUND',
                "message": f"Command module '{operation}' not found in src.commands",
            },
        )
        result['class'] = None
        return result
    except Exception:
        logger.critical("Error inesperado al importar módulo", detail={
            'operation': operation,
            'traceback': traceback_format_exc()
        })
        result = error(
            code=1,
            data={
                'error_code': 'IMPORT_ERROR',
                'message': "Unexpected error importing command module",
            },
        )
        result['class'] = None
        return result
    
    # Intentar obtener la clase del comando
    try:
        command_class = getattr(module, class_name)
        logger.debug("Clase de comando encontrada", detail={
            'operation': operation,
            'class_name': class_name,
            'class_type': str(type(command_class))
        })
    except AttributeError:
        logger.critical("Clase de comando no encontrada en módulo", detail={
            'operation': operation,
            'class_name': class_name,
            'module_name': module.__name__,
            'available_attrs': [attr for attr in dir(module) if not attr.startswith('_')],
            'traceback': traceback_format_exc()
        })
        result = error(
            code=1,
            data={
                'error_code': 'CLASS_NOT_FOUND',
                "message": f"Command class '{class_name}' not found in module '{operation}'",
            },
        )
        result['class'] = None
        return result
    except Exception:
        logger.critical("Error inesperado al obtener clase", detail={
            'operation': operation,
            'class_name': class_name,
            'traceback': traceback_format_exc()
        })
        result = error(
            code=1,
            data={
                'error_code': 'CLASS_ACCESS_ERROR',
                'message': "Unexpected error accessing command class",
            },
        )
        result['class'] = None
        return result
    
    # Verificar que la clase sea una subclase de BaseCommand (opcional)
    try:
        from src.utils.base_command import BaseCommand
        if not issubclass(command_class, BaseCommand):
            logger.warning("Clase importada no hereda de BaseCommand", detail={
                'operation': operation,
                'class_name': class_name,
                'base_classes': [base.__name__ for base in command_class.__bases__]
            })
    except ImportError:
        # Si BaseCommand no está disponible, continuar sin validación
        logger.debug("BaseCommand no disponible para validación", detail={
            'operation': operation
        })
    except Exception:
        logger.critical("Error al validar herencia de BaseCommand", detail={
            'operation': operation
        })
    
    # Éxito - retornar datos del comando
    data = {
        'class_name': class_name,
        'module': module,
        'command_class': command_class,
        'operation': operation
    }
    
    result = success(data)
    result['class'] = command_class  # Compatibility for direct access
    
    logger.success("Comando importado exitosamente", detail={
        'operation': operation,
        'class_name': class_name,
        'module_path': module.__name__
    })
    
    return result


def create_command_instance(operation: str, args: dict = None) -> ResultDict:
    """
    Importa dinámicamente un comando y crea una instancia.
    
    Combina la importación dinámica con la creación de instancia,
    proporcionando un método conveniente para obtener un comando listo para usar.
    
    Parameters
    ----------
    operation : str
        Nombre de la operación a importar (en snake_case)
    args : dict, optional
        Argumentos a pasar al constructor del comando
        
    Returns
    -------
    ResultDict
        Dict con is_valid = True e instancia del comando o is_valid = False si falla
        Incluye claves: 'instance', 'class', 'class_name', 'operation'
        
    Examples
    --------
    >>> result = create_command_instance("hello_world", {"name": "Usuario"})
    >>> result['is_valid']
    True
    >>> isinstance(result['instance'], BaseCommand)
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    # Importar el comando
    import_result = import_command(operation)
    
    if not import_result['is_valid']:
        # Retornar el error de importación tal como está
        import_result['instance'] = None
        return import_result
    
    command_class = import_result['class']
    
    # Intentar crear la instancia
    try:
        instance = command_class(args)
        logger.debug("Instancia de comando creada", detail={
            'operation': operation,
            'class_name': import_result['data']['class_name'],
            'args_provided': args is not None,
            'args_count': len(args) if args else 0
        })
    except Exception:
        logger.critical("Error al crear instancia de comando", detail={
            'operation': operation,
            'class_name': import_result['data']['class_name'],
            'args': args,
            'traceback': traceback_format_exc()
        })
        result = error(
            code=1,
            data={
                'error_code': 'INSTANCE_CREATION_ERROR',
                'message': f"Could not create instance of command '{operation}'",
            },
        )
        result['instance'] = None
        result['class'] = command_class
        return result
    
    # Éxito - retornar instancia
    data = {
        'instance': instance,
        'class': command_class,
        'class_name': import_result['data']['class_name'],
        'operation': operation,
        'module': import_result['data']['module']
    }
    
    result = success(data)
    result['instance'] = instance  # Compatibility for direct access
    result['class'] = command_class
    
    logger.success("Instancia de comando creada exitosamente", detail={
        'operation': operation,
        'class_name': import_result['data']['class_name']
    })
    
    return result


def execute_command_cycle(operation: str, args: dict = None) -> int:
    """
    Ejecuta el ciclo completo de un comando: importar, instanciar y ejecutar.
    
    Método de conveniencia que combina importación dinámica, creación de instancia
    y ejecución del ciclo completo del comando (validate, preload, execute).
    
    Parameters
    ----------
    operation : str
        Nombre de la operación a ejecutar (en snake_case)
    args : dict, optional
        Argumentos a pasar al comando
        
    Returns
    -------
    int
        Código de salida del comando (0 para éxito, >0 para error)
        
    Examples
    --------
    >>> exit_code = execute_command_cycle("hello_world", {"name": "Usuario"})
    >>> exit_code == 0
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    logger.info("Iniciando ejecución completa de comando", detail={
        'operation': operation,
        'args_provided': args is not None
    })
    
    # Crear instancia del comando
    instance_result = create_command_instance(operation, args)
    
    if not instance_result['is_valid']:
        error_msg = instance_result['data'].get('message', 'Unknown error')
        logger.error("No se pudo crear comando para ejecución", detail={
            'operation': operation,
            'error': error_msg,
            'error_code': instance_result['data'].get('error_code', 'UNKNOWN')
        })
        return 1
    
    command_instance = instance_result['instance']
    
    # Ejecutar el ciclo completo del comando
    try:
        exit_code = command_instance.run_command_cycle()
        logger.info("Ciclo de comando completado", detail={
            'operation': operation,
            'exit_code': exit_code
        })
        return exit_code
    except Exception:
        logger.critical("Error durante la ejecución del comando", detail={
            'operation': operation,
            'traceback': traceback_format_exc()
        })
        return 1


# API pública del módulo
__all__ = [
    'import_command',
    'create_command_instance',
    'execute_command_cycle'
]