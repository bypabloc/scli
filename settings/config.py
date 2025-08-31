"""
Application configuration for SCLI project

Complete configuration management with environment-specific settings for CLI application.
"""

from typing import List

from src.utils.base_settings import BaseSettings


class AppConfig(BaseSettings):
    """
    Configuration for SCLI interactive CLI application with comprehensive settings.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Application configuration class.

    Examples
    --------
    >>> config = AppConfig()
    >>> config.environment
    'dev'
    
    >>> config.is_valid()
    True

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """

    # Environment Configuration
    environment: str = 'dev'
    debug_mode: bool = True
    testing: str = '0'

    # Logging Configuration
    log_level: str = 'INFO'
    log_file_enabled: bool = True
    log_console_enabled: bool = True
    log_format: str = '{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
    log_info_enabled: bool = True
    log_error_enabled: bool = True
    log_warning_enabled: bool = True
    log_debug_enabled: bool = True
    log_critical_enabled: bool = True

    # CLI Configuration
    max_args_length: int = 1000
    validate_named_flags_only: bool = True
    help_enabled: bool = True
    version: str = '1.0.0'
    output_format: str = 'table'  # json, table, simple

    # Spinner Configuration
    spinner_enabled: bool = True
    spinner_style: str = 'dots'
    spinner_speed: float = 0.1

    # Feature Flags
    interactive_mode_enabled: bool = True
    color_output_enabled: bool = True
    progress_bars_enabled: bool = True

    def load_environment(self, current_value: str) -> str:
        """
        Environment-specific validator that sets debug_mode based on environment.

        Parameters
        ----------
        current_value : str
            Current environment value.

        Returns
        -------
        str
            Validated environment value.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.environment = 'prod'
        >>> config.load_environment('prod')
        'prod'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        if current_value == 'prod':
            self.debug_mode = False
            self.log_level = 'WARNING'
            self.spinner_enabled = False
        elif current_value == 'dev':
            self.debug_mode = True
            self.log_level = 'DEBUG'
            self.spinner_enabled = True
        elif current_value == 'test':
            self.debug_mode = False
            self.log_level = 'ERROR'
            self.spinner_enabled = False
            self.log_file_enabled = False
        
        return current_value

    def load_debug_mode(self, current_value: bool) -> bool:
        """
        Debug mode validator that adjusts related settings.

        Parameters
        ----------
        current_value : bool
            Current debug mode value.

        Returns
        -------
        bool
            Validated debug mode value.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.load_debug_mode(True)
        True

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        if current_value:
            self.log_debug_enabled = True
        else:
            self.log_debug_enabled = False
        
        return current_value

    def load_log_level(self, current_value: str) -> str:
        """
        Log level validator that ensures valid logging level.

        Parameters
        ----------
        current_value : str
            Current log level value.

        Returns
        -------
        str
            Validated log level value.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.load_log_level('INFO')
        'INFO'

        >>> config.load_log_level('INVALID')
        'INFO'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if current_value.upper() in valid_levels:
            return current_value.upper()
        
        # Default to INFO if invalid level provided
        return 'INFO'

    def load_output_format(self, current_value: str) -> str:
        """
        Output format validator that ensures valid format.

        Parameters
        ----------
        current_value : str
            Current output format value.

        Returns
        -------
        str
            Validated output format value.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.load_output_format('json')
        'json'

        >>> config.load_output_format('invalid')
        'table'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        valid_formats = ['json', 'table', 'simple']
        
        if current_value.lower() in valid_formats:
            return current_value.lower()
        
        # Default to table if invalid format provided
        return 'table'

    def load_spinner_style(self, current_value: str) -> str:
        """
        Spinner style validator that ensures valid spinner type.

        Parameters
        ----------
        current_value : str
            Current spinner style value.

        Returns
        -------
        str
            Validated spinner style value.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.load_spinner_style('dots')
        'dots'

        >>> config.load_spinner_style('invalid')
        'dots'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        valid_styles = ['dots', 'line', 'pipe', 'simpleDots', 'simpleDotsScrolling']
        
        if current_value in valid_styles:
            return current_value
        
        # Default to dots if invalid style provided
        return 'dots'

    def is_testing(self) -> bool:
        """
        Detect if code is running in testing mode.

        Parameters
        ----------
        self : AppConfig
            Instance of AppConfig class.

        Returns
        -------
        bool
            True if in testing mode, False otherwise.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.testing = '1'
        >>> config.is_testing()
        True

        >>> config.testing = '0'
        >>> config.is_testing()
        False

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        return self.testing == '1'

    def is_test_environment(self) -> bool:
        """
        Detect if running in test environment.

        Parameters
        ----------
        self : AppConfig
            Instance of AppConfig class.

        Returns
        -------
        bool
            True if in test environment, False otherwise.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.environment = 'test'
        >>> config.is_test_environment()
        True

        >>> config.environment = 'prod'
        >>> config.is_test_environment()
        False

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        # Check for explicit TESTING environment variable first
        if self.testing == '1':
            return True

        # Check if environment contains 'test'
        if self.environment and 'test' in self.environment.lower():
            return True

        return False

    def is_production(self) -> bool:
        """
        Detect if running in production environment.

        Parameters
        ----------
        self : AppConfig
            Instance of AppConfig class.

        Returns
        -------
        bool
            True if in production environment, False otherwise.

        Examples
        --------
        >>> config = AppConfig()
        >>> config.environment = 'prod'
        >>> config.is_production()
        True

        >>> config.environment = 'dev'
        >>> config.is_production()
        False

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        return self.environment == 'prod'

    def get_log_configuration(self) -> dict:
        """
        Get complete logging configuration as dictionary.

        Parameters
        ----------
        self : AppConfig
            Instance of AppConfig class.

        Returns
        -------
        dict
            Complete logging configuration.

        Examples
        --------
        >>> config = AppConfig()
        >>> log_config = config.get_log_configuration()
        >>> 'level' in log_config
        True
        >>> 'format' in log_config
        True

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        return {
            'level': self.log_level,
            'file_enabled': self.log_file_enabled,
            'console_enabled': self.log_console_enabled,
            'format': self.log_format,
            'info_enabled': self.log_info_enabled,
            'error_enabled': self.log_error_enabled,
            'warning_enabled': self.log_warning_enabled,
            'debug_enabled': self.log_debug_enabled,
            'critical_enabled': self.log_critical_enabled
        }

    def get_spinner_configuration(self) -> dict:
        """
        Get complete spinner configuration as dictionary.

        Parameters
        ----------
        self : AppConfig
            Instance of AppConfig class.

        Returns
        -------
        dict
            Complete spinner configuration.

        Examples
        --------
        >>> config = AppConfig()
        >>> spinner_config = config.get_spinner_configuration()
        >>> 'enabled' in spinner_config
        True
        >>> 'style' in spinner_config
        True

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        return {
            'enabled': self.spinner_enabled,
            'style': self.spinner_style,
            'speed': self.spinner_speed
        }

    def get_cli_configuration(self) -> dict:
        """
        Get complete CLI configuration as dictionary.

        Parameters
        ----------
        self : AppConfig
            Instance of AppConfig class.

        Returns
        -------
        dict
            Complete CLI configuration.

        Examples
        --------
        >>> config = AppConfig()
        >>> cli_config = config.get_cli_configuration()
        >>> 'max_args_length' in cli_config
        True
        >>> 'validate_named_flags_only' in cli_config
        True

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        return {
            'max_args_length': self.max_args_length,
            'validate_named_flags_only': self.validate_named_flags_only,
            'help_enabled': self.help_enabled,
            'version': self.version,
            'output_format': self.output_format,
            'interactive_mode_enabled': self.interactive_mode_enabled,
            'color_output_enabled': self.color_output_enabled,
            'progress_bars_enabled': self.progress_bars_enabled
        }


# Global configuration instance
app_config = AppConfig()
