"""
Integration tests for BaseSettings utility system

Testing que el sistema de configuración base funciona correctamente
"""

import pytest
import os
from typing import List


@pytest.mark.integration
class TestBaseSettingsIntegration:
    """Integration tests for BaseSettings system functionality."""
    
    def test_base_settings_import_and_basic_functionality(self):
        """
        Test que falla - BaseSettings debe importarse y funcionar básicamente.
        
        Comportamiento esperado:
        - BaseSettings se importa sin errores
        - Se puede crear una clase que herede de BaseSettings
        - Variables de entorno se cargan automáticamente
        """
        # Act - importar BaseSettings
        from src.utils.base_settings import BaseSettings
        
        # Act - crear clase de configuración de prueba
        class TestConfig(BaseSettings):
            test_field: str = 'default_value'
            test_int: int = 42
            test_list: List[str] = ['item1', 'item2']
        
        # Act - crear instancia
        config = TestConfig()
        
        # Assert - campos están presentes
        assert hasattr(config, 'test_field')
        assert hasattr(config, 'test_int')
        assert hasattr(config, 'test_list')
        assert config.test_field == 'default_value'
        assert config.test_int == 42
        assert config.test_list == ['item1', 'item2']
    
    def test_environment_variable_loading_integration(self):
        """
        Test que falla - variables de entorno deben cargarse automáticamente.
        """
        from src.utils.base_settings import BaseSettings
        
        # Arrange - establecer variables de entorno
        os.environ['TEST_FIELD'] = 'env_value'
        os.environ['TEST_INT'] = '123'
        os.environ['TEST_LIST'] = 'a, b, c'
        
        try:
            # Act - crear clase de configuración
            class TestConfig(BaseSettings):
                test_field: str = 'default_value'
                test_int: int = 42
                test_list: List[str] = ['default1', 'default2']
            
            # Act - crear instancia (debe cargar env vars)
            config = TestConfig()
            
            # Assert - env vars sobrescriben defaults
            assert config.test_field == 'env_value'
            assert config.test_int == 123
            assert config.test_list == ['a', 'b', 'c']
            
        finally:
            # Clean up
            del os.environ['TEST_FIELD']
            del os.environ['TEST_INT']
            del os.environ['TEST_LIST']
    
    def test_custom_validators_integration(self):
        """
        Test que falla - validadores personalizados deben ejecutarse.
        """
        from src.utils.base_settings import BaseSettings
        
        # Act - crear clase con validador personalizado
        class TestConfig(BaseSettings):
            test_field: str = 'default'
            
            def load_test_field(self, current_value: str) -> str:
                """Validador personalizado que convierte a mayúsculas."""
                return current_value.upper()
        
        # Act - crear instancia
        config = TestConfig()
        
        # Assert - validador se ejecutó
        assert config.test_field == 'DEFAULT'
    
    def test_validation_method_integration(self):
        """
        Test que falla - método validate debe funcionar.
        """
        from src.utils.base_settings import BaseSettings
        
        # Act - usar método validate
        def uppercase_validator(value: str) -> str:
            return value.upper()
        
        result = BaseSettings.validate(uppercase_validator, 'test')
        
        # Assert - validación funcionó
        assert result == 'TEST'
    
    def test_is_valid_method_integration(self):
        """
        Test que falla - método is_valid debe validar configuración.
        """
        from src.utils.base_settings import BaseSettings
        
        # Act - crear configuración válida
        class ValidConfig(BaseSettings):
            required_field: str = 'value'
            optional_field: int = 42
        
        valid_config = ValidConfig()
        
        # Assert - configuración es válida
        assert valid_config.is_valid() is True
        
        # Act - crear configuración inválida
        class InvalidConfig(BaseSettings):
            required_field: str = ''  # Campo vacío
        
        invalid_config = InvalidConfig()
        
        # Assert - configuración es inválida
        assert invalid_config.is_valid() is False
    
    def test_to_json_method_integration(self):
        """
        Test que falla - método to_json debe convertir a JSON.
        """
        from src.utils.base_settings import BaseSettings
        
        # Act - crear configuración
        class TestConfig(BaseSettings):
            test_field: str = 'value'
            test_int: int = 123
        
        config = TestConfig()
        
        # Act - convertir a JSON
        json_data = config.to_json()
        
        # Assert - JSON contiene los campos
        assert isinstance(json_data, dict)
        assert json_data['test_field'] == 'value'
        assert json_data['test_int'] == 123


@pytest.mark.integration
def test_base_settings_integration_with_logger():
    """
    Integration test: BaseSettings + logger working together.
    
    Verifica que BaseSettings puede usar el logger correctamente.
    """
    from src.utils.base_settings import BaseSettings
    from src.utils.logger import info
    
    # Act - crear configuración que use logger
    class LoggedConfig(BaseSettings):
        test_field: str = 'default'
        
        def load_test_field(self, current_value: str) -> str:
            info("Loading test_field configuration")
            return current_value.upper()
    
    # Act - crear instancia (debe loggear)
    config = LoggedConfig()
    
    # Assert - configuración funcionó
    assert config.test_field == 'DEFAULT'