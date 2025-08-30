# CLAUDE.md - Project Context

## Project Overview

**SCLI** es un proyecto **CLI interactivo** desarrollado con Python 3.12 y uv como gestor de paquetes. El código principal está organizado en la carpeta `src/` con `main.py` como punto de entrada.

### Contexto Temporal

**Fecha actual: 2025**. Todas las búsquedas web, investigación de librerías, mejores prácticas y tecnologías deben enfocarse en lo más reciente y actualizado posible. Priorizar:

- Versiones más recientes de paquetes Python
- Últimas mejores prácticas de desarrollo
- Tecnologías y enfoques modernos de 2024-2025
- Documentación y recursos actualizados

### Características del CLI Interactivo

- **Navegación con flechas direccionales** y selección numérica
- **Búsqueda/filtrado** de opciones en tiempo real
- **Loading indicators** dinámicos con spinners personalizables
- **Interfaz moderna** similar a herramientas como Claude Code

## Development Environment

- **Python Version**: 3.12+ (required)
- **Package Manager**: uv (required)
- **Virtual Environment**: `.venv` (auto-created by uv)
- **Entry Point**: `src/main.py`

## Project Structure

```
scli/
├── src/
│   ├── __init__.py            # Package init with version
│   ├── main.py               # Main entry point (MINIMAL - no business logic)
│   └── utils/               # Utilities directory (ALL reusable functions)
│       ├── __init__.py      # Utils package init
│       ├── logger.py        # Logging system
│       └── argument_parser.py # CLI argument parsing
├── tests/                   # Testing directory
│   ├── integration/         # Integration tests (70%)
│   └── e2e/                # End-to-end tests (30%)
├── pyproject.toml           # Project configuration
├── README.md               # User documentation  
├── CLAUDE.md               # This file - AI assistant context
└── .venv/                  # Virtual environment (auto-generated)
```

## Commands & Scripts

```bash
# Setup and sync dependencies
uv sync

# Run the application
uv run scli
uv run scli --help

# Direct execution
uv run python src/main.py

# Add dependencies
uv add <package-name>

# Development dependencies
uv add --dev <dev-package>
```

## Recommended CLI Interactive Libraries

### Core CLI Framework

- **typer**: Moderno framework CLI con type hints (recomendado para comandos base)
- **click**: Framework CLI maduro y estable (alternativa a typer)

### Interactive Menu & Navigation

- **simple-term-menu**: Menús con navegación por flechas (Unix/Linux/macOS solamente)
- **survey**: Navegación por flechas + búsqueda/filtrado en tiempo real
- **cutie**: Interface simple para menús selectables
- **inquirer**: Puerto de Inquirer.js, muy completo pero soporte experimental en Windows
- **prompt_toolkit**: Más bajo nivel pero muy poderoso para interfaces complejas

### Loading & Progress Indicators

- **rich**: Library completa para CLI con status, progress, spinners, colores (RECOMENDADO)

  ```python
  from rich.console import Console
  console = Console()
  with console.status("Loading...") as status:
      # Cambiar texto dinámicamente
      status.update("Processing...")
  ```

- **yaspin**: Spinner con actualizaciones dinámicas de texto (más features)
- **halo**: Spinners hermosos y simples

### Platform Compatibility

- **Windows**: usar `survey`, `cutie`, `rich`, `halo`, `yaspin`
- **Unix/Linux/macOS**: cualquier librería, `simple-term-menu` es excelente
- **Cross-platform**: `rich` + `survey` o `rich` + `prompt_toolkit`

### Recommended Stack

```python
# Combinación recomendada para máxima funcionalidad
uv add rich          # Para styling, progress, spinners
uv add survey        # Para menús interactivos cross-platform  
uv add typer         # Para estructura de comandos CLI
```

## Code Style & Standards

### Python Conventions

- Use **Python 3.12+** features when appropriate
- Follow **PEP 8** style guide
- Use **type hints** for function parameters and return values
- Use **docstrings** for all public functions and classes
- Prefer **f-strings** for string formatting
- Use **pathlib** instead of os.path for file operations

### Import Organization Rules

**🚨 MANDATORY Import Structure** - 3 secciones separadas con líneas en blanco:

```python
# ❌ INCORRECTO - Imports mezclados y sin organización
import sys
from typing import List
from src.utils.logger import logger
from src.utils.argument_parser import validate_named_flags_only, parse_args_to_dict

# ✅ CORRECTO - Imports organizados por categorías
import sys
from traceback import format_exc as traceback_format_exc  # Siempre con alias descriptivo
from typing import List, Dict  # Especificar importaciones individuales

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from accounts.models import UserActivity
from basic.logger_v2 import logger
from commons.config.dynamo_modules_configuration import dynamoModulesConfig
from commons.config.dynamo_modules_configuration import DynamoModulesConfigModules  # Nunca multiple imports en una línea
```

**Import Rules OBLIGATORIAS**:
- ✅ **3 secciones separadas**: Nativas → Third-party → Propias (con líneas en blanco entre ellas)
- ✅ **Imports específicos**: `from typing import Dict` NO `import typing`
- ✅ **Alias descriptivos**: `from traceback import format_exc as traceback_format_exc`
- ✅ **Una importación por línea**: Especialmente para archivos propios del proyecto
- ❌ **NUNCA comentarios de sección**: El orden ya indica la categoría
- ❌ **NUNCA mezclar** imports de diferentes categorías
- ❌ **NUNCA imports múltiples** del mismo módulo en una línea para archivos propios

### File Structure

- Keep `src/main.py` as the primary entry point
- Create modules in `src/` directory as needed
- Use `__init__.py` files for package organization
- Limit individual files to reasonable size (< 500 lines)

## Testing Requirements

- Write unit tests for all new functionality
- Place tests in `tests/` directory (create when needed)
- Use pytest as testing framework
- Aim for meaningful test coverage
- Test both success and error cases

## Documentation Standards

### Docstrings Rules

**🚨 MANDATORY**: Todos los métodos, funciones `def` y clases DEBEN tener docstring con el siguiente formato:

#### **Para Clases:**
```python
class CheckpointsLeavesFlow(APIView):
    """
    Agenda un punto de contacto para enviar notificaciones a los usuarios que han
    dejado un flujo de pago. El punto de contacto se programa según el tipo de
    producto y el botón de pago (entity) que se ha seleccionado.

    Methods
    -------
    post : Genera el punto de contacto
    get : Obtiene información del punto de contacto

    Attributes
    ----------
    authentication_classes : tuple
        Clases de autenticación requeridas
    permission_classes : tuple
        Clases de permisos requeridas

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30

    :Updated:
        - 2025-08-30
    """
```

#### **Para Funciones/Métodos con Parámetros:**
```python
def register_user_activity(
    user: User,
    action: str,
    request: HttpRequest,
    additional_data: Dict = None,
) -> Dict:
    """
    Registra una nueva actividad de usuario en la tabla UserActivity.

    Parameters
    ----------
    user : User
        El usuario que realiza la acción
    action : str
        La acción realizada, debe ser una de las opciones en UserActivity.ACTION_CHOICES
    request : HttpRequest
        La solicitud HTTP actual
    additional_data : dict, optional
        Datos adicionales para almacenar en el campo JSONField

    Returns
    -------
    dict
        Un diccionario que contiene:
        - 'is_valid' (bool): True si la actividad se registró con éxito
        - 'activity' (UserActivity): La instancia creada y guardada

    Examples
    --------
    >>> user = User.objects.get(username='testuser')
    >>> result = register_user_activity(
    ...     user=user,
    ...     action='login',
    ...     request=request,
    ...     additional_data={'ip': '192.168.1.1'}
    ... )
    >>> print(result['is_valid'])
    True
    
    >>> # Caso con error
    >>> result = register_user_activity(
    ...     user=None,
    ...     action='invalid',
    ...     request=request
    ... )
    >>> print(result['is_valid'])
    False

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
```

#### **Para Funciones Simples:**
```python
def parse_iso8601_duration(duration_string: str) -> timedelta:
    """
    Convierte un string de duración ISO 8601 en un objeto timedelta.

    Soporta años (Y), meses (M), semanas (W), días (D), horas (H), minutos (M), segundos (S).

    Parameters
    ----------
    duration_string : str
        String de duración en formato ISO 8601

    Returns
    -------
    timedelta
        Objeto timedelta con la duración especificada

    Examples
    --------
    >>> parse_iso8601_duration('PT10M')
    datetime.timedelta(seconds=600)
    
    >>> parse_iso8601_duration('P1DT2H30M')
    datetime.timedelta(days=1, seconds=9000)
    
    >>> parse_iso8601_duration('PT0S')
    datetime.timedelta(0)

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
```

#### **Docstring Format Rules:**
- ✅ **Descripción corta**: Primera línea describe qué hace
- ✅ **Descripción larga**: Detalles adicionales si es necesario (línea en blanco después de la corta)
- ✅ **Parameters**: Formato con `----------` debajo, tipo y descripción separados por `:`
- ✅ **Returns**: Formato con `-------` debajo, tipo y descripción
- ✅ **Examples**: Formato con `--------` debajo, casos de uso prácticos con `>>>` (doctests)
- ✅ **Methods** (clases): Lista de métodos principales con `-------`
- ✅ **Attributes** (clases): Lista de atributos con `----------` 
- ✅ **:Authors:**: Obtener de `git config --global user.name` (`- $(git config --global user.name)`)
- ✅ **:Created:**: Fecha actual en formato `YYYY-MM-DD` (usar `date +%Y-%m-%d`)
- ✅ **:Updated:**: Fecha de última actualización (opcional) en formato `YYYY-MM-DD`

#### **🚨 MANDATORY Update Rules:**
- ✅ **Actualizar docstring SIEMPRE** que se modifique una función y cambie input/output
- ✅ **Examples deben reflejar** la funcionalidad actual de la función
- ✅ **Parameters y Returns** deben estar sincronizados con la firma actual
- ✅ **:Updated:** debe agregarse con fecha actual cuando se modifique funcionalidad
- ✅ **Examples con casos reales**: Incluir casos de éxito y error cuando sea relevante

#### **Examples Format Rules:**
- ✅ **Usar doctests**: Formato `>>> función(args)` seguido del resultado esperado
- ✅ **Casos múltiples**: Incluir al menos 2-3 ejemplos diferentes
- ✅ **Casos edge**: Incluir casos límite o de error cuando sea relevante
- ✅ **Comentarios**: Usar `# Caso con error` para clarificar ejemplos complejos

**Comandos para obtener valores dinámicamente:**
```bash
# Obtener autor de git config global
git config --global user.name  # Returns: Pablo Contreras
git config --global user.email # Returns: pacg1991@gmail.com

# Obtener fecha actual
date +%Y-%m-%d                  # Returns: 2025-08-30
```

### README.md Synchronization

**IMPORTANTE**: Cuando se modifique el README.md, actualizar también esta sección de CLAUDE.md con un resumen de los cambios principales para mantener el contexto actualizado.

**Último resumen del README.md**:

- Instalación con `uv sync`
- Ejecución con `uv run scli` o `uv run python src/main.py`
- Gestión de dependencias con `uv add`
- **Testing**: Comandos para ejecutar tests con `python tests/run.py`
- **Filosofía TDD**: Integration + E2E tests, sin unit tests
- **TDD Workflow**: Proceso Red-Green-Refactor documentado
- Estructura completa del proyecto incluyendo tests/ y archivos de configuración

## Quality Assurance Checklist

Antes de completar cualquier tarea, verificar:

- [ ] **🚨 TDD OBLIGATORIO**: Test que falla escrito ANTES de cualquier código de implementación
- [ ] **RED-GREEN-REFACTOR**: Proceso TDD seguido estrictamente (test falla → código mínimo → refactor)
- [ ] **Tests pasan**: `python tests/run.py` ejecutado y exitoso
- [ ] **Coverage**: Integration + E2E cubren comportamiento crítico de la nueva feature
- [ ] Código sigue las convenciones de estilo establecidas
- [ ] Type hints están presentes en funciones públicas
- [ ] Docstrings están actualizados
- [ ] No hay imports no utilizados
- [ ] Funciones tienen una responsabilidad clara
- [ ] Error handling es apropiado
- [ ] README.md está actualizado si es necesario
- [ ] CLAUDE.md refleja cambios en la estructura del proyecto

## Project-Specific Rules

1. **Mantenimiento de dependencias**: Solo agregar dependencias realmente necesarias
2. **Estructura src/**: Todo el código de aplicación debe estar en `src/`
3. **Entry point único**: `src/main.py` debe ser el único punto de entrada
4. **Gestión de errores**: Usar códigos de salida apropiados (0 = éxito, >0 = error)
5. **Logging**: NUNCA usar print() directamente - SIEMPRE usar src.utils.logger
6. **CLI Design**: Seguir convenciones estándar de herramientas CLI de Unix

### CLI Interactive Specific Rules

7. **Navegación**: Implementar navegación con flechas direccionales Y números
8. **Búsqueda**: Incluir filtrado/búsqueda en tiempo real cuando sea apropiado
9. **Loading feedback**: Usar spinners informativos para operaciones >1 segundo
10. **Cross-platform**: Priorizar librerías que funcionen en Windows, macOS y Linux
11. **UX Consistency**: Mantener patrones de interacción consistentes en toda la aplicación
12. **Fallback options**: Siempre proveer alternativas por teclado (números) además de flechas

### Utils Architecture Rules

13. **Utils Standard**: Para cualquier utilidad crear archivo en carpeta `src/utils/` con nombre `<util>.py`
14. **Logger Mandatory**: PROHIBIDO usar print() - usar únicamente `src.utils.logger`
15. **Logger Features**: Sistema centralizado con Loguru - colores, path, datetime, niveles, rotación de archivos
16. **Logger Pre-initialized**: Usar `logger = Logger()` pre-inicializada en utils/logger.py
17. **Function Organization**: Funciones reutilizables deben ir en `src/utils/` - NO en `src/main.py`
18. **Utils Examples**: `argument_parser.py`, `logger.py`, `file_handler.py`, `config_loader.py`

### TDD (Test-Driven Development) Rules

13. **Ciclo Red-Green-Refactor**: Escribir test → Fallar → Escribir código mínimo → Pasar → Refactorizar
14. **Un test fallando**: Nunca tener más de un test fallando al mismo tiempo
15. **Test Behavior**: Testear comportamiento real, no implementación interna
16. **Test Distribution**: 70% integration tests, 30% e2e tests (NO unit tests)
17. **Fast Feedback**: Usar markers pytest para excluir tests lentos durante desarrollo
18. **No Mocks**: Evitar mocks complejos - usar componentes reales cuando sea posible
17. **🚨 MANDATORY TDD**: TODA nueva feature DEBE empezar con un test que falle ANTES de escribir código

## Logging System Architecture

### Logger System Overview

**Sistema centralizado de logging usando Loguru** como librería base para gestión avanzada de logs en consola y archivos.

### Logger Features

- **Colored console output**: Colores automáticos basados en log levels
- **VS Code navigation**: Formato clickeable `utils/logger.py:line` relativo desde src/ para navegación directa
- **File path tracking**: Path completo + línea + función para debugging
- **Datetime formatting**: Timestamps legibles con formato personalizable
- **Log levels**: trace, debug, info, success, warning, error, critical
- **File rotation**: Archivos rotativos por tamaño/tiempo con compresión
- **Structured logging**: Soporte JSON para análisis automático
- **Thread-safe**: Operaciones seguras en entornos multi-hilo

### Logger Implementation

```python
# src/utils/logger.py - Pre-initialized logger
from src.utils.logger import logger

# Usage: logger.method()
logger.info("Message")
logger.error("Error message") 
logger.success("Success message")
```

### Logger Usage Rules

- ❌ **NEVER use print()** - Usar siempre el logger
- ❌ **NEVER use "as e" in except** - Usar `logger.critical()` para capturar traceback completo automático
- ❌ **NEVER use f-strings or b-strings** - Solo plain strings como primer argumento
- ✅ **Always import logger class**: `from src.utils.logger import logger`
- ✅ **Logger Format OBLIGATORIO**: 
  - **Primer argumento**: Solo plain string (NUNCA f-strings)
  - **Segundo argumento**: `detail` como dict opcional (NO se imprime en output)
  - ✅ **CORRECTO**: `logger.info("User logged in", detail={"user_id": user_id})`
  - ❌ **INCORRECTO**: `logger.info(f"User {user_id} logged in")`
- ✅ **Use appropriate levels**: 
  - `logger.info()` - Información general
  - `logger.success()` - Operaciones exitosas 
  - `logger.warning()` - Advertencias
  - `logger.error()` - Errores recuperables
  - `logger.critical()` - Errores críticos (con traceback automático)
  - `logger.debug()` - Información de desarrollo
  - `logger.trace()` - Información muy detallada
- ✅ **Exception handling**: `logger.critical("Context message")` en lugar de "as e"

### Logger Configuration

- **Development**: Console con colores + archivos rotativos
- **Testing**: Solo warnings y errores críticos
- **Production**: Solo errores en consola + logging completo a archivos

### Example Usage

```python
# ❌ WRONG
print("Starting application...")
try:
    operation()
except Exception as e:
    print(f"Error: {e}")

# ✅ CORRECT  
from src.utils.logger import logger

logger.info("Starting application...")
try:
    operation()
except Exception:
    logger.critical("Operation failed during startup")
```

### Exception Handling Pattern

```python
# ❌ WRONG PATTERN
try:
    risky_operation()
except ValueError as e:
    print(f"Value error: {e}")
except Exception as e:
    print(f"General error: {e}")

# ✅ CORRECT PATTERN  
from src.utils.logger import logger

try:
    risky_operation()
except ValueError:
    logger.critical("Invalid value provided to risky_operation")
except Exception:
    logger.critical("Unexpected error in risky_operation")
```

## Test-Driven Development (TDD) Setup

### Testing Structure

```
tests/
├── __init__.py              # Tests package
├── conftest.py             # Pytest fixtures y configuración
├── integration/           # Integration tests (70%) - módulos trabajando juntos
└── e2e/                  # End-to-end tests (30%) - workflows completos de usuario
```

**Filosofía: No Unit Tests**

- ❌ Sin mocks complejos que ensucian el código
- ❌ Sin tests de funciones aisladas que se rompen al refactorizar  
- ✅ Solo tests que verifican comportamiento real del usuario
- ✅ Integration tests para lógica interna sin mocks

### Testing Dependencies (Dev)

```bash
# Core testing framework
pytest>=8.4.1              # Testing framework moderno
pytest-cov>=6.2.1         # Coverage reporting
pytest-mock>=3.14.1       # Mocking utilities
pytest-console-scripts    # CLI testing específico
coverage>=7.10.6          # Coverage measurement

# CLI Testing (incluido en proyecto)
typer[testing]            # Typer CliRunner para testing
rich                      # Console testing
```

### TDD Workflow Cycle (Integration-First)

#### 1. RED Phase (Integration test que falle)

```python
# test_cli_navigation.py
@pytest.mark.integration
def test_menu_navigation_with_arrow_keys():
    # Arrange - componentes reales trabajando juntos
    menu = MenuSystem(['Option 1', 'Option 2', 'Exit'])
    keyboard_input = ArrowKeySimulator()
    
    # Act - testear comportamiento real
    keyboard_input.press_down_arrow(2)  
    result = menu.get_selected_option()
    
    # Assert comportamiento esperado
    assert result.text == "Exit"
    assert result.index == 2
```

#### 2. GREEN Phase (Implementación mínima)

```python
# src/menu_system.py
class MenuSystem:
    def __init__(self, options):
        self.options = options
        self.selected_index = 0
        
    def handle_arrow_down(self):
        self.selected_index = min(self.selected_index + 1, len(self.options) - 1)
        
    def get_selected_option(self):
        return {'text': self.options[self.selected_index], 'index': self.selected_index}
```

#### 3. REFACTOR Phase (Mejorar sin romper behavior)

```python
# Refactorizar manteniendo el test verde - sin mocks
class MenuSystem:
    def __init__(self, options: List[str]):
        self._options = options
        self._current_selection = 0
        
    def navigate_down(self) -> None:
        """Navigate to next option, wrapping to first if at end."""
        self._current_selection = (self._current_selection + 1) % len(self._options)
```

### CLI Testing Best Practices (No Mocks)

#### Integration Testing - Módulos trabajando juntos

```python
@pytest.mark.integration
def test_cli_menu_integration():
    # Testea: CLI parser + Menu system + Navigation
    from src.cli import parse_command  
    from src.menu import create_interactive_menu
    
    # Componentes reales trabajando juntos
    args = parse_command(['menu', '--options', 'file1,file2,file3'])
    menu = create_interactive_menu(args.options)
    result = menu.select_by_index(1)
    
    assert result == 'file2'
    assert menu.current_selection == 1
```

#### E2E Testing - Usuario real workflow

```python
@pytest.mark.e2e
def test_complete_cli_workflow():
    # Usuario ejecuta comando real
    process = subprocess.run(
        ['uv', 'run', 'scli', 'interactive-menu'],
        input='2\n',  # Usuario presiona 2 + Enter
        text=True,
        capture_output=True
    )
    
    assert process.returncode == 0
    assert "Option 2 selected" in process.stdout
```

#### Testing Rich Components - Sin mocks

```python  
@pytest.mark.integration
def test_spinner_with_rich():
    # Testea rich spinner + console sin mocks
    from rich.console import Console
    from io import StringIO
    
    fake_stdout = StringIO()
    console = Console(file=fake_stdout)
    
    with console.status("Loading..."):
        # Simula operación
        time.sleep(0.1)
    
    output = fake_stdout.getvalue()
    assert len(output) > 0  # Spinner produjo output
```

### Testing Commands

```bash
# Ejecutar todos los tests
uv run pytest

# Solo integration tests (rápidos para desarrollo)  
uv run pytest -m integration

# Solo E2E tests (más lentos)
uv run pytest -m e2e

# Excluir tests lentos durante desarrollo
uv run pytest -m "not slow"

# Con coverage
uv run pytest --cov=src --cov-report=html

# Watch mode para TDD (con pytest-watch si se agrega)
uv run ptw tests/integration/
```

### Test Markers Usage

```python
import pytest

@pytest.mark.integration  
def test_modules_working_together():
    # Testea múltiples componentes sin mocks
    pass

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_user_workflow():
    # Testea comando completo como usuario real
    pass

@pytest.mark.integration
@pytest.mark.slow  
def test_complex_integration_with_files():
    # Integration test que requiere I/O real
    pass
```

## Workflow Instructions

### 🚨 TDD OBLIGATORIO para nuevas funcionalidades

**REGLA DE ORO**: Jamás escribir código de implementación sin un test que falle primero.

#### Proceso estricto TDD

1. **📝 PLANIFICAR**: Definir qué comportamiento debe tener la feature
2. **🔴 RED**: Escribir integration test que falle describiendo el comportamiento esperado
3. **✅ GREEN**: Escribir el código MÍNIMO necesario para que el test pase
4. **🔧 REFACTOR**: Mejorar implementación sin romper el test
5. **🔄 REPETIR**: Solo un test fallando a la vez, commits frecuentes

#### ⚠️ Proceso bloqueante

- **NO código** sin test que falle primero
- **NO implementación** antes de definir comportamiento en test
- **NO feature completa** sin pasar por Red-Green-Refactor

### Para modificaciones de código

1. Leer este CLAUDE.md completamente antes de empezar
2. Escribir/actualizar tests PRIMERO (TDD)
3. Entender la estructura actual del proyecto
4. Seguir las convenciones establecidas
5. Ejecutar tests: `uv run pytest`
6. Verificar que el código funciona con `uv run scli`

### Para nuevas funcionalidades (PROCESO ESTRICTO)

1. **🚨 STOP**: ¿Ya existe un test que falle para esta feature? Si NO → ir a paso 2
2. **📋 DISCUTIR**: Definir comportamiento esperado y estructura antes de implementar
3. **🔴 TEST PRIMERO**: Escribir integration test que falle describiendo el comportamiento
4. **🧪 EJECUTAR**: `python tests/run.py` debe mostrar 1 test FALLANDO
5. **✅ IMPLEMENTAR**: Código mínimo para que el test pase (GREEN)
6. **🔧 REFACTOR**: Mejorar implementación manteniendo test verde
7. **📚 DOCUMENTAR**: Actualizar README.md con nueva funcionalidad
8. **🔄 SINCRONIZAR**: Cambios importantes en este CLAUDE.md

#### ❌ Violaciones NO permitidas

- Empezar con código antes del test
- Implementar sin test que falle
- Commits sin pasar tests

### 🎯 Ejemplo práctico TDD estricto

#### Mala práctica (❌)

```python
# ❌ MAL: Escribir código primero
def create_interactive_menu(options):
    # Implementación aquí...
    return menu
```

#### Buena práctica TDD (✅)

```python
# ✅ BIEN: Test primero (RED)
# tests/integration/menu.py
@pytest.mark.integration
def test_interactive_menu_creation():
    """Test que falla - describe comportamiento esperado."""
    options = ["File 1", "File 2", "Exit"]
    menu = create_interactive_menu(options)
    
    assert menu.options == options
    assert menu.current_selection == 0
    assert menu.can_navigate() == True
    # Este test DEBE fallar porque create_interactive_menu() no existe

# Ejecutar: python tests/run.py (debe mostrar 1 FAILING)

# ✅ BIEN: Código mínimo (GREEN)  
# src/menu.py
def create_interactive_menu(options):
    """Implementación mínima para pasar test."""
    class Menu:
        def __init__(self, opts):
            self.options = opts
            self.current_selection = 0
        def can_navigate(self):
            return True
    return Menu(options)

# Ejecutar: python tests/run.py (debe mostrar PASSING)

# ✅ BIEN: Refactor (mantener GREEN)
# Mejorar implementación sin romper test
```

#### 🔄 Workflow comando por comando

```bash
# 1. RED - Escribir test que falle
echo "Escribiendo test..." && python tests/run.py  # ❌ 1 FAILING

# 2. GREEN - Código mínimo  
echo "Implementando..." && python tests/run.py    # ✅ ALL PASSING

# 3. REFACTOR - Mejorar código
echo "Refactorizando..." && python tests/run.py  # ✅ ALL PASSING

# 4. Commit solo cuando todos los tests pasen
git add . && git commit -m "feat: add interactive menu (TDD)"
```

## Emergency Commands

Si algo no funciona:

```bash
# Recrear entorno virtual
rm -rf .venv
uv sync

# Verificar instalación
uv run python -c "import src; print('OK')"

# Ejecutar directamente
python src/main.py
```

---

**Nota**: Este archivo debe mantenerse actualizado conforme evoluciona el proyecto. Cualquier cambio significativo en README.md debe reflejarse aquí de forma resumida.
