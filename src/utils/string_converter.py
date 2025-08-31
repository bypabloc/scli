from typing import List
from typing import Optional
from re import split as re_split
from re import sub as re_sub
from re import findall as re_findall

from src.utils.logger import logger


def detect_case_style(text: str) -> str:
    """
    Detecta automáticamente el estilo de case de un texto.
    
    Parameters
    ----------
    text : str
        Texto a analizar para detectar el estilo
        
    Returns
    -------
    str
        Estilo detectado: 'snake_case', 'kebab-case', 'camelCase', 'PascalCase', 'UPPER_CASE', 'space_separated', 'unknown'
        
    Examples
    --------
    >>> detect_case_style("hello_world")
    'snake_case'
    
    >>> detect_case_style("hello-world")
    'kebab-case'
    
    >>> detect_case_style("helloWorld")
    'camelCase'
    
    >>> detect_case_style("HelloWorld")
    'PascalCase'
    
    >>> detect_case_style("HELLO_WORLD")
    'UPPER_CASE'
    
    >>> detect_case_style("hello world")
    'space_separated'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not text or not isinstance(text, str):
        return 'unknown'
        
    # Espacios - texto separado por espacios
    if ' ' in text and '_' not in text and '-' not in text:
        return 'space_separated'
    
    # UPPER_CASE - todo en mayúsculas con guiones bajos
    if text.isupper() and '_' in text:
        return 'UPPER_CASE'
    
    # snake_case - minúsculas con guiones bajos
    if '_' in text and text.islower():
        return 'snake_case'
    
    # kebab-case - minúsculas con guiones
    if '-' in text and text.islower():
        return 'kebab-case'
    
    # PascalCase - empieza con mayúscula y tiene más mayúsculas
    if text[0].isupper() and any(c.isupper() for c in text[1:]) and '_' not in text and '-' not in text:
        return 'PascalCase'
    
    # camelCase - empieza con minúscula y tiene mayúsculas
    if text[0].islower() and any(c.isupper() for c in text[1:]) and '_' not in text and '-' not in text:
        return 'camelCase'
    
    # Si no coincide con ningún patrón conocido
    return 'unknown'


def split_words(text: str, current_style: Optional[str] = None) -> List[str]:
    """
    Divide un texto en palabras individuales basándose en su estilo.
    
    Parameters
    ----------
    text : str
        Texto a dividir en palabras
    current_style : str, optional
        Estilo actual del texto (se detecta automáticamente si no se proporciona)
        
    Returns
    -------
    List[str]
        Lista de palabras en minúsculas
        
    Examples
    --------
    >>> split_words("hello_world", "snake_case")
    ['hello', 'world']
    
    >>> split_words("helloWorld", "camelCase")
    ['hello', 'world']
    
    >>> split_words("HelloWorld", "PascalCase")
    ['hello', 'world']
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not text:
        return []
        
    if current_style is None:
        current_style = detect_case_style(text)
    
    logger.debug("Dividiendo palabras", detail={
        "text": text,
        "detected_style": current_style
    })
    
    words = []
    
    if current_style in ['snake_case', 'UPPER_CASE']:
        # Dividir por guiones bajos
        words = text.lower().split('_')
    elif current_style == 'kebab-case':
        # Dividir por guiones
        words = text.lower().split('-')
    elif current_style == 'space_separated':
        # Dividir por espacios
        words = text.lower().split(' ')
    elif current_style in ['camelCase', 'PascalCase']:
        # Dividir por mayúsculas usando regex
        # Encuentra transiciones de minúscula a mayúscula
        words = re_findall(r'[A-Z]*[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', text)
        words = [word.lower() for word in words if word]
    else:
        # Estilo desconocido, intentar dividir por varios separadores
        # Primero intentar con camelCase/PascalCase
        camel_words = re_findall(r'[A-Z]*[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', text)
        if len(camel_words) > 1:
            words = [word.lower() for word in camel_words]
        else:
            # Fallback: dividir por separadores comunes
            words = re_split(r'[_\-\s]+', text.lower())
    
    # Filtrar palabras vacías y limpiar
    words = [word.strip() for word in words if word and word.strip()]
    
    logger.debug("Palabras extraídas", detail={
        "original": text,
        "style": current_style,
        "words": words
    })
    
    return words


def convert_to_snake_case(words: List[str]) -> str:
    """
    Convierte una lista de palabras a snake_case.
    
    Parameters
    ----------
    words : List[str]
        Lista de palabras a convertir
        
    Returns
    -------
    str
        Texto en formato snake_case
        
    Examples
    --------
    >>> convert_to_snake_case(['hello', 'world'])
    'hello_world'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return '_'.join(word.lower() for word in words if word)


def convert_to_kebab_case(words: List[str]) -> str:
    """
    Convierte una lista de palabras a kebab-case.
    
    Parameters
    ----------
    words : List[str]
        Lista de palabras a convertir
        
    Returns
    -------
    str
        Texto en formato kebab-case
        
    Examples
    --------
    >>> convert_to_kebab_case(['hello', 'world'])
    'hello-world'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return '-'.join(word.lower() for word in words if word)


def convert_to_camel_case(words: List[str]) -> str:
    """
    Convierte una lista de palabras a camelCase.
    
    Parameters
    ----------
    words : List[str]
        Lista de palabras a convertir
        
    Returns
    -------
    str
        Texto en formato camelCase
        
    Examples
    --------
    >>> convert_to_camel_case(['hello', 'world'])
    'helloWorld'
    
    >>> convert_to_camel_case(['hello'])
    'hello'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not words:
        return ''
    
    # Primera palabra en minúscula, resto con primera letra mayúscula
    result = words[0].lower()
    if len(words) > 1:
        result += ''.join(word.capitalize() for word in words[1:])
    
    return result


def convert_to_pascal_case(words: List[str]) -> str:
    """
    Convierte una lista de palabras a PascalCase.
    
    Parameters
    ----------
    words : List[str]
        Lista de palabras a convertir
        
    Returns
    -------
    str
        Texto en formato PascalCase
        
    Examples
    --------
    >>> convert_to_pascal_case(['hello', 'world'])
    'HelloWorld'
    
    >>> convert_to_pascal_case(['hello'])
    'Hello'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return ''.join(word.capitalize() for word in words if word)


def convert_case_style(text: str, target_style: str) -> str:
    """
    Convierte texto de cualquier estilo a otro estilo específico.
    
    Detecta automáticamente el estilo original del texto y lo convierte
    al estilo objetivo especificado.
    
    Parameters
    ----------
    text : str
        Texto original a convertir
    target_style : str
        Estilo objetivo: 'snake_case', 'kebab-case', 'camelCase', 'PascalCase'
        
    Returns
    -------
    str
        Texto convertido al estilo objetivo
        
    Raises
    ------
    ValueError
        Si el target_style no es válido
        
    Examples
    --------
    >>> convert_case_style("hello_world", "camelCase")
    'helloWorld'
    
    >>> convert_case_style("helloWorld", "snake_case")
    'hello_world'
    
    >>> convert_case_style("hello-world", "PascalCase")
    'HelloWorld'
    
    >>> convert_case_style("hello world", "kebab-case")
    'hello-world'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    if not text or not isinstance(text, str):
        logger.warning("Texto inválido para conversión", detail={
            "text": text,
            "type": type(text).__name__ if text is not None else "None"
        })
        return text or ''
    
    # Validar target_style
    valid_styles = ['snake_case', 'kebab-case', 'camelCase', 'PascalCase']
    if target_style not in valid_styles:
        raise ValueError(f"target_style debe ser uno de {valid_styles}, recibido: {target_style}")
    
    # Detectar estilo original
    original_style = detect_case_style(text)
    
    logger.debug("Iniciando conversión de estilo", detail={
        "original_text": text,
        "original_style": original_style,
        "target_style": target_style
    })
    
    # Si ya está en el estilo objetivo, retornar sin cambios
    if original_style == target_style:
        logger.debug("Texto ya está en el estilo objetivo", detail={
            "text": text,
            "style": target_style
        })
        return text
    
    # Dividir en palabras
    words = split_words(text, original_style)
    
    if not words:
        logger.warning("No se pudieron extraer palabras del texto", detail={
            "original_text": text,
            "detected_style": original_style
        })
        return text
    
    # Convertir al estilo objetivo
    converters = {
        'snake_case': convert_to_snake_case,
        'kebab-case': convert_to_kebab_case,
        'camelCase': convert_to_camel_case,
        'PascalCase': convert_to_pascal_case
    }
    
    converted_text = converters[target_style](words)
    
    logger.debug("Conversión completada", detail={
        "original": text,
        "converted": converted_text,
        "from_style": original_style,
        "to_style": target_style,
        "words_extracted": words
    })
    
    return converted_text


def get_supported_styles() -> List[str]:
    """
    Obtiene la lista de estilos de case soportados.
    
    Returns
    -------
    List[str]
        Lista de estilos soportados para conversión
        
    Examples
    --------
    >>> styles = get_supported_styles()
    >>> 'snake_case' in styles
    True
    
    >>> 'camelCase' in styles
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return ['snake_case', 'kebab-case', 'camelCase', 'PascalCase']


# API pública del módulo
__all__ = [
    'detect_case_style',
    'split_words', 
    'convert_case_style',
    'convert_to_snake_case',
    'convert_to_kebab_case',
    'convert_to_camel_case',
    'convert_to_pascal_case',
    'get_supported_styles'
]