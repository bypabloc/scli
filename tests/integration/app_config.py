"""
Integration tests for AppConfig settings system

Testing que el sistema de configuración de aplicación funciona correctamente
"""

import pytest
import os
from typing import List


@pytest.mark.integration
class TestAppConfigIntegration:
    """Integration tests for AppConfig system functionality."""
    
    def test_app_config_import_and_basic_functionality(self):
        """
        Test que falla - AppConfig debe importarse y funcionar básicamente.
        
        Comportamiento esperado:
        - AppConfig se importa sin errores
        - Tiene configuraciones específicas para SCLI
        - Configuración por defecto está presente
        """
        # Act - importar AppConfig
        from src.settings.config import AppConfig, app_config
        
        # Assert - configuración está disponible
        assert isinstance(app_config, AppConfig)
        
        # Assert - campos básicos están presentes
        assert hasattr(app_config, 'environment')
        assert hasattr(app_config, 'debug_mode')
        assert hasattr(app_config, 'log_level')
        assert hasattr(app_config, 'output_format')
        
        # Assert - valores por defecto
        assert app_config.environment in ['dev', 'test', 'prod']
        assert isinstance(app_config.debug_mode, bool)
        assert app_config.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert app_config.output_format in ['json', 'table', 'simple']
    
    def test_app_config_environment_loading_integration(self):
        """
        Test que falla - AppConfig debe cargar variables de entorno específicas.
        """
        from src.settings.config import AppConfig
        
        # Arrange - establecer variables de entorno específicas
        os.environ['ENVIRONMENT'] = 'prod'
        os.environ['DEBUG_MODE'] = 'true'
        os.environ['LOG_LEVEL'] = 'ERROR'
        os.environ['OUTPUT_FORMAT'] = 'json'
        
        try:
            # Act - crear nueva instancia de configuración
            config = AppConfig()
            
            # Assert - env vars se cargaron correctamente
            assert config.environment == 'prod'
            assert config.debug_mode is True
            assert config.log_level == 'ERROR'
            assert config.output_format == 'json'
            
        finally:
            # Clean up
            for env_var in ['ENVIRONMENT', 'DEBUG_MODE', 'LOG_LEVEL', 'OUTPUT_FORMAT']:
                if env_var in os.environ:
                    del os.environ[env_var]
    
    def test_app_config_spinner_configuration_integration(self):
        """
        Test que falla - AppConfig debe tener configuración para spinners.
        """
        from src.settings.config import app_config
        
        # Assert - configuración de spinner está presente
        assert hasattr(app_config, 'spinner_enabled')
        assert hasattr(app_config, 'spinner_style')
        assert hasattr(app_config, 'spinner_speed')
        
        # Assert - valores por defecto razonables
        assert isinstance(app_config.spinner_enabled, bool)
        assert isinstance(app_config.spinner_style, str)
        assert isinstance(app_config.spinner_speed, (int, float))
        assert app_config.spinner_speed > 0
    
    def test_app_config_logging_configuration_integration(self):
        """
        Test que falla - AppConfig debe tener configuración completa de logging.
        """
        from src.settings.config import app_config
        
        # Assert - configuración de logging está presente
        assert hasattr(app_config, 'log_level')
        assert hasattr(app_config, 'log_file_enabled')
        assert hasattr(app_config, 'log_console_enabled')
        assert hasattr(app_config, 'log_format')
        
        # Assert - valores por defecto
        assert app_config.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert isinstance(app_config.log_file_enabled, bool)
        assert isinstance(app_config.log_console_enabled, bool)
        assert isinstance(app_config.log_format, str)
        assert len(app_config.log_format) > 0
    
    def test_app_config_cli_configuration_integration(self):
        """
        Test que falla - AppConfig debe tener configuración para CLI.
        """
        from src.settings.config import app_config
        
        # Assert - configuración CLI está presente
        assert hasattr(app_config, 'max_args_length')
        assert hasattr(app_config, 'validate_named_flags_only')
        assert hasattr(app_config, 'help_enabled')
        assert hasattr(app_config, 'version')
        
        # Assert - valores por defecto
        assert isinstance(app_config.max_args_length, int)
        assert app_config.max_args_length > 0
        assert isinstance(app_config.validate_named_flags_only, bool)
        assert isinstance(app_config.help_enabled, bool)
        assert isinstance(app_config.version, str)
        assert len(app_config.version) > 0
    
    def test_app_config_validation_integration(self):
        """
        Test que falla - AppConfig debe validar configuración correctamente.
        """
        from src.settings.config import app_config
        
        # Act - validar configuración
        is_valid = app_config.is_valid()
        
        # Assert - configuración es válida
        assert is_valid is True
        
        # Act - obtener JSON
        json_data = app_config.to_json()
        
        # Assert - JSON contiene campos esperados
        assert isinstance(json_data, dict)
        assert 'environment' in json_data
        assert 'log_level' in json_data
        assert 'output_format' in json_data
    
    def test_app_config_environment_specific_validation(self):
        """
        Test que falla - AppConfig debe tener validaciones específicas por ambiente.
        """
        from src.settings.config import AppConfig
        
        # Test para ambiente de desarrollo
        os.environ['ENVIRONMENT'] = 'dev'
        try:
            dev_config = AppConfig()
            assert dev_config.environment == 'dev'
            # En desarrollo, debug debería estar habilitado por defecto
            assert dev_config.debug_mode is True
        finally:
            if 'ENVIRONMENT' in os.environ:
                del os.environ['ENVIRONMENT']
        
        # Test para ambiente de producción
        os.environ['ENVIRONMENT'] = 'prod'
        try:
            prod_config = AppConfig()
            assert prod_config.environment == 'prod'
            # En producción, debug debería estar deshabilitado por defecto
            assert prod_config.debug_mode is False
        finally:
            if 'ENVIRONMENT' in os.environ:
                del os.environ['ENVIRONMENT']


@pytest.mark.integration
def test_app_config_integration_with_logger():
    """
    Integration test: AppConfig + logger working together.
    
    Verifica que AppConfig puede configurar el logger correctamente.
    """
    from src.settings.config import app_config
    from src.utils.logger import info
    
    # Act - usar configuración con logger
    info("Testing AppConfig integration", detail={
        "environment": app_config.environment,
        "log_level": app_config.log_level,
        "debug_mode": app_config.debug_mode
    })
    
    # Assert - configuración está disponible
    assert app_config is not None
    assert hasattr(app_config, 'log_level')


@pytest.mark.integration 
def test_app_config_integration_with_spinner():
    """
    Integration test: AppConfig + spinner working together.
    
    Verifica que AppConfig puede configurar spinners correctamente.
    """
    from src.settings.config import app_config
    from src.utils.spinner import create_spinner
    
    # Act - usar configuración para crear spinner
    spinner = create_spinner(
        "Testing config integration",
        style=app_config.spinner_style,
        speed=app_config.spinner_speed
    )
    
    # Assert - spinner se creó con configuración
    assert spinner is not None
    assert app_config.spinner_enabled is not None