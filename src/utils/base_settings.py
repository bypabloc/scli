"""
BaseSettings utility for configuration management

Provides base functionality for loading environment variables and validating configuration fields.
"""

from json import dumps as json_dumps
from json import loads as json_loads
from os import environ as os_environ
from typing import Any
from typing import List
from typing import Type


class BaseSettings:
    """
    Base class for configuration management with environment variable loading and field validation.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Base configuration class for environment variable loading.

    Examples
    --------
    >>> class MyConfig(BaseSettings):
    ...     field_name: str = 'default_value'
    >>> config = MyConfig()
    >>> config.field_name
    'default_value'

    >>> import os
    >>> os.environ['FIELD_NAME'] = 'env_value'
    >>> config = MyConfig()
    >>> config.field_name
    'env_value'

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """

    def __init__(self):
        """
        Initialize configuration by loading environment variables.

        Parameters
        ----------
        self : BaseSettings
            Instance of BaseSettings class.

        Returns
        -------
        None
            Method for initializing configuration.

        Examples
        --------
        >>> config = BaseSettings()
        >>> hasattr(config, '_load_env_variables')
        True

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        self._load_env_variables()

    def _load_env_variables(self):
        """
        Load environment variables as instance attributes.
        
        First applies automatic environment variable loading,
        then executes specific validators if they are defined.

        Parameters
        ----------
        self : BaseSettings
            Instance of BaseSettings class.

        Returns
        -------
        None
            Method for loading environment variables.

        Examples
        --------
        >>> import os
        >>> os.environ['TEST_FIELD'] = 'test_value'
        >>> class TestConfig(BaseSettings):
        ...     test_field: str = 'default'
        >>> config = TestConfig()
        >>> config.test_field
        'test_value'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        for field_name, field_type in self.__annotations__.items():
            # Try loading from environment variable with uppercase field name
            env_value = os_environ.get(field_name.upper())

            if env_value is not None:
                if field_type is str:
                    setattr(self, field_name, env_value)
                elif field_type is int:
                    try:
                        setattr(self, field_name, int(env_value))
                    except ValueError:
                        # Skip logging to avoid import circular dependency
                        pass
                elif field_type is bool:
                    setattr(self, field_name, env_value.lower() in ('true', '1', 'yes', 'on'))
                elif field_type is float:
                    try:
                        setattr(self, field_name, float(env_value))
                    except ValueError:
                        # Skip logging to avoid import circular dependency
                        pass
                elif field_type is List[str]:
                    setattr(self, field_name, env_value.split(', '))
            else:
                # If no environment value, keep default value if exists
                if hasattr(self, field_name):
                    setattr(self, field_name, getattr(self, field_name))

        # Execute specific validators after automatic loading
        self._apply_custom_validators()

    def _apply_custom_validators(self):
        """
        Apply specific validators defined in the class.
        
        Specific validators can override automatically loaded values.

        Parameters
        ----------
        self : BaseSettings
            Instance of BaseSettings class.

        Returns
        -------
        None
            Method for applying custom validators.

        Examples
        --------
        >>> class TestConfig(BaseSettings):
        ...     test_field: str = 'default'
        ...     def load_test_field(self, current_value: str) -> str:
        ...         return current_value.upper()
        >>> config = TestConfig()
        >>> config.test_field
        'DEFAULT'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        # Search for methods that follow the load_{field_name} pattern
        for method_name in dir(self):
            if method_name.startswith('load_') and callable(getattr(self, method_name)):
                field_name = method_name[5:]  # Remove 'load_' prefix
                if hasattr(self, field_name):
                    current_value = getattr(self, field_name)
                    validator_method = getattr(self, method_name)
                    # Execute specific validator
                    new_value = validator_method(current_value)
                    setattr(self, field_name, new_value)

    @classmethod
    def validate(cls, validation_function: Type, value: Any) -> Any:
        """
        Class method to validate a value with a given validation function.

        Parameters
        ----------
        cls : BaseSettings
            BaseSettings class.
        validation_function : Type
            Validation function to apply.
        value : Any
            Value to validate.

        Returns
        -------
        Any
            Validated value.

        Examples
        --------
        >>> def uppercase(val: str) -> str:
        ...     return val.upper()
        >>> BaseSettings.validate(uppercase, 'test')
        'TEST'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        return validation_function(value)

    def is_valid(self) -> bool:
        """
        Validate that current configuration has all required fields.

        Parameters
        ----------
        self : BaseSettings
            Instance of BaseSettings class.

        Returns
        -------
        bool
            True if configuration is valid, False otherwise.

        Examples
        --------
        >>> class ValidConfig(BaseSettings):
        ...     required_field: str = 'value'
        >>> config = ValidConfig()
        >>> config.is_valid()
        True

        >>> class InvalidConfig(BaseSettings):
        ...     required_field: str = ''
        >>> config = InvalidConfig()
        >>> config.is_valid()
        False

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        try:
            # Verify that all annotated fields have non-empty values
            for field_name, field_type in self.__annotations__.items():
                if hasattr(self, field_name):
                    value = getattr(self, field_name)
                    if value is None or (isinstance(value, str) and value.strip() == ''):
                        return False
                else:
                    return False
            return True
        except Exception:
            return False

    def to_json(self):
        """
        Convert current configuration to a JSON string.

        Parameters
        ----------
        self : BaseSettings
            Instance of BaseSettings class.

        Returns
        -------
        dict
            Configuration as dictionary.

        Examples
        --------
        >>> class TestConfig(BaseSettings):
        ...     test_field: str = 'value'
        >>> config = TestConfig()
        >>> result = config.to_json()
        >>> isinstance(result, dict)
        True
        >>> result['test_field']
        'value'

        :Authors:
            - Pablo Contreras

        :Created:
            - 2025-08-30
        """
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        return json_loads(json_dumps(data))