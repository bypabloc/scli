"""
Integration tests for argument validation system

Testing que todos los argumentos deben ser named flags obligatorios
"""

import pytest
from src.main import main


@pytest.mark.integration
class TestArgumentValidation:
    """Integration tests for named flags validation."""
    
    def test_positional_arguments_should_fail_with_error_message(self):
        """
        Test que falla - argumentos posicionales deben ser rechazados.
        
        Comportamiento esperado:
        - scli asd → exit code 1 + mensaje de error
        - scli comando arg → exit code 1 + mensaje de error  
        """
        # Test cases con argumentos posicionales (no permitidos)
        invalid_cases = [
            ["asd"],                    # Un argumento posicional
            ["comando", "arg"],         # Múltiples argumentos posicionales
            ["help"],                   # Comando sin --
            ["file.txt", "process"]     # Argumentos mixtos posicionales
        ]
        
        for args in invalid_cases:
            # Act - debe fallar con exit code 1
            result = main(args)
            
            # Assert - debe retornar error (no 0)
            assert result == 1, f"Args {args} deberían fallar pero retornaron {result}"
    
    def test_named_flags_should_succeed(self):
        """
        Test que falla - named flags deben ser aceptados.
        
        Comportamiento esperado:
        - scli --help → exit code 0
        - scli --file valor → exit code 0
        - scli --verbose --output file → exit code 0
        """
        # Test cases con named flags (permitidos)
        valid_cases = [
            ["--help"],                      # Flag simple
            ["--file", "example.txt"],       # Flag con valor
            ["--verbose", "--output", "result.txt"],  # Múltiples flags
            []                               # Sin argumentos es válido
        ]
        
        for args in valid_cases:
            # Act - debe funcionar con exit code 0
            result = main(args)
            
            # Assert - debe retornar éxito
            assert result == 0, f"Args {args} deberían funcionar pero retornaron {result}"
    
    def test_mixed_positional_and_flags_should_fail(self):
        """
        Test que falla - mezclar posicionales con flags debe fallar.
        
        Comportamiento esperado:
        - scli archivo --verbose → exit code 1 (posicional + flag)
        - scli --file val comando → exit code 1 (flag + posicional)
        """
        # Test cases con argumentos mixtos (no permitidos)
        mixed_cases = [
            ["archivo", "--verbose"],        # Posicional + flag
            ["--file", "val", "comando"]     # Flag + valor + posicional
        ]
        
        for args in mixed_cases:
            # Act - debe fallar
            result = main(args)
            
            # Assert - debe retornar error
            assert result == 1, f"Mixed args {args} deberían fallar pero retornaron {result}"


@pytest.mark.integration
class TestArgumentParsing:
    """Integration tests for argument parsing to dict."""
    
    def test_named_flags_should_be_converted_to_dict(self, capsys):
        """
        Test que falla - argumentos nombrados deben convertirse a dict.
        
        Comportamiento esperado:
        - scli --test asd → debe imprimir {'test': 'asd'}
        - scli --verbose --output file.txt → debe imprimir {'verbose': True, 'output': 'file.txt'}
        """
        # Test case: flag con valor
        result = main(["--test", "asd"])
        captured = capsys.readouterr()
        
        # Assert - debe mostrar dict en output
        assert "{'test': 'asd'}" in captured.out, f"Output should contain dict format, got: {captured.out}"
        assert result == 0
        
        # Test case: múltiples flags
        result = main(["--verbose", "--output", "file.txt"])  
        captured = capsys.readouterr()
        
        # Assert - debe mostrar dict con múltiples valores
        assert "'verbose': True" in captured.out
        assert "'output': 'file.txt'" in captured.out
        assert result == 0


@pytest.mark.integration
def test_argument_validation_integration_with_help_system():
    """
    Integration test: validación + sistema de ayuda.
    
    Cuando hay argumentos inválidos, debe mostrar ayuda automáticamente.
    """
    # Este test verifica que el sistema de validación 
    # se integra correctamente con el sistema de ayuda
    
    # Act - argumento posicional inválido
    result = main(["invalid_command"])
    
    # Assert - debe fallar y activar help
    assert result == 1
    # En el futuro, aquí verificaríamos que se muestra mensaje de ayuda