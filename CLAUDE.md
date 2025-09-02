# CLAUDE.md - SCLI Project Context

> **2025 Best Practices**: This file provides complete context for Claude Code development. All instructions here take priority over general prompts.

## 🚀 Project Overview

**SCLI** is an **interactive CLI application** built with modern Python practices, featuring dynamic spinners, argument validation, and comprehensive logging. This is a production-ready CLI tool focused on user experience and code quality.

---

## 📋 Tech Stack & Versions

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12+ | Core runtime (required) |
| **uv** | Latest | Package manager & virtual environment |
| **Loguru** | ≥0.7.3 | Advanced logging with colors & formatting |
| **Rich** | ≥14.1.0 | Terminal UI components |
| **Survey** | ≥5.4.2 | Interactive CLI prompts |
| **Typer** | ≥0.17.3 | CLI framework |
| **pytest** | ≥8.4.1 | Testing framework (dev) |

---

## 🏗️ Project Architecture

### Directory Structure
```
scli/
├── src/                      # Source code (ALL business logic MUST be here)
│   ├── main.py              # Entry point (MINIMAL - delegates to utils)
│   ├── settings/            # Application configuration (REQUIRED)
│   │   ├── __init__.py      # Settings package init
│   │   └── config.py        # AppConfig class with app_config instance
│   └── utils/               # Business logic (ALL functions here)
│       ├── base_settings.py # Configuration base class
│       ├── logger.py        # Centralized logging with Loguru
│       ├── argument_parser.py # Named flags validation
│       ├── spinner.py       # Dynamic loading indicators
│       └── docstring_generator.py # Auto docstring creation
├── tests/                   # Testing (NO unit tests - integration + e2e only)
│   ├── integration/         # Integration tests (70%)
│   └── e2e/                 # End-to-end tests (30%)
├── pyproject.toml          # Project configuration
└── CLAUDE.md              # This file
```

### Architecture Principles
1. **src/ containment**: ALL business logic MUST be inside `src/` folder, NEVER outside
2. **utils/ pattern**: ALL reusable functions go in `src/utils/`
3. **settings/ pattern**: ALL configuration MUST be in `src/settings/config.py`
4. **Centralized config**: Use `app_config` instance from `src.settings.config`
5. **Minimal main.py**: Entry point only, no business logic
6. **No unit tests**: Only integration (70%) and e2e (30%) tests
7. **TDD mandatory**: Test-first development always

---

## 🔧 Essential Commands

### Development Workflow
```bash
# Setup (first time)
uv sync                      # Install dependencies & create .venv

# Daily development
uv run scli [--flags]        # Run application
uv run python -c "from src.utils.logger import logger; logger.info('test')"  # Test utils

# Testing
python tests/run.py          # Run all tests (integration + e2e)
python tests/run.py --integration  # Integration tests only
python tests/run.py --e2e    # E2E tests only
python tests/run.py --fast   # Exclude slow tests
python tests/run.py --coverage # Run with coverage report

# Git workflow
git config --global user.name   # Check author (used in docstrings)
date +%Y-%m-%d                  # Current date for docstrings
```

### Package Management
```bash
uv add [package]             # Add production dependency
uv add --dev [package]       # Add development dependency  
uv remove [package]          # Remove dependency
uv tree                      # Show dependency tree
```

---

## 🎯 Development Rules & Context

### 1. 🚨 MANDATORY TDD Workflow
```
1. Write failing test FIRST (Red)
2. Write minimal code to pass (Green)  
3. Refactor and improve (Refactor)
4. NEVER skip this cycle
```

### 2. Import Organization (STRICT)
```python
# ALWAYS use this 3-section structure (no comments):
from sys import argv as sys_argv
from typing import List

from django.contrib.auth.models import User
from third_party_package import something

from src.utils.logger import logger
from src.utils.argument_parser import validate_named_flags_only
from src.settings.config import app_config
```

**Rules:**
- ✅ 3 sections: Native → Third-party → Project files
- ✅ Blank lines between sections
- ✅ **CONSISTENT PROJECT IMPORTS**: ALWAYS use `from src.utils.logger import logger` for project imports
- ✅ **SPECIFIC IMPORTS ONLY**: `from typing import Dict` not `import typing`
- ✅ **FORBIDDEN GENERAL IMPORTS**: `import sys` → use `from sys import argv as sys_argv`
- ✅ **ALIAS PATTERN**: `<from>_<import>` → `from sys import argv as sys_argv`
- ✅ **ONE IMPORT PER LINE**: `from threading import Thread as threading_Thread\nfrom threading import Event as threading_Event`
- ✅ **FORBIDDEN MULTIPLE IMPORTS**: `from typing import Optional, List` → use separate lines
- ✅ **IMPORTS ONLY AT TOP**: ALL imports MUST be at the beginning of the file
- ❌ NO section comments
- ❌ NO mixing imports from different categories
- ❌ **STRICTLY FORBIDDEN**: Inline imports within functions or conditional blocks
- ❌ **NEVER** use general imports like `import sys`, `import os`, `import json`
- ❌ **NEVER** use multiple imports on one line like `from typing import Optional, List`

### 3. Logger Format (ENFORCED)
```python
# ✅ CORRECT - Plain string + detail dict
logger.info("User logged in", detail={"user_id": user_id, "timestamp": now})
logger.error("Database connection failed", detail={"host": host, "port": port})

# ❌ FORBIDDEN - f-strings or b-strings  
logger.info(f"User {user_id} logged in")  # Will raise ValueError
```

**Logger Rules:**
- ✅ First argument: Plain string only
- ✅ Second argument: `detail` dict (optional, not printed)
- ✅ Use: `logger.info()`, `logger.success()`, `logger.error()`, `logger.critical()`
- ❌ NEVER use `print()` - always use logger
- ❌ NEVER use `as e` in except blocks - use `logger.critical()`

### 4. Docstring Requirements (MANDATORY)
```python
def example_function(param: str) -> Dict:
    """
    Brief description of what the function does.

    Parameters
    ----------
    param : str
        Description of the parameter

    Returns
    -------
    Dict
        Description of return value

    Examples
    --------
    >>> example_function("test")
    {'result': 'processed'}
    
    >>> example_function("")
    {'result': 'empty'}

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
```

**Docstring Rules:**
- ✅ ALL functions, methods, and classes MUST have docstrings
- ✅ Use `git config --global user.name` for author (Pablo Contreras)
- ✅ Use current date for :Created: (`date +%Y-%m-%d`)
- ✅ Include Examples section with doctests
- ✅ Update :Updated: date when modifying function I/O
- ✅ Examples must reflect current functionality
- ❌ **FORBIDDEN**: File-level docstrings at the beginning of files
- ❌ **NEVER** add docstrings as the first lines of `.py` files

### 5. Argument Validation (STRICT)
```python
# ✅ CORRECT - Named flags only
scli --test value --flag
scli --option1 value1 --option2

# ❌ FORBIDDEN - Positional arguments
scli command value           # Will be rejected
scli --flag value extra      # Will be rejected
```

### 6. Configuration Management (MANDATORY)
```python
# ✅ CORRECT - Use centralized config
from src.settings.config import app_config

# Access configuration values
environment = app_config.environment
log_level = app_config.log_level
spinner_enabled = app_config.spinner_enabled

# Check configuration status
if app_config.is_production():
    # Production-specific logic
    pass

# ❌ FORBIDDEN - Direct environment access
import os
value = os.environ.get('SOME_VAR')  # DON'T DO THIS

# ❌ FORBIDDEN - Hardcoded values
MAX_RETRIES = 3  # Should be app_config.max_retries
```

**Configuration Rules:**
- ✅ ALL environment variables and config MUST be defined in `src/settings/config.py`
- ✅ Use `app_config` instance for accessing configuration
- ✅ Each config field MUST have a default value
- ✅ Environment variables override defaults (e.g., `LOG_LEVEL` env var → `app_config.log_level`)
- ✅ Use type annotations for all config fields
- ✅ Add validation methods using `load_{field_name}` pattern
- ✅ Import config: `from src.settings.config import app_config`
- ❌ NEVER access `os.environ` directly in business logic
- ❌ NEVER hardcode configuration values in code
- ❌ NEVER create config outside `src/settings/`

**Config Pattern Example:**
```python
# In src/settings/config.py
class AppConfig(BaseSettings):
    # Field with default value and type annotation
    max_retries: int = 3  # Can be overridden by MAX_RETRIES env var
    
    def load_max_retries(self, current_value: int) -> int:
        """Validate max_retries is positive."""
        return max(1, current_value)

# Global instance for import
app_config = AppConfig()
```

---

## 🔄 Git Workflow & Repository Etiquette

### Branch Naming Convention
```bash
# Feature development
feature/add-spinner-utility
feature/refactor-logger-validation

# Bug fixes  
fix/argument-parser-validation
fix/logger-format-issues

# Refactoring
refactor/move-functions-to-utils
refactor/improve-docstring-format
```

### Commit Standards
```bash
# Use conventional commits
feat(core): add dynamic spinner with morphing text
fix(logger): resolve f-string validation error
docs(claude): update import organization rules
refactor(utils): move argument parsing to utils module

# Auto-generated suffix (required)
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Merge Strategy
- ✅ **Prefer merge commits** over rebase for feature branches
- ✅ Squash commits only for small, single-purpose changes
- ✅ Always run tests before merging: `python tests/run.py`

---

## 📁 File Context & Access Rules

### Files Claude CAN Read
```
✅ src/main.py                 # Entry point
✅ src/settings/*.py           # Application configuration
✅ src/utils/*.py              # All utility modules  
✅ tests/integration/*.py      # Integration tests
✅ tests/e2e/*.py             # E2E tests
✅ tests/run.py               # Test runner
✅ pyproject.toml             # Project config
✅ README.md                  # User documentation
✅ CLAUDE.md                  # This context file
```

### Files Claude Should AVOID
```
❌ .venv/                     # Virtual environment
❌ __pycache__/               # Python cache
❌ .git/                      # Git internals
❌ logs/                      # Log files (if created)
```

---

## 🧪 Testing Philosophy

### Core Principles
1. **NO unit tests** - They create mocking that damages code quality
2. **Integration tests (70%)** - Test components working together
3. **E2E tests (30%)** - Test complete user workflows
4. **Test real behavior** - No mocks, no isolated function tests

### Test Structure
```python
# Integration test example
def test_argument_validation_integration():
    """Test argument parser with logger integration."""
    # Test real interaction between components
    
# E2E test example  
def test_complete_user_workflow():
    """Test full CLI usage from user perspective."""
    # Test complete user journey
```

### Test Execution
```bash
# Primary test command
python tests/run.py                    # All tests

# Specific test types
python tests/run.py --integration     # Component integration
python tests/run.py --e2e             # End-to-end workflows
python tests/run.py --fast            # Exclude @pytest.mark.slow
python tests/run.py --coverage        # With coverage report
```

---

## 🚨 Critical Instructions for Claude

### When Making Changes
1. **Always check imports** - Ensure 3-section organization
2. **Update docstrings** - When function I/O changes  
3. **Run tests** - `python tests/run.py` before completing tasks
4. **Follow TDD** - Write failing test first, then implementation
5. **Use utils/ pattern** - Move reusable code to utils modules
6. **Check src/ containment** - ALL business logic must be inside `src/`
7. **Use app_config** - For any environment variables or configuration

### When Encountering Errors
1. **Check logger validation** - Ensure plain strings only
2. **Verify imports** - Check section organization and naming
3. **Test environment** - Run `uv sync` if dependency issues
4. **Review CLAUDE.md** - This file contains the source of truth

### Communication Style
- ✅ Be concise and direct (< 4 lines unless detail requested)
- ✅ Focus on specific user requests only
- ✅ Provide code examples when helpful
- ❌ Avoid unnecessary preambles or explanations
- ❌ Don't add extra context unless asked

---

## 📊 Quality Checklist

Before completing any task, verify:

- [ ] **🚨 TDD**: Failing test written BEFORE implementation
- [ ] **Tests pass**: `python tests/run.py` successful
- [ ] **Imports organized**: 3-section structure (Native → Third-party → Project)
- [ ] **Logger format**: Plain strings + detail dict only
- [ ] **Docstrings current**: Match function I/O, include Examples
- [ ] **src/ containment**: ALL business logic inside `src/` folder
- [ ] **Configuration centralized**: Use `app_config` from `src.settings.config`
- [ ] **Utils architecture**: Reusable functions in `src/utils/`
- [ ] **No print() statements**: Use logger instead
- [ ] **Named flags only**: CLI arguments validated
- [ ] **Code follows patterns**: Consistent with existing codebase

---

## 🔍 Context Summary

**Project Type**: Interactive CLI application with modern Python practices  
**Architecture**: utils/ pattern with minimal main.py entry point  
**Testing**: Integration + E2E only (no unit tests)  
**Development**: Strict TDD workflow with comprehensive logging  
**Key Features**: Dynamic spinners, argument validation, structured logging  

**Current Focus**: Building robust CLI utilities with excellent developer experience and user interface.

---

*Last Updated: 2025-08-30*  
*Version: 2.0 (2025 Best Practices Edition)*