from typing import List
from typing import Optional
from os import listdir as os_listdir
from os.path import isfile as os_path_isfile
from os.path import join as os_path_join
from pathlib import Path

from src.utils.logger import logger
from src.utils.string_converter import convert_case_style


def get_available_commands() -> List[str]:
    """
    Obtiene lista de comandos disponibles desde src/commands/.
    
    Escanea el directorio src/commands/ buscando archivos .py que contengan
    clases de comando válidas y retorna los nombres en snake_case.
    
    Returns
    -------
    List[str]
        Lista de nombres de comandos disponibles en formato snake_case
        
    Examples
    --------
    >>> commands = get_available_commands()
    >>> 'hello_world' in commands
    True
    
    >>> 'test_spinner' in commands
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    commands_dir = Path("src/commands")
    available_commands = []
    
    logger.debug("Escaneando directorio de comandos", detail={
        "commands_dir": str(commands_dir),
        "exists": commands_dir.exists()
    })
    
    if not commands_dir.exists():
        logger.warning("Directorio de comandos no encontrado", detail={
            "path": str(commands_dir)
        })
        return []
    
    try:
        # Escanear archivos .py en el directorio de comandos
        for filename in os_listdir(commands_dir):
            file_path = os_path_join(commands_dir, filename)
            
            # Solo archivos .py que no sean __init__.py
            if (os_path_isfile(file_path) and 
                filename.endswith('.py') and 
                filename != '__init__.py'):
                
                # El nombre del archivo es el comando (sin .py)
                command_name = filename[:-3]  # Remove .py extension
                
                # Verificar que el archivo contenga una clase válida
                if _is_valid_command_file(file_path, command_name):
                    available_commands.append(command_name)
                    
        logger.debug("Comandos encontrados", detail={
            "count": len(available_commands),
            "commands": available_commands
        })
        
    except Exception:
        logger.critical("Error al escanear directorio de comandos", detail={
            "commands_dir": str(commands_dir)
        })
        return []
    
    # Ordenar por atributo order en lugar de alfabéticamente
    return sorted(available_commands, key=get_command_order)


def _is_valid_command_file(file_path: str, command_name: str) -> bool:
    """
    Verifica si un archivo contiene una clase de comando válida usando análisis estático.
    
    Esto evita importaciones innecesarias que generan logs durante el escaneo.
    
    Parameters
    ----------
    file_path : str
        Ruta al archivo a verificar
    command_name : str
        Nombre esperado del comando (snake_case)
        
    Returns
    -------
    bool
        True si el archivo parece contener una clase válida, False en caso contrario
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
        
    :Updated:
        - 2025-09-01 (Cambio a análisis estático para evitar importaciones innecesarias)
    """
    try:
        # Leer el contenido del archivo
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Convertir command_name a class_name esperado (snake_case a PascalCase)
        expected_class_name = convert_case_style(command_name, "PascalCase")
        
        # Verificaciones básicas por análisis de texto (más flexibles)
        checks = [
            # 1. Debe importar BaseCommand
            "from src.utils.base_command import BaseCommand" in content,
            # 2. Debe tener una clase con el nombre esperado
            f"class {expected_class_name}" in content,
            # 3. La clase debe heredar de BaseCommand (flexible con espacios)
            f"{expected_class_name}(BaseCommand)" in content.replace(" ", "").replace("\n", ""),
            # 4. Debe tener atributo description
            "description" in content
        ]
        
        # Todas las verificaciones deben pasar
        is_valid = all(checks)
        
        if not is_valid:
            logger.debug("Archivo no pasa validaciones estáticas", detail={
                "file": file_path,
                "command_name": command_name,
                "expected_class": expected_class_name,
                "checks_passed": sum(checks),
                "total_checks": len(checks)
            })
            
        return is_valid
            
    except Exception as e:
        logger.debug("Error al leer archivo de comando", detail={
            "file": file_path,
            "error": str(e)
        })
        return False


def filter_commands(commands: List[str], search_term: str) -> List[str]:
    """
    Filtra comandos basándose en un término de búsqueda o número de orden.
    
    Realiza búsqueda fuzzy en los nombres de comandos, permitiendo
    coincidencias parciales y flexibles. También permite filtrar por
    número de orden del comando.
    
    Parameters
    ----------
    commands : List[str]
        Lista de comandos disponibles
    search_term : str
        Término de búsqueda (puede ser parcial) o número de orden
        
    Returns
    -------
    List[str]
        Lista filtrada de comandos que coinciden con el término
        
    Examples
    --------
    >>> commands = ['hello_world', 'test_spinner', 'user_profile']
    >>> filter_commands(commands, 'hello')
    ['hello_world']
    
    >>> filter_commands(commands, '1')
    ['hello_world']  # Si hello_world tiene order=1
    
    >>> filter_commands(commands, 'test')
    ['test_spinner']
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
        
    :Updated:
        - 2025-08-31 (Agregado filtrado por número de orden)
    """
    if not search_term:
        return commands
    
    search_lower = search_term.lower().strip()
    filtered = []
    
    # Verificar si el término de búsqueda es un número (filtrado por order)
    if search_term.strip().isdigit():
        target_order = int(search_term.strip())
        logger.debug("Filtrando por número de orden", detail={
            "target_order": target_order,
            "commands_count": len(commands)
        })
        
        for command in commands:
            command_order = get_command_order(command)
            if command_order == target_order:
                filtered.append(command)
                logger.debug("Comando encontrado por orden", detail={
                    "command": command,
                    "order": command_order
                })
    else:
        # Filtrado tradicional por nombre de comando
        for command in commands:
            command_lower = command.lower()
            
            # Coincidencia exacta al inicio (alta prioridad)
            if command_lower.startswith(search_lower):
                filtered.insert(0, command)
                continue
                
            # Coincidencia parcial en cualquier parte
            if search_lower in command_lower:
                filtered.append(command)
                continue
                
            # Coincidencia fuzzy - caracteres en orden
            if _fuzzy_match(command_lower, search_lower):
                filtered.append(command)
    
    logger.debug("Comandos filtrados", detail={
        "search_term": search_term,
        "search_type": "numeric" if search_term.strip().isdigit() else "text",
        "original_count": len(commands),
        "filtered_count": len(filtered),
        "results": filtered[:5]  # Solo primeros 5 para logging
    })
    
    return filtered


def _fuzzy_match(text: str, pattern: str) -> bool:
    """
    Realiza matching fuzzy entre texto y patrón.
    
    Verifica si todos los caracteres del patrón aparecen en orden
    en el texto, permitiendo caracteres intermedios.
    
    Parameters
    ----------
    text : str
        Texto donde buscar
    pattern : str
        Patrón a buscar
        
    Returns
    -------
    bool
        True si hay coincidencia fuzzy, False en caso contrario
        
    Examples
    --------
    >>> _fuzzy_match("hello_world", "hlwrd")
    True
    
    >>> _fuzzy_match("test_spinner", "tspn")
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not pattern:
        return True
        
    text_idx = 0
    
    for char in pattern:
        # Buscar el carácter desde la posición actual
        while text_idx < len(text) and text[text_idx] != char:
            text_idx += 1
            
        # Si no encontramos el carácter, no hay match
        if text_idx >= len(text):
            return False
            
        # Avanzar para el siguiente carácter
        text_idx += 1
    
    return True


def format_command_list(commands: List[str], selected_index: int = -1) -> str:
    """
    Formatea lista de comandos para display interactivo.
    
    Parameters
    ----------
    commands : List[str]
        Lista de comandos a formatear
    selected_index : int, optional
        Índice del comando seleccionado (-1 para ninguno)
        
    Returns
    -------
    str
        String formateado con la lista de comandos
        
    Examples
    --------
    >>> commands = ['hello_world', 'test_spinner']
    >>> result = format_command_list(commands, 0)
    >>> '→ 1. hello_world' in result
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not commands:
        return "  No hay comandos disponibles"
    
    lines = []
    for i, command in enumerate(commands):
        prefix = "→ " if i == selected_index else "  "
        lines.append(f"{prefix}{i + 1}. {command}")
    
    return "\n".join(lines)


def get_command_order(command_name: str) -> int:
    """
    Obtiene el orden de un comando desde su atributo order.
    
    Parameters
    ----------
    command_name : str
        Nombre del comando en snake_case
        
    Returns
    -------
    int
        Número de orden del comando (default: 999 para comandos sin order)
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    try:
        from src.utils.dynamic_importer import import_command
        from src.utils.result_types import is_success
        
        result = import_command(command_name)
        if is_success(result):
            command_class = result['class']
            
            # Crear instancia para obtener el orden del atributo
            try:
                instance = command_class()
                if hasattr(instance, 'order') and isinstance(instance.order, int):
                    return instance.order
            except Exception:
                logger.critical("Error al crear instancia para obtener order", detail={
                    "command_name": command_name,
                    "class_name": command_class.__name__
                })
        
        # Valor por defecto alto para comandos sin order o con errores
        return 999
        
    except Exception:
        return 999


def get_command_description(command_name: str) -> str:
    """
    Obtiene descripción de un comando desde su atributo description.
    
    Parameters
    ----------
    command_name : str
        Nombre del comando en snake_case
        
    Returns
    -------
    str
        Descripción del comando o mensaje por defecto
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    try:
        from src.utils.dynamic_importer import import_command
        from src.utils.result_types import is_success
        
        result = import_command(command_name)
        if is_success(result):
            command_class = result['class']
            
            # Crear instancia para obtener la descripción del atributo
            try:
                instance = command_class()
                if hasattr(instance, 'description') and instance.description.strip():
                    return instance.description.strip()
            except Exception:
                logger.critical("Error al crear instancia para obtener descripción", detail={
                    "command_name": command_name,
                    "class_name": command_class.__name__
                })
        
        return "Descripción no disponible"
        
    except Exception:
        return "Descripción no disponible"


# API pública del módulo
__all__ = [
    'get_available_commands',
    'filter_commands', 
    'format_command_list',
    'get_command_order',
    'get_command_description'
]