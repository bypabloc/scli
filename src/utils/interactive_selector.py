from typing import Optional
from typing import List

try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Prompt = None

try:
    # Survey requiere stdin interactivo, solo importar en entornos apropiados
    import sys
    if hasattr(sys.stdin, 'fileno') and sys.stdin.isatty():
        import survey
        SURVEY_AVAILABLE = True
    else:
        SURVEY_AVAILABLE = False
        survey = None
except (ImportError, OSError, AttributeError):
    SURVEY_AVAILABLE = False
    survey = None

from src.utils.logger import logger
from src.utils.command_selector import get_available_commands
from src.utils.command_selector import filter_commands
from src.utils.command_selector import get_command_description
from src.utils.command_selector import get_command_order


def select_command_interactively() -> Optional[str]:
    """
    Permite al usuario seleccionar un comando de forma interactiva.
    
    Muestra una lista de comandos disponibles con múltiples modos de selección:
    
    **Modo Survey (Preferido)**:
    - ↑↓ Navegación con flechas direccionales
    - Búsqueda en tiempo real (escribir para filtrar)
    - Colores y formato mejorado
    
    **Modo Rich (Fallback)**:
    - Selección por número o búsqueda por texto
    - Interfaz visual mejorada con tablas
    
    **Modo Básico (Fallback)**:
    - Selección por número
    - Búsqueda por texto manual
    - Compatible con terminals básicos
    
    Returns
    -------
    Optional[str]
        Nombre del comando seleccionado o None si se cancela
        
    Examples
    --------
    >>> # En uso interactivo con Survey:
    >>> # 🚀 Seleccione comando (use ↑↓ flechas, escriba para buscar):
    >>> # → hello_world - Comando simple que demuestra la estructura básica de un comando en SCLI
    >>> #   test_spinner - Comando para demostrar la funcionalidad del spinner dinámico de SCLI
    >>> selected = select_command_interactively()  # doctest: +SKIP
    >>> selected
    'hello_world'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
        
    :Updated:
        - 2025-08-31 (Agregada navegación con flechas y búsqueda en tiempo real)
    """
    logger.info("Iniciando selección interactiva de comando")
    
    try:
        # Obtener comandos disponibles
        commands = get_available_commands()
        
        if not commands:
            logger.warning("No hay comandos disponibles")
            _print_error("No se encontraron comandos disponibles")
            return None
        
        logger.debug("Comandos disponibles para selección", detail={
            "count": len(commands),
            "commands": commands[:10]  # Primeros 10 para logging
        })
        
        # Modo interactivo con Survey (navegación con flechas + búsqueda)
        if SURVEY_AVAILABLE:
            return _select_with_survey(commands)
        # Fallback a Rich si está disponible
        elif RICH_AVAILABLE:
            return _select_with_rich(commands)
        # Fallback a modo básico
        else:
            return _select_with_basic_input(commands)
            
    except KeyboardInterrupt:
        logger.info("Selección interrumpida por usuario (Ctrl+C)")
        return None
    except Exception:
        logger.critical("Error durante selección interactiva")
        return None


def _select_with_survey(commands: List[str]) -> Optional[str]:
    """
    Selección interactiva usando Survey con navegación por flechas y búsqueda.
    
    Parameters
    ----------
    commands : List[str]
        Lista de comandos disponibles
        
    Returns
    -------
    Optional[str]
        Comando seleccionado o None si se cancela
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    try:
        # Crear opciones con formato: "orden. comando - descripción"
        options = []
        command_mapping = {}  # Map from display option to command name
        
        for command in commands:
            order = get_command_order(command)
            description = get_command_description(command)
            display_option = f"{order}. {command} - {description}"
            options.append(display_option)
            command_mapping[display_option] = command
        
        logger.debug("Iniciando selector Survey", detail={
            "options_count": len(options),
            "commands": commands[:5]  # Primeros 5 para logging
        })
        
        # Usar Survey select con búsqueda integrada y filtros mejorados
        # Usar primer argumento posicional como prompt y options como keyword
        selected_option = survey.routines.select(
            "🚀 Seleccione comando: [filter: type | move: ↑↓]",
            options=options,
            focus_mark="→ ",
            focus_color=survey.colors.basic('cyan'),
            evade_color=survey.colors.basic('white'),
            permit=True  # Permite búsqueda en tiempo real
        )
        
        if selected_option is None:
            logger.info("Selección cancelada por usuario")
            return None
            
        # Manejar diferentes tipos de respuesta de Survey
        selected_command = None
        
        # Si Survey retorna un índice numérico
        if isinstance(selected_option, int):
            if 0 <= selected_option < len(options):
                selected_display = options[selected_option]
                selected_command = command_mapping.get(selected_display)
                logger.debug("Survey retornó índice", detail={
                    "index": selected_option,
                    "display": selected_display,
                    "command": selected_command
                })
        # Si Survey retorna la opción completa (string)
        elif isinstance(selected_option, str):
            selected_command = command_mapping.get(selected_option)
            logger.debug("Survey retornó string", detail={
                "display": selected_option,
                "command": selected_command
            })
        
        if selected_command:
            logger.info("Comando seleccionado con Survey", detail={
                "selected": selected_command,
                "option_type": type(selected_option).__name__,
                "option_value": str(selected_option)[:50] + "..." if len(str(selected_option)) > 50 else str(selected_option)
            })
            return selected_command
        else:
            logger.error("Error al mapear opción seleccionada", detail={
                "selected_option": selected_option,
                "selected_type": type(selected_option).__name__,
                "available_mappings": list(command_mapping.keys())[:3]
            })
            return None
            
    except KeyboardInterrupt:
        logger.info("Selección interrumpida por usuario (Ctrl+C)")
        return None
    except Exception:
        logger.critical("Error en selector Survey, usando fallback")
        # Fallback a Rich o modo básico
        if RICH_AVAILABLE:
            return _select_with_rich(commands)
        else:
            return _select_with_basic_input(commands)


def _select_with_rich(commands: List[str]) -> Optional[str]:
    """
    Selección interactiva usando Rich para mejor UX con búsqueda mejorada.
    
    Parameters
    ----------
    commands : List[str]
        Lista de comandos disponibles
        
    Returns
    -------
    Optional[str]
        Comando seleccionado o None si se cancela
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
        
    :Updated:
        - 2025-08-31 (Mejorada búsqueda interactiva y UX)
    """
    console = Console()
    filtered_commands = commands.copy()
    search_history = []
    
    while True:
        # Limpiar pantalla y mostrar header
        console.clear()
        
        # Header con información mejorada y filtros
        header_text = "[bold blue]🚀 SCLI - Selector de Comandos Interactivo[/bold blue]\n"
        header_text += "[dim italic]\\[filter: type | move: ↑↓][/dim italic]"
        if search_history:
            header_text += f"\n[dim]Búsquedas: {' → '.join(search_history[-3:])}[/dim]"
        
        header = Panel.fit(header_text, border_style="blue")
        console.print(header)
        console.print()
        
        # Mostrar comandos disponibles en tabla mejorada con orden
        if filtered_commands:
            table = Table(show_header=True, header_style="bold magenta", show_lines=True)
            table.add_column("#", style="dim", width=4)
            table.add_column("Orden", style="bold yellow", width=6)
            table.add_column("Comando", style="bold cyan", min_width=15)
            table.add_column("Descripción", style="green", no_wrap=False)
            
            # Mostrar hasta 8 resultados para mejor visualización
            display_count = min(8, len(filtered_commands))
            for i, cmd in enumerate(filtered_commands[:display_count], 1):
                order = get_command_order(cmd)
                description = get_command_description(cmd)
                # Truncar descripción larga
                if len(description) > 60:
                    description = description[:57] + "..."
                table.add_row(str(i), str(order), cmd, description)
            
            console.print(table)
            
            if len(filtered_commands) > display_count:
                console.print(f"\n[dim italic]... y {len(filtered_commands) - display_count} comandos más (refine su búsqueda)[/dim]")
                
        else:
            console.print("[red]❌ No se encontraron comandos con esa búsqueda[/red]")
            if search_history:
                console.print("[yellow]💡 Intente con términos más generales[/yellow]")
        
        console.print()
        
        # Instrucciones mejoradas
        if filtered_commands:
            console.print("[dim]💡 Opciones:[/dim]")
            console.print(f"[dim]  • Número (1-{len(filtered_commands)}): Seleccionar comando[/dim]")
            console.print("[dim]  • Texto: Buscar/filtrar comandos por nombre[/dim]")
            console.print("[dim]  • Número de orden: Filtrar por número de orden del comando[/dim]")
            console.print("[dim]  • Enter vacío: Cancelar[/dim]")
        else:
            console.print("[dim]💡 Escriba texto para buscar comandos o presione Enter para cancelar[/dim]")
        
        console.print()
        
        # Prompt mejorado para selección
        prompt_text = "[bold yellow]🔍 Comando o búsqueda[/bold yellow]"
        if filtered_commands and len(filtered_commands) <= 8:
            prompt_text += " [dim](1-{})".format(len(filtered_commands))
        
        selection = Prompt.ask(prompt_text, default="", console=console, show_default=False).strip()
        
        if not selection:
            logger.info("Selección cancelada por usuario")
            return None
        
        # Verificar si es un número
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(filtered_commands):
                selected_command = filtered_commands[index]
                logger.info("Comando seleccionado por número", detail={
                    "selected": selected_command,
                    "index": index + 1,
                    "search_path": " → ".join(search_history) if search_history else "direct"
                })
                return selected_command
            else:
                console.print(f"[red]❌ Número inválido. Use 1-{len(filtered_commands)}[/red]")
                console.input("[dim]Presione Enter para continuar...[/dim]")
                continue
        
        # Si no es número, usar como filtro de búsqueda
        search_history.append(selection)
        filtered_commands = filter_commands(commands, selection)
        
        if len(filtered_commands) == 1:
            # Solo un resultado, seleccionarlo automáticamente
            selected_command = filtered_commands[0]
            logger.info("Comando seleccionado por búsqueda única", detail={
                "selected": selected_command,
                "search": selection,
                "search_path": " → ".join(search_history)
            })
            return selected_command


def _select_with_basic_input(commands: List[str]) -> Optional[str]:
    """
    Selección interactiva básica sin Rich.
    
    Parameters
    ----------
    commands : List[str]
        Lista de comandos disponibles
        
    Returns
    -------
    Optional[str]
        Comando seleccionado o None si se cancela
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    filtered_commands = commands.copy()
    
    try:
        while True:
            print("\n" + "="*50)
            print("🚀 SCLI - Selector de Comandos")
            print("[filter: type | move: ↑↓]")
            print("="*50)
            
            if filtered_commands:
                print("\nComandos disponibles:")
                for i, cmd in enumerate(filtered_commands[:10], 1):
                    order = get_command_order(cmd)
                    description = get_command_description(cmd)
                    print(f"  {i}. [{order}] {cmd} - {description}")
                
                if len(filtered_commands) > 10:
                    print(f"  ... y {len(filtered_commands) - 10} comandos más")
            else:
                print("\nNo se encontraron comandos con esa búsqueda")
            
            print("\nOpciones:")
            print("  - Número (1-{}): Seleccionar comando".format(len(filtered_commands)))
            print("  - Texto: Buscar comandos por nombre")
            print("  - Número de orden: Filtrar por número de orden [1,2,3...]")
            print("  - Enter vacío: Cancelar")
            
            selection = input("\nSeleccione comando: ").strip()
            
            if not selection:
                logger.info("Selección cancelada por usuario")
                return None
            
            # Verificar si es un número
            if selection.isdigit():
                index = int(selection) - 1
                if 0 <= index < len(filtered_commands):
                    selected_command = filtered_commands[index]
                    logger.info("Comando seleccionado por número", detail={
                        "selected": selected_command,
                        "index": index + 1
                    })
                    return selected_command
                else:
                    print(f"\n❌ Número inválido. Use 1-{len(filtered_commands)}")
                    input("Presione Enter para continuar...")
                    continue
            
            # Si no es número, usar como filtro
            filtered_commands = filter_commands(commands, selection)
            
            if len(filtered_commands) == 1:
                selected_command = filtered_commands[0]
                logger.info("Comando seleccionado por búsqueda única", detail={
                    "selected": selected_command,
                    "search": selection
                })
                return selected_command
                
    except KeyboardInterrupt:
        logger.info("Selección interrumpida por usuario (Ctrl+C)")
        return None


def _print_error(message: str) -> None:
    """
    Imprime mensaje de error con formato apropiado.
    
    Parameters
    ----------
    message : str
        Mensaje de error a mostrar
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if RICH_AVAILABLE:
        console = Console()
        console.print(f"[red]❌ {message}[/red]")
    else:
        print(f"❌ {message}")


def show_command_help() -> None:
    """
    Muestra ayuda sobre el sistema de comandos.
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    help_text = """
🚀 SCLI - Sistema de Comandos

FORMAS DE USO:
  scli --command <nombre> [argumentos]     # Forma larga
  scli -c <nombre> [argumentos]            # Forma corta
  scli --command                           # Selección interactiva
  scli -c                                  # Selección interactiva

EJEMPLOS:
  scli --command hello_world --name Usuario
  scli -c hello_world --name Usuario
  scli -c test_spinner --duration 5
  scli --command                           # Abre selector interactivo

SELECCIÓN INTERACTIVA:
  - Use números para seleccionar directamente
  - Escriba texto para buscar comandos
  - Use Enter vacío para cancelar
"""
    
    if RICH_AVAILABLE:
        console = Console()
        panel = Panel.fit(help_text.strip(), title="Ayuda", border_style="green")
        console.print(panel)
    else:
        print(help_text)


# API pública del módulo
__all__ = [
    'select_command_interactively',
    'show_command_help'
]