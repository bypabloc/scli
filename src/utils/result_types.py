from typing import Dict
from typing import Any
from typing import Union


# Type alias para resultados estructurados
ResultDict = Dict[str, Any]


def success(data: Any = None) -> ResultDict:
    """
    Crea un resultado exitoso estándar.
    
    Parameters
    ----------
    data : Any, optional
        Datos a incluir en el resultado exitoso
        
    Returns
    -------
    ResultDict
        Diccionario con is_valid=True y datos proporcionados
        
    Examples
    --------
    >>> result = success({'user_id': 123})
    >>> result['is_valid']
    True
    
    >>> result['data']
    {'user_id': 123}
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    result = {
        'is_valid': True,
        'code': 0,
        'data': data
    }
    
    return result


def error(code: int = 1, data: Any = None, message: str = None) -> ResultDict:
    """
    Crea un resultado de error estándar.
    
    Parameters
    ----------
    code : int, optional
        Código de error (default: 1)
    data : Any, optional
        Datos adicionales del error
    message : str, optional
        Mensaje de error personalizado
        
    Returns
    -------
    ResultDict
        Diccionario con is_valid=False y información del error
        
    Examples
    --------
    >>> result = error(code=404, message="Not found")
    >>> result['is_valid']
    False
    
    >>> result['code']
    404
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    result = {
        'is_valid': False,
        'code': code,
        'data': data
    }
    
    if message:
        if isinstance(data, dict):
            result['data'] = {**data, 'message': message}
        else:
            result['data'] = {'message': message}
    
    return result


def is_success(result: ResultDict) -> bool:
    """
    Verifica si un resultado es exitoso.
    
    Parameters
    ----------
    result : ResultDict
        Resultado a verificar
        
    Returns
    -------
    bool
        True si el resultado es exitoso, False en caso contrario
        
    Examples
    --------
    >>> success_result = success({'data': 'test'})
    >>> is_success(success_result)
    True
    
    >>> error_result = error(code=1, message="Failed")
    >>> is_success(error_result)
    False
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return result.get('is_valid', False) is True


def is_error(result: ResultDict) -> bool:
    """
    Verifica si un resultado es un error.
    
    Parameters
    ----------
    result : ResultDict
        Resultado a verificar
        
    Returns
    -------
    bool
        True si el resultado es un error, False en caso contrario
        
    Examples
    --------
    >>> error_result = error(code=1, message="Failed")
    >>> is_error(error_result)
    True
    
    >>> success_result = success({'data': 'test'})
    >>> is_error(success_result)
    False
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return result.get('is_valid', True) is False


def get_error_message(result: ResultDict) -> str:
    """
    Extrae el mensaje de error de un resultado.
    
    Parameters
    ----------
    result : ResultDict
        Resultado del cual extraer el mensaje
        
    Returns
    -------
    str
        Mensaje de error o string vacío si no hay mensaje
        
    Examples
    --------
    >>> error_result = error(code=1, message="Something failed")
    >>> get_error_message(error_result)
    'Something failed'
    
    >>> success_result = success({'data': 'test'})
    >>> get_error_message(success_result)
    ''
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not is_error(result):
        return ''
    
    data = result.get('data', {})
    
    if isinstance(data, dict):
        return data.get('message', '')
    
    return ''


def get_result_data(result: ResultDict) -> Any:
    """
    Extrae los datos de un resultado.
    
    Parameters
    ----------
    result : ResultDict
        Resultado del cual extraer los datos
        
    Returns
    -------
    Any
        Datos del resultado o None si no hay datos
        
    Examples
    --------
    >>> success_result = success({'user_id': 123, 'name': 'John'})
    >>> get_result_data(success_result)
    {'user_id': 123, 'name': 'John'}
    
    >>> error_result = error(code=1, data={'error_code': 'INVALID'})
    >>> get_result_data(error_result)
    {'error_code': 'INVALID'}
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return result.get('data')


def get_result_code(result: ResultDict) -> int:
    """
    Extrae el código de un resultado.
    
    Parameters
    ----------
    result : ResultDict
        Resultado del cual extraer el código
        
    Returns
    -------
    int
        Código del resultado (0 para éxito, >0 para error)
        
    Examples
    --------
    >>> success_result = success({'data': 'test'})
    >>> get_result_code(success_result)
    0
    
    >>> error_result = error(code=404, message="Not found")
    >>> get_result_code(error_result)
    404
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return result.get('code', 0)


# API pública del módulo
__all__ = [
    'ResultDict',
    'success',
    'error',
    'is_success',
    'is_error',
    'get_error_message',
    'get_result_data',
    'get_result_code'
]