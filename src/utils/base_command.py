from typing import Dict
from typing import Any
from typing import Optional
from abc import ABC
from abc import abstractmethod

from pydantic import BaseModel

from src.utils.logger import logger
from src.utils.pydantic_validator import validate_with_model


class BaseCommand(ABC):
    """
    Clase base abstracta para todos los comandos de SCLI.
    
    Define la interfaz estándar que deben implementar todos los comandos
    del sistema, incluyendo el ciclo de vida validate -> preload -> execute,
    el manejo de argumentos con validación Pydantic y estados internos.
    
    Attributes
    ----------
    args : Dict[str, Any]
        Argumentos del comando proporcionados durante la inicialización
    is_validated : bool
        Estado de validación del comando
    is_preloaded : bool
        Estado de precarga del comando
    description : str
        Descripción del comando para mostrar en la interfaz CLI (OBLIGATORIO)
    order : int
        Número de orden para clasificar y filtrar comandos (OBLIGATORIO)
    args_model : type[BaseModel]
        Modelo Pydantic para validación de argumentos (OBLIGATORIO)
    validated_args : Dict[str, Any]
        Argumentos validados y procesados por el modelo Pydantic
        
    Examples
    --------
    >>> from pydantic import BaseModel, Field
    >>> class MyCommandArgs(BaseModel):
    ...     name: str = Field(min_length=1, description="Nombre del usuario")
    ...     count: int = Field(ge=1, le=100, description="Número de iteraciones")
    >>> 
    >>> class MyCommand(BaseCommand):
    ...     description = "Comando de ejemplo con validación Pydantic"
    ...     order = 1
    ...     args_model = MyCommandArgs
    ...     
    ...     def validate(self) -> bool:
    ...         self.is_validated = True
    ...         return True
    ...     def preload(self) -> bool:
    ...         self.is_preloaded = True
    ...         return True
    ...     def execute(self) -> int:
    ...         print(f"Hola {self.validated_args['name']}")
    ...         return 0
    >>> 
    >>> cmd = MyCommand({"name": "Usuario", "count": 5})
    >>> cmd.description
    'Comando de ejemplo con validación Pydantic'
    >>> cmd.order
    1
    >>> cmd.validated_args['name']
    'Usuario'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
        
    :Updated:
        - 2025-08-31 (Agregada validación obligatoria con modelos Pydantic)
    """
    
    def __init__(self, args: Optional[Dict[str, Any]] = None):
        """
        Inicializa la clase base del comando con validación Pydantic.
        
        Establece el estado inicial del comando, valida atributos requeridos
        y procesa argumentos usando el modelo Pydantic definido en la clase hija.
        
        Parameters
        ----------
        args : Dict[str, Any], optional
            Argumentos del comando a validar con el modelo Pydantic
            
        Raises
        ------
        AttributeError
            Si la clase no define los atributos requeridos (description, order, args_model)
        ValueError
            Si los argumentos no pasan la validación Pydantic o el order es inválido
            
        Examples
        --------
        >>> from pydantic import BaseModel, Field
        >>> class TestArgs(BaseModel):
        ...     name: str = Field(min_length=1)
        >>> class TestCommand(BaseCommand):
        ...     description = "Comando de prueba"
        ...     order = 1
        ...     args_model = TestArgs
        ...     def validate(self): return True
        ...     def preload(self): return True
        ...     def execute(self): return 0
        >>> cmd = TestCommand({"name": "Usuario"})
        >>> cmd.validated_args['name']
        'Usuario'
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
            
        :Updated:
            - 2025-08-31 (Agregada validación con modelo Pydantic)
        """
        # Validar que la clase hija defina description
        if not hasattr(self, 'description') or not isinstance(self.description, str) or not self.description.strip():
            raise AttributeError(
                f"La clase {self.__class__.__name__} debe definir un atributo 'description' "
                f"de tipo string no vacío para describir el comando en la interfaz CLI."
            )
        
        # Validar que la clase hija defina order
        if not hasattr(self, 'order') or not isinstance(self.order, int):
            raise AttributeError(
                f"La clase {self.__class__.__name__} debe definir un atributo 'order' "
                f"de tipo int para ordenar el comando en la interfaz CLI."
            )
        
        if self.order < 1:
            raise ValueError(
                f"La clase {self.__class__.__name__} debe tener un 'order' >= 1, "
                f"recibido: {self.order}"
            )
        
        # Validar que la clase hija defina args_model
        if not hasattr(self, 'args_model'):
            raise AttributeError(
                f"La clase {self.__class__.__name__} debe definir un atributo 'args_model' "
                f"que sea una clase Pydantic BaseModel para validar argumentos."
            )
        
        # Validar que args_model sea subclase de BaseModel
        if not (isinstance(self.args_model, type) and issubclass(self.args_model, BaseModel)):
            raise AttributeError(
                f"El atributo 'args_model' en {self.__class__.__name__} debe ser una subclase de "
                f"pydantic.BaseModel, recibido: {type(self.args_model)}"
            )
        
        # Inicializar argumentos y estados
        self.args = args or {}
        self.is_validated = False
        self.is_preloaded = False
        self.validated_args = {}
        
        # Validar argumentos con modelo Pydantic
        validation_result = validate_with_model(
            data=self.args, 
            model_class=self.args_model,
            command_name=self.__class__.__name__
        )
        
        if not validation_result['is_valid']:
            error_summary = validation_result['error_summary']
            detailed_errors = validation_result['errors']
            
            logger.error("Fallo en validación de argumentos", detail={
                "command_class": self.__class__.__name__,
                "error_summary": error_summary,
                "detailed_errors": detailed_errors,
                "provided_args": self.args
            })
            
            # Crear mensaje de error detallado
            error_lines = [f"Errores de validación en {self.__class__.__name__}:"]
            for field, messages in detailed_errors.items():
                if isinstance(messages, list):
                    for msg in messages:
                        error_lines.append(f"  - {msg}")
                else:
                    error_lines.append(f"  - {field}: {messages}")
            
            raise ValueError("\n".join(error_lines))
        
        # Guardar argumentos validados
        self.validated_args = validation_result['validated_data']
        
        logger.debug("Comando base inicializado exitosamente", detail={
            "command_class": self.__class__.__name__,
            "description": self.description,
            "order": self.order,
            "args_model": self.args_model.__name__,
            "raw_args_count": len(self.args),
            "validated_args_count": len(self.validated_args),
            "validated_args_keys": list(self.validated_args.keys())
        })
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Valida que el comando pueda ejecutarse correctamente.
        
        Método abstracto que debe ser implementado por cada comando específico.
        Debe verificar prerrequisitos, argumentos válidos y cualquier condición
        necesaria para la ejecución exitosa del comando.
        
        Returns
        -------
        bool
            True si la validación es exitosa, False en caso contrario.
            Debe actualizar self.is_validated apropiadamente.
            
        Raises
        ------
        NotImplementedError
            Si el método no es implementado en la clase hija
            
        Examples
        --------
        >>> class TestCommand(BaseCommand):
        ...     def validate(self) -> bool:
        ...         self.is_validated = True
        ...         return True
        ...     def preload(self) -> bool:
        ...         return True
        ...     def execute(self) -> int:
        ...         return 0
        >>> cmd = TestCommand()
        >>> cmd.validate()
        True
        >>> cmd.is_validated
        True
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        raise NotImplementedError(
            f"El método validate() debe ser implementado en {self.__class__.__name__}"
        )
    
    @abstractmethod 
    def preload(self) -> bool:
        """
        Precarga recursos y prepara el entorno para la ejecución del comando.
        
        Método abstracto que debe ser implementado por cada comando específico.
        Debe realizar tareas de inicialización como cargar configuraciones,
        establecer conexiones o preparar datos necesarios.
        
        Returns
        -------
        bool
            True si la precarga es exitosa, False en caso contrario.
            Debe actualizar self.is_preloaded apropiadamente.
            
        Raises
        ------
        NotImplementedError
            Si el método no es implementado en la clase hija
            
        Examples
        --------
        >>> class TestCommand(BaseCommand):
        ...     def validate(self) -> bool:
        ...         self.is_validated = True
        ...         return True
        ...     def preload(self) -> bool:
        ...         self.is_preloaded = True
        ...         return True
        ...     def execute(self) -> int:
        ...         return 0
        >>> cmd = TestCommand()
        >>> cmd.validate()
        True
        >>> cmd.preload()
        True
        >>> cmd.is_preloaded
        True
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        raise NotImplementedError(
            f"El método preload() debe ser implementado en {self.__class__.__name__}"
        )
    
    @abstractmethod
    def execute(self) -> int:
        """
        Ejecuta la lógica principal del comando.
        
        Método abstracto que debe ser implementado por cada comando específico.
        Contiene el núcleo funcional del comando y debe retornar un código
        de salida apropiado (0 para éxito, >0 para errores).
        
        Returns
        -------
        int
            Código de salida (0 para éxito, 1+ para diferentes tipos de error)
            
        Raises
        ------
        NotImplementedError
            Si el método no es implementado en la clase hija
            
        Examples
        --------
        >>> class TestCommand(BaseCommand):
        ...     def validate(self) -> bool:
        ...         self.is_validated = True
        ...         return True
        ...     def preload(self) -> bool:
        ...         self.is_preloaded = True
        ...         return True
        ...     def execute(self) -> int:
        ...         return 0
        >>> cmd = TestCommand()
        >>> cmd.validate()
        True
        >>> cmd.preload() 
        True
        >>> cmd.execute()
        0
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        raise NotImplementedError(
            f"El método execute() debe ser implementado en {self.__class__.__name__}"
        )
    
    def is_valid_for_execution(self) -> bool:
        """
        Verifica si el comando está en un estado válido para ejecutarse.
        
        Comprueba que tanto la validación como la precarga hayan sido
        completadas exitosamente antes de permitir la ejecución del comando.
        
        Returns
        -------
        bool
            True si el comando puede ejecutarse, False en caso contrario
            
        Examples
        --------
        >>> class TestCommand(BaseCommand):
        ...     def validate(self) -> bool:
        ...         self.is_validated = True
        ...         return True
        ...     def preload(self) -> bool:
        ...         self.is_preloaded = True
        ...         return True
        ...     def execute(self) -> int:
        ...         return 0
        >>> cmd = TestCommand()
        >>> cmd.is_valid_for_execution()
        False
        >>> cmd.validate()
        True
        >>> cmd.is_valid_for_execution()
        False
        >>> cmd.preload()
        True
        >>> cmd.is_valid_for_execution()
        True
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        return self.is_validated and self.is_preloaded
    
    def get_command_info(self) -> Dict[str, Any]:
        """
        Retorna información de estado del comando.
        
        Proporciona un resumen del estado actual del comando incluyendo
        argumentos, estados de validación y precarga.
        
        Returns
        -------
        Dict[str, Any]
            Diccionario con información del comando
            
        Examples
        --------
        >>> cmd = BaseCommand({"test": "value"})
        >>> info = cmd.get_command_info()
        >>> info["command_class"]
        'BaseCommand'
        >>> info["args_count"]
        1
        >>> info["is_validated"]
        False
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        return {
            "command_class": self.__class__.__name__,
            "description": self.description,
            "args": self.args,
            "args_count": len(self.args),
            "args_keys": list(self.args.keys()),
            "is_validated": self.is_validated,
            "is_preloaded": self.is_preloaded,
            "ready_for_execution": self.is_valid_for_execution()
        }
    
    def run_command_cycle(self) -> int:
        """
        Ejecuta el ciclo completo del comando: validate -> preload -> execute.
        
        Método de conveniencia que ejecuta la secuencia estándar de un comando,
        verificando cada paso y retornando códigos de error apropiados.
        
        Returns
        -------
        int
            Código de salida del comando (0 éxito, 1+ error en diferentes fases)
            
        Examples
        --------
        >>> class TestCommand(BaseCommand):
        ...     def validate(self) -> bool:
        ...         self.is_validated = True
        ...         return True
        ...     def preload(self) -> bool:
        ...         self.is_preloaded = True
        ...         return True
        ...     def execute(self) -> int:
        ...         return 0
        >>> cmd = TestCommand()
        >>> cmd.run_command_cycle()
        0
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        logger.debug("Iniciando ciclo completo de comando", detail=self.get_command_info())
        
        # Fase 1: Validación
        if not self.validate():
            logger.error("Fallo en la validación del comando", detail={
                "command_class": self.__class__.__name__,
                "args": self.args
            })
            return 1
            
        # Fase 2: Precarga
        if not self.preload():
            logger.error("Fallo en la precarga del comando", detail={
                "command_class": self.__class__.__name__,
                "validation_status": self.is_validated
            })
            return 2
            
        # Fase 3: Ejecución
        try:
            result = self.execute()
            logger.success("Ciclo de comando completado exitosamente", detail={
                "command_class": self.__class__.__name__,
                "exit_code": result
            })
            return result
        except Exception:
            logger.critical("Error durante la ejecución del comando", detail={
                "command_class": self.__class__.__name__
            })
            return 3


# API pública del módulo
__all__ = [
    'BaseCommand'
]