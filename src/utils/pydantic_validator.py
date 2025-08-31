from typing import Any
from typing import Dict
from typing import List
from typing import Union

from pydantic import ValidationError

from src.utils.logger import logger


def format_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Formatea los errores devueltos por Pydantic en un diccionario estructurado
    con mensajes descriptivos acordes al árbol de argumentos.
    
    Genera mensajes más informativos que incluyen el contexto completo
    del error y sugerencias de corrección cuando es apropiado.
    
    Parameters
    ----------
    errors : List[Dict[str, Any]]
        Lista de errores devueltos por Pydantic
        
    Returns
    -------
    Dict[str, Any]
        Diccionario estructurado con errores formateados y contextualizados
        
    Examples
    --------
    >>> errors = [
    ...     {
    ...         'loc': ('rut',),
    ...         'msg': 'String too short',
    ...         'type': 'value_error.any_str.min_length',
    ...         'ctx': {'limit_value': 8}
    ...     }
    ... ]
    >>> result = format_errors(errors)
    >>> result['rut']
    ['El campo rut debe tener al menos 8 caracteres']
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    formatted = {}
    
    for error in errors:
        # Construir la ruta completa del campo
        field_path = " → ".join(str(loc) for loc in error['loc'])
        field_name = error['loc'][-1] if error['loc'] else 'campo desconocido'
        
        # Contextualizar el mensaje según el tipo de error
        original_msg = error['msg']
        error_type = error.get('type', '')
        context = error.get('ctx', {})
        
        # Generar mensaje contextualizado y descriptivo
        contextual_msg = _generate_contextual_message(
            field_name, field_path, original_msg, error_type, context
        )
        
        # Construir estructura anidada manteniendo la jerarquía
        current_level = formatted
        for loc in error['loc'][:-1]:
            if loc not in current_level:
                current_level[loc] = {}
            current_level = current_level[loc]
        
        # Agregar el mensaje al campo final
        final_loc = error['loc'][-1] if error['loc'] else 'unknown'
        if final_loc not in current_level:
            current_level[final_loc] = []
        
        current_level[final_loc].append(contextual_msg)
        
        # Log del error para debugging
        logger.debug("Error de validación Pydantic procesado", detail={
            "field_path": field_path,
            "error_type": error_type,
            "original_msg": original_msg,
            "contextual_msg": contextual_msg
        })
    
    return formatted


def _generate_contextual_message(
    field_name: str,
    field_path: str, 
    original_msg: str,
    error_type: str,
    context: Dict[str, Any]
) -> str:
    """
    Genera un mensaje contextualizado y descriptivo para un error de validación.
    
    Parameters
    ----------
    field_name : str
        Nombre del campo que causó el error
    field_path : str
        Ruta completa del campo en formato "padre → hijo"
    original_msg : str
        Mensaje original de Pydantic
    error_type : str
        Tipo de error de Pydantic
    context : Dict[str, Any]
        Contexto adicional del error
        
    Returns
    -------
    str
        Mensaje contextualizado y descriptivo
        
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    # Prefijo contextual
    if field_path == field_name:
        prefix = f"El argumento '{field_name}'"
    else:
        prefix = f"El campo '{field_name}' en {field_path}"
    
    # Mapear tipos de error comunes a mensajes más descriptivos
    error_mappings = {
        # Errores de tipo
        'type_error.str': f"{prefix} debe ser una cadena de texto",
        'type_error.int': f"{prefix} debe ser un número entero",
        'type_error.float': f"{prefix} debe ser un número decimal",
        'type_error.bool': f"{prefix} debe ser verdadero o falso (true/false)",
        'type_error.dict': f"{prefix} debe ser un objeto JSON válido",
        'type_error.list': f"{prefix} debe ser una lista/array",
        
        # Errores de valor
        'value_error.missing': f"{prefix} es obligatorio y no puede estar vacío",
        'value_error.extra': f"El campo '{field_name}' no está permitido en este contexto",
        'value_error.const': f"{prefix} debe tener exactamente el valor esperado",
        
        # Errores de longitud de string
        'value_error.any_str.min_length': f"{prefix} debe tener al menos {context.get('limit_value', '?')} caracteres",
        'value_error.any_str.max_length': f"{prefix} no puede exceder {context.get('limit_value', '?')} caracteres",
        
        # Errores numéricos
        'value_error.number.not_ge': f"{prefix} debe ser mayor o igual a {context.get('limit_value', '?')}",
        'value_error.number.not_gt': f"{prefix} debe ser mayor que {context.get('limit_value', '?')}",
        'value_error.number.not_le': f"{prefix} debe ser menor o igual a {context.get('limit_value', '?')}",
        'value_error.number.not_lt': f"{prefix} debe ser menor que {context.get('limit_value', '?')}",
        
        # Errores de formato
        'value_error.email': f"{prefix} debe tener un formato de email válido",
        'value_error.url': f"{prefix} debe ser una URL válida",
        'value_error.regex': f"{prefix} no cumple con el formato requerido",
    }
    
    # Intentar encontrar un mapeo directo
    if error_type in error_mappings:
        return error_mappings[error_type]
    
    # Mapeos por patrones parciales
    if 'min_length' in error_type:
        min_val = context.get('limit_value', '?')
        return f"{prefix} debe tener al menos {min_val} caracteres"
    
    if 'max_length' in error_type:
        max_val = context.get('limit_value', '?')
        return f"{prefix} no puede exceder {max_val} caracteres"
    
    if 'missing' in error_type.lower() or 'required' in original_msg.lower():
        return f"{prefix} es obligatorio"
    
    if 'too_short' in original_msg.lower():
        min_val = context.get('limit_value', context.get('min_length', '?'))
        return f"{prefix} es demasiado corto, mínimo {min_val} caracteres requeridos"
    
    if 'too_long' in original_msg.lower():
        max_val = context.get('limit_value', context.get('max_length', '?'))
        return f"{prefix} es demasiado largo, máximo {max_val} caracteres permitidos"
    
    if 'invalid' in original_msg.lower():
        return f"{prefix} tiene un valor inválido: {original_msg}"
    
    # Si no hay mapeo específico, mejorar el mensaje original
    return f"{prefix}: {original_msg.lower()}"


def validate_with_model(
    data: Dict[str, Any], 
    model_class: type,
    command_name: str = "desconocido"
) -> Dict[str, Any]:
    """
    Valida datos usando un modelo Pydantic específico con manejo de errores mejorado.
    
    Parameters
    ----------
    data : Dict[str, Any]
        Datos a validar
    model_class : type
        Clase del modelo Pydantic para validación
    command_name : str, optional
        Nombre del comando para contexto en logs
        
    Returns
    -------
    Dict[str, Any]
        Resultado de validación con estructura:
        {
            'is_valid': bool,
            'validated_data': Dict[str, Any] | None,
            'errors': Dict[str, Any] | None,
            'error_summary': str | None
        }
        
    Examples
    --------
    >>> from pydantic import BaseModel, Field
    >>> class TestModel(BaseModel):
    ...     name: str = Field(min_length=2)
    ...     age: int = Field(ge=0)
    >>> result = validate_with_model({'name': 'A', 'age': -1}, TestModel)
    >>> result['is_valid']
    False
    >>> 'name' in result['errors']
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    logger.debug("Iniciando validación con modelo Pydantic", detail={
        "command_name": command_name,
        "model_class": model_class.__name__,
        "data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
        "data_count": len(data) if isinstance(data, dict) else 0
    })
    
    try:
        # Intentar validar con el modelo
        validated_instance = model_class(**data)
        validated_data = validated_instance.model_dump()
        
        logger.debug("Validación exitosa", detail={
            "command_name": command_name,
            "model_class": model_class.__name__,
            "validated_fields": list(validated_data.keys())
        })
        
        return {
            'is_valid': True,
            'validated_data': validated_data,
            'errors': None,
            'error_summary': None
        }
        
    except ValidationError:
        import sys
        validation_error = sys.exc_info()[1]
        
        # Formatear errores de forma descriptiva
        formatted_errors = format_errors(validation_error.errors())
        
        # Generar resumen de errores
        error_count = len(validation_error.errors())
        error_fields = list(set(str(err['loc'][-1]) for err in validation_error.errors() if err['loc']))
        error_summary = f"{error_count} error(es) de validación en el comando '{command_name}': {', '.join(error_fields)}"
        
        logger.warning("Error de validación Pydantic", detail={
            "command_name": command_name,
            "model_class": model_class.__name__,
            "error_count": error_count,
            "error_fields": error_fields,
            "formatted_errors": formatted_errors
        })
        
        return {
            'is_valid': False,
            'validated_data': None,
            'errors': formatted_errors,
            'error_summary': error_summary
        }
        
    except Exception:
        # Error inesperado durante la validación
        error_msg = f"Error inesperado durante validación del comando '{command_name}'"
        
        logger.critical("Error inesperado en validación", detail={
            "command_name": command_name,
            "model_class": model_class.__name__
        })
        
        return {
            'is_valid': False,
            'validated_data': None,
            'errors': {'validation_error': [error_msg]},
            'error_summary': error_msg
        }


# API pública del módulo
__all__ = [
    'format_errors',
    'validate_with_model'
]