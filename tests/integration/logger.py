"""
Integration tests for logging system

Testing que el sistema de logging funciona correctamente con Loguru
"""

import pytest
import os
from pathlib import Path
from io import StringIO
import sys


@pytest.mark.integration
class TestLoggerIntegration:
    """Integration tests for logger system functionality."""
    
    def test_logger_import_and_basic_functionality(self, capsys):
        """
        Test que falla - logger debe importarse y funcionar básicamente.
        
        Comportamiento esperado:
        - Logger se importa sin errores
        - Métodos de logging están disponibles
        - Output básico funciona
        """
        # Act - importar logger
        from src.utils.logger import info, error, success, debug, warning
        
        # Act - usar logger
        info("Test info message")
        success("Test success message")
        warning("Test warning message")
        
        # Assert - output capturado
        captured = capsys.readouterr()
        
        # Verificar que los mensajes aparecen en stderr (loguru default)
        assert "Test info message" in captured.err
        assert "Test success message" in captured.err  
        assert "Test warning message" in captured.err
    
    def test_logger_levels_integration(self, capsys):
        """
        Test que falla - diferentes niveles de log deben funcionar.
        """
        from src.utils.logger import trace, debug, info, success, warning, error, critical
        
        # Act - usar diferentes niveles
        debug("Debug message")
        info("Info message")
        success("Success message")
        warning("Warning message")
        error("Error message")
        critical("Critical message")
        
        # Assert - todos los niveles están presentes
        captured = capsys.readouterr()
        
        # Debug no aparece por defecto en tests
        assert "Info message" in captured.err
        assert "Success message" in captured.err
        assert "Warning message" in captured.err
        assert "Error message" in captured.err
        assert "Critical message" in captured.err
    
    def test_log_exception_integration(self, capsys):
        """
        Test que falla - log_exception debe capturar traceback automáticamente.
        """
        from src.utils.logger import log_exception
        
        # Act - crear excepción y loggearla
        try:
            raise ValueError("Test exception for logging")
        except Exception:
            log_exception("Test exception context")
        
        # Assert - traceback está en output
        captured = capsys.readouterr()
        
        assert "Test exception context" in captured.err
        assert "ValueError" in captured.err
        assert "Test exception for logging" in captured.err
        assert "Traceback" in captured.err
    
    def test_logger_context_functions_integration(self, capsys):
        """
        Test que falla - funciones de contexto deben funcionar.
        """
        from src.utils.logger import log_command_execution, log_file_operation, log_system_info
        
        # Act - usar funciones de contexto
        log_command_execution("test_command", {"arg1": "value1"})
        log_file_operation("read", "/path/to/file", "success")
        log_system_info("test_component", "Test message", {"extra": "data"})
        
        # Assert - mensajes de contexto están presentes
        captured = capsys.readouterr()
        
        assert "Executing command: test_command" in captured.err
        assert "File operation completed: read on /path/to/file" in captured.err
        assert "[test_component] Test message" in captured.err
    
    def test_logger_file_creation_integration(self):
        """
        Test que falla - logger debe crear archivos de log.
        """
        # Act - importar logger (esto debería crear archivos)
        from src.utils.logger import info
        
        info("Test message for file logging")
        
        # Assert - directorio logs existe
        logs_dir = Path("logs")
        assert logs_dir.exists(), "Logs directory should be created"
        
        # Assert - archivos de log existen
        log_files = list(logs_dir.glob("scli_*.log"))
        assert len(log_files) > 0, "Log files should be created"


@pytest.mark.integration
def test_logger_integration_with_main():
    """
    Integration test: logger + main.py working together.
    
    Verifica que main.py usa el logger correctamente.
    """
    from src.main import main
    
    # Act - ejecutar main con argumentos válidos
    result = main(["--test", "value"])
    
    # Assert - función completó exitosamente
    assert result == 0
    # El logging ya está integrado en main.py


@pytest.mark.integration 
def test_logger_configuration_integration():
    """
    Test que falla - configuración del logger debe ser correcta.
    """
    from src.utils.logger import get_logger
    
    # Act - obtener logger configurado
    logger_instance = get_logger()
    
    # Assert - logger está configurado
    assert logger_instance is not None
    
    # Verificar que tiene los métodos esperados
    assert hasattr(logger_instance, 'info')
    assert hasattr(logger_instance, 'error') 
    assert hasattr(logger_instance, 'success')
    assert hasattr(logger_instance, 'warning')
    assert hasattr(logger_instance, 'critical')
    assert hasattr(logger_instance, 'debug')