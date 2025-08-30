#!/usr/bin/env python3
"""
Validation system for SCLI commands

Based on production validation patterns but adapted for CLI usage.
Provides validation framework for command arguments and configurations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ValidationErrorType(Enum):
    """Types of validation errors for SCLI commands"""
    MISSING_REQUIRED = "missing_required"
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    INVALID_FORMAT = "invalid_format"
    VALIDATION_ERROR = "validation_error"
    DEPENDENCY_MISSING = "dependency_missing"
    PERMISSION_DENIED = "permission_denied"
    FILE_NOT_FOUND = "file_not_found"
    UNEXPECTED_ERROR = "unexpected_error"


@dataclass
class ValidationResult:
    """
    Pure validation result without knowledge of response handlers.
    
    Attributes:
        is_valid: Whether validation was successful
        data: Validated data if successful, None if failed
        error_type: Type of error if validation failed
        error_message: Detailed error message
        field: Field that caused the error (optional)
        code: Error code (0 for success, 1+ for errors)
    """
    is_valid: bool
    data: Any = None
    error_type: Optional[ValidationErrorType] = None
    error_message: Optional[str] = None
    field: Optional[str] = None
    code: int = 0


class ValidationCore:
    """
    Core validation logic for SCLI commands.
    
    Provides basic validation functions that can be used by commands
    to validate their inputs, arguments, and configurations.
    """
    
    @staticmethod
    def validate_required_field(
        data: Dict[str, Any], 
        field: str, 
        field_type: type = None
    ) -> ValidationResult:
        """
        Validate that a required field exists and has the correct type.
        
        Args:
            data: Dictionary containing the data
            field: Name of the required field
            field_type: Expected type of the field (optional)
            
        Returns:
            ValidationResult with validation outcome
        """
        if field not in data:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.MISSING_REQUIRED,
                error_message=f"Required field '{field}' is missing",
                field=field,
                code=1
            )
        
        value = data[field]
        
        if value is None:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.MISSING_REQUIRED,
                error_message=f"Field '{field}' cannot be None",
                field=field,
                code=1
            )
        
        if field_type and not isinstance(value, field_type):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_TYPE,
                error_message=f"Field '{field}' must be of type {field_type.__name__}, got {type(value).__name__}",
                field=field,
                code=1
            )
        
        return ValidationResult(
            is_valid=True,
            data=value,
            code=0
        )
    
    @staticmethod
    def validate_file_path(
        path: str, 
        must_exist: bool = True, 
        must_be_file: bool = True
    ) -> ValidationResult:
        """
        Validate a file path.
        
        Args:
            path: Path to validate
            must_exist: Whether the path must exist
            must_be_file: Whether the path must be a file (vs directory)
            
        Returns:
            ValidationResult with validation outcome
        """
        import os
        from pathlib import Path
        
        if not path or not isinstance(path, str):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message="Path must be a non-empty string",
                field="path",
                code=1
            )
        
        path_obj = Path(path)
        
        if must_exist and not path_obj.exists():
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.FILE_NOT_FOUND,
                error_message=f"Path does not exist: {path}",
                field="path",
                code=1
            )
        
        if must_exist and must_be_file and not path_obj.is_file():
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message=f"Path is not a file: {path}",
                field="path",
                code=1
            )
        
        if must_exist and not must_be_file and not path_obj.is_dir():
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message=f"Path is not a directory: {path}",
                field="path",
                code=1
            )
        
        # Check permissions if path exists
        if path_obj.exists():
            try:
                if must_be_file and not os.access(path, os.R_OK):
                    return ValidationResult(
                        is_valid=False,
                        error_type=ValidationErrorType.PERMISSION_DENIED,
                        error_message=f"No read permission for file: {path}",
                        field="path",
                        code=1
                    )
            except OSError as e:
                return ValidationResult(
                    is_valid=False,
                    error_type=ValidationErrorType.PERMISSION_DENIED,
                    error_message=f"Permission error: {e}",
                    field="path",
                    code=1
                )
        
        return ValidationResult(
            is_valid=True,
            data=str(path_obj.absolute()),
            code=0
        )
    
    @staticmethod
    def validate_dependency(dependency: str) -> ValidationResult:
        """
        Validate that a Python dependency is available.
        
        Args:
            dependency: Name of the dependency to check
            
        Returns:
            ValidationResult with validation outcome
        """
        try:
            __import__(dependency)
            return ValidationResult(
                is_valid=True,
                data=dependency,
                code=0
            )
        except ImportError:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.DEPENDENCY_MISSING,
                error_message=f"Required dependency '{dependency}' is not installed",
                field="dependency",
                code=1
            )
    
    @staticmethod
    def validate_choice(
        value: Any, 
        choices: List[Any], 
        field_name: str = "value"
    ) -> ValidationResult:
        """
        Validate that a value is in a list of allowed choices.
        
        Args:
            value: Value to validate
            choices: List of allowed values
            field_name: Name of the field being validated
            
        Returns:
            ValidationResult with validation outcome
        """
        if value not in choices:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message=f"Invalid {field_name}: '{value}'. Must be one of: {choices}",
                field=field_name,
                code=1
            )
        
        return ValidationResult(
            is_valid=True,
            data=value,
            code=0
        )
    
    @staticmethod
    def validate_range(
        value: Union[int, float], 
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        field_name: str = "value"
    ) -> ValidationResult:
        """
        Validate that a numeric value is within a specified range.
        
        Args:
            value: Numeric value to validate
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)
            field_name: Name of the field being validated
            
        Returns:
            ValidationResult with validation outcome
        """
        if not isinstance(value, (int, float)):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_TYPE,
                error_message=f"{field_name} must be a number, got {type(value).__name__}",
                field=field_name,
                code=1
            )
        
        if min_value is not None and value < min_value:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message=f"{field_name} must be >= {min_value}, got {value}",
                field=field_name,
                code=1
            )
        
        if max_value is not None and value > max_value:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message=f"{field_name} must be <= {max_value}, got {value}",
                field=field_name,
                code=1
            )
        
        return ValidationResult(
            is_valid=True,
            data=value,
            code=0
        )
    
    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """
        Validate an email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult with validation outcome
        """
        import re
        
        if not email or not isinstance(email, str):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message="Email must be a non-empty string",
                field="email",
                code=1
            )
        
        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_FORMAT,
                error_message=f"Invalid email format: {email}",
                field="email",
                code=1
            )
        
        return ValidationResult(
            is_valid=True,
            data=email.lower().strip(),
            code=0
        )
    
    @staticmethod
    def validate_url(url: str) -> ValidationResult:
        """
        Validate a URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            ValidationResult with validation outcome
        """
        import re
        
        if not url or not isinstance(url, str):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_VALUE,
                error_message="URL must be a non-empty string",
                field="url",
                code=1
            )
        
        # Basic URL regex pattern
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        
        if not re.match(url_pattern, url):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.INVALID_FORMAT,
                error_message=f"Invalid URL format: {url}",
                field="url",
                code=1
            )
        
        return ValidationResult(
            is_valid=True,
            data=url.strip(),
            code=0
        )


class ValidationErrorMapping:
    """
    Mapping of validation error types to user-friendly messages.
    
    Centralizes error message formatting for consistency.
    """
    
    ERROR_MESSAGES = {
        ValidationErrorType.MISSING_REQUIRED: "Required field is missing",
        ValidationErrorType.INVALID_TYPE: "Invalid data type",
        ValidationErrorType.INVALID_VALUE: "Invalid value",
        ValidationErrorType.INVALID_FORMAT: "Invalid format",
        ValidationErrorType.VALIDATION_ERROR: "Validation error",
        ValidationErrorType.DEPENDENCY_MISSING: "Missing dependency",
        ValidationErrorType.PERMISSION_DENIED: "Permission denied",
        ValidationErrorType.FILE_NOT_FOUND: "File not found",
        ValidationErrorType.UNEXPECTED_ERROR: "Unexpected error",
    }
    
    @classmethod
    def get_error_message(cls, error_type: ValidationErrorType) -> str:
        """Get user-friendly error message for error type"""
        return cls.ERROR_MESSAGES.get(error_type, "Unknown error")
    
    @classmethod
    def format_validation_errors(cls, results: List[ValidationResult]) -> str:
        """
        Format multiple validation errors into a readable message.
        
        Args:
            results: List of ValidationResult objects with errors
            
        Returns:
            Formatted error message string
        """
        errors = [r for r in results if not r.is_valid]
        if not errors:
            return "No validation errors"
        
        if len(errors) == 1:
            error = errors[0]
            return f"❌ {error.error_message or cls.get_error_message(error.error_type)}"
        
        lines = ["❌ Multiple validation errors:"]
        for i, error in enumerate(errors, 1):
            message = error.error_message or cls.get_error_message(error.error_type)
            field_info = f" (field: {error.field})" if error.field else ""
            lines.append(f"  {i}. {message}{field_info}")
        
        return "\n".join(lines)


def validate_command_args(args: Dict[str, Any], validations: Dict[str, Any]) -> List[ValidationResult]:
    """
    Validate command arguments using a validation schema.
    
    Args:
        args: Dictionary of arguments to validate
        validations: Dictionary of validation rules
        
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    for field, rules in validations.items():
        if isinstance(rules, dict):
            # Required field validation
            if rules.get('required', False):
                result = ValidationCore.validate_required_field(
                    args, field, rules.get('type')
                )
                results.append(result)
                if not result.is_valid:
                    continue
            
            # Get the value for further validation
            value = args.get(field)
            if value is None:
                continue
            
            # Choice validation
            if 'choices' in rules:
                result = ValidationCore.validate_choice(
                    value, rules['choices'], field
                )
                results.append(result)
            
            # Range validation
            if 'min' in rules or 'max' in rules:
                result = ValidationCore.validate_range(
                    value, rules.get('min'), rules.get('max'), field
                )
                results.append(result)
            
            # File path validation
            if rules.get('type') == 'file':
                result = ValidationCore.validate_file_path(
                    value, 
                    rules.get('must_exist', True),
                    rules.get('must_be_file', True)
                )
                results.append(result)
            
            # Email validation
            if rules.get('type') == 'email':
                result = ValidationCore.validate_email(value)
                results.append(result)
            
            # URL validation
            if rules.get('type') == 'url':
                result = ValidationCore.validate_url(value)
                results.append(result)
    
    return results