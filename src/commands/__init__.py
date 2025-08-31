"""
Módulo de comandos SCLI.

Este paquete contiene todas las implementaciones de comandos disponibles
en el sistema SCLI. Cada comando sigue el patrón estándar con métodos
validate(), preload() y execute().
"""

from src.commands.hello_world import HelloWorld
from src.commands.hello_world import create_hello_world_command
from src.commands.hello_world import run_hello_world_command
from src.commands.test_spinner import TestSpinner
from src.commands.test_spinner import create_test_spinner_command
from src.commands.test_spinner import run_test_spinner_command

# API pública del paquete commands
__all__ = [
    'HelloWorld',
    'create_hello_world_command',
    'run_hello_world_command',
    'TestSpinner',
    'create_test_spinner_command',
    'run_test_spinner_command'
]