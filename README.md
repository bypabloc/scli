# SCLI - Python CLI Project

Un proyecto CLI desarrollado con Python 3.12 y uv como gestor de paquetes.

## Instalación

### Requisitos previos
- Python 3.12 o superior
- uv (gestor de paquetes)

### Pasos de instalación

1. Clonar o descargar el proyecto
2. Navegar al directorio del proyecto
3. Instalar dependencias y crear entorno virtual:

```bash
uv sync
```

## Ejecución

### Usando el comando scli
```bash
# Ejecutar con argumentos
uv run scli

# Ejecutar con argumentos específicos
uv run scli --help
```

### Ejecutar directamente src/main.py
```bash
# Usando uv run
uv run python src/main.py

# O activando el entorno virtual
source .venv/bin/activate
python src/main.py
```

### Agregar dependencias
```bash
uv add <nombre-del-paquete>
```

## Testing

### Ejecutar tests
```bash
# Todos los tests (integration + e2e)
python tests/run.py

# Solo integration tests (más rápidos)
python tests/run.py --integration

# Solo e2e tests (más lentos)
python tests/run.py --e2e

# Tests rápidos (excluir lentos)
python tests/run.py --fast

# Tests con coverage
python tests/run.py --coverage
```

### Filosofía de testing
- **Integration tests (70%)**: Componentes trabajando juntos sin mocks
- **E2E tests (30%)**: Workflows completos de usuario
- **Sin unit tests**: Evitamos mocks complejos que ensucian el código

### TDD Workflow
```bash
# 1. Escribir test que falle
echo "Test que falla..." && python tests/run.py  # ❌ 1 FAILING

# 2. Código mínimo para pasar
echo "Implementando..." && python tests/run.py   # ✅ ALL PASSING

# 3. Refactorizar
echo "Mejorando..." && python tests/run.py      # ✅ ALL PASSING
```

## Estructura del proyecto

```
scli/
├── src/
│   ├── __init__.py
│   └── main.py          # Punto de entrada principal
├── tests/               # Tests organizados por tipo
│   ├── run.py          # Test runner principal
│   ├── conftest.py     # Fixtures compartidos
│   ├── integration/    # Tests de integración (70%)
│   │   ├── cli.py
│   │   └── main.py
│   └── e2e/           # Tests end-to-end (30%)
│       └── cli.py
├── pyproject.toml       # Configuración del proyecto
├── pytest.ini         # Configuración de pytest
├── CLAUDE.md          # Contexto y reglas del proyecto
├── README.md          # Este archivo
└── .venv/             # Entorno virtual (generado automáticamente)
```