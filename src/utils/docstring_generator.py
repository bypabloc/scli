from subprocess import run as subprocess_run
from subprocess import CalledProcessError as subprocess_CalledProcessError
from datetime import datetime
from typing import Optional
from typing import Dict


def get_git_author() -> str:
    """
    Obtiene el nombre del autor desde git config global.

    Returns
    -------
    str
        Nombre del autor configurado en git global

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
    try:
        result = subprocess_run(
            ['git', 'config', '--global', 'user.name'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess_CalledProcessError:
        return "Pablo Contreras"  # Fallback


def get_git_email() -> str:
    """
    Obtiene el email del autor desde git config global.

    Returns
    -------
    str
        Email del autor configurado en git global

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
    try:
        result = subprocess_run(
            ['git', 'config', '--global', 'user.email'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess_CalledProcessError:
        return "pacg1991@gmail.com"  # Fallback


def get_current_date() -> str:
    """
    Obtiene la fecha actual en formato YYYY-MM-DD.

    Returns
    -------
    str
        Fecha actual en formato YYYY-MM-DD

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
    return datetime.now().strftime('%Y-%m-%d')


def generate_function_docstring(
    description: str,
    parameters: Optional[Dict[str, str]] = None,
    returns: Optional[str] = None,
    examples: Optional[Dict[str, str]] = None,
    updated_date: Optional[str] = None
) -> str:
    """
    Genera un docstring completo para una función con valores dinámicos.

    Parameters
    ----------
    description : str
        Descripción principal de la función
    parameters : dict, optional
        Diccionario con parámetros y sus descripciones
    returns : str, optional
        Descripción del valor de retorno
    examples : dict, optional
        Diccionario con ejemplos de uso (clave: código, valor: resultado esperado)
    updated_date : str, optional
        Fecha de última actualización (opcional)

    Returns
    -------
    str
        Docstring completo formateado

    Examples
    --------
    >>> docstring = generate_function_docstring(
    ...     'Suma dos números',
    ...     parameters={'a : int': 'Primer número', 'b : int': 'Segundo número'},
    ...     returns='int\\n        Resultado de la suma',
    ...     examples={'add(2, 3)': '5', 'add(0, 0)': '0'}
    ... )
    >>> 'Examples' in docstring
    True

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
    author = get_git_author()
    created_date = get_current_date()
    
    docstring = f'    """\n    {description}\n'
    
    # Add parameters section if provided
    if parameters:
        docstring += '\n    Parameters\n    ----------\n'
        for param, desc in parameters.items():
            docstring += f'    {param}\n        {desc}\n'
    
    # Add returns section if provided
    if returns:
        docstring += '\n    Returns\n    -------\n'
        docstring += f'    {returns}\n'
    
    # Add examples section if provided
    if examples:
        docstring += '\n    Examples\n    --------\n'
        for example_code, expected_result in examples.items():
            docstring += f'    >>> {example_code}\n'
            docstring += f'    {expected_result}\n'
            docstring += '\n'
    
    # Add metadata
    docstring += '\n    :Authors:\n'
    docstring += f'        - {author}\n'
    docstring += '\n    :Created:\n'
    docstring += f'        - {created_date}\n'
    
    if updated_date:
        docstring += '\n    :Updated:\n'
        docstring += f'        - {updated_date}\n'
    
    docstring += '    """'
    
    return docstring


def generate_class_docstring(
    description: str,
    methods: Optional[Dict[str, str]] = None,
    attributes: Optional[Dict[str, str]] = None,
    examples: Optional[Dict[str, str]] = None,
    updated_date: Optional[str] = None
) -> str:
    """
    Genera un docstring completo para una clase con valores dinámicos.

    Parameters
    ----------
    description : str
        Descripción principal de la clase
    methods : dict, optional
        Diccionario con métodos y sus descripciones
    attributes : dict, optional
        Diccionario con atributos y sus descripciones
    examples : dict, optional
        Diccionario con ejemplos de uso (clave: código, valor: resultado esperado)
    updated_date : str, optional
        Fecha de última actualización (opcional)

    Returns
    -------
    str
        Docstring completo formateado para clase

    Examples
    --------
    >>> class_docstring = generate_class_docstring(
    ...     'Clase para manejo de configuración',
    ...     methods={'load': 'Carga configuración', 'save': 'Guarda configuración'},
    ...     examples={'config = Config()': 'Config object created'}
    ... )
    >>> 'Methods' in class_docstring
    True

    :Authors:
        - Pablo Contreras

    :Created:
        - 2025-08-30
    """
    author = get_git_author()
    created_date = get_current_date()
    
    docstring = f'    """\n    {description}\n'
    
    # Add methods section if provided
    if methods:
        docstring += '\n    Methods\n    -------\n'
        for method, desc in methods.items():
            docstring += f'    {method} : {desc}\n'
    
    # Add attributes section if provided
    if attributes:
        docstring += '\n    Attributes\n    ----------\n'
        for attr, desc in attributes.items():
            docstring += f'    {attr}\n        {desc}\n'
    
    # Add examples section if provided
    if examples:
        docstring += '\n    Examples\n    --------\n'
        for example_code, expected_result in examples.items():
            docstring += f'    >>> {example_code}\n'
            docstring += f'    {expected_result}\n'
            docstring += '\n'
    
    # Add metadata
    docstring += '\n    :Authors:\n'
    docstring += f'        - {author}\n'
    docstring += '\n    :Created:\n'
    docstring += f'        - {created_date}\n'
    
    if updated_date:
        docstring += '\n    :Updated:\n'
        docstring += f'        - {updated_date}\n'
    
    docstring += '    """'
    
    return docstring


# Export public API
__all__ = [
    'get_git_author',
    'get_git_email', 
    'get_current_date',
    'generate_function_docstring',
    'generate_class_docstring'
]