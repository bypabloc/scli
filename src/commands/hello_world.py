from typing import Dict
from typing import Any
from typing import Optional

from src.utils.logger import logger
from src.utils.base_command import BaseCommand


class HelloWorld(BaseCommand):
    """
    Comando simple que demuestra la estructura básica de un comando en SCLI.
    
    Esta clase implementa un comando "hello world" que valida prerrequisitos,
    precarga recursos necesarios y ejecuta un saludo simple usando el logger.
    """
    
    def validate(self) -> bool:
        """
        Valida que el comando pueda ejecutarse correctamente.
        
        Verifica prerrequisitos y condiciones necesarias para la ejecución
        del comando. En este caso simple, siempre retorna True.
        
        Returns
        -------
        bool
            True si la validación es exitosa, False en caso contrario
            
        Examples
        --------
        >>> cmd = HelloWorld()
        >>> cmd.validate()
        True
        
        >>> cmd.is_validated
        True
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        logger.debug("Validando comando HelloWorld", detail={
            "args_count": len(self.args),
            "args_keys": list(self.args.keys())
        })
        
        # Validación simple: siempre exitosa para este comando básico
        self.is_validated = True
        logger.debug("Validación de HelloWorld completada exitosamente")
        
        return True
        
    def preload(self) -> bool:
        """
        Precarga recursos y prepara el entorno para la ejecución del comando.
        
        Realiza tareas de inicialización como cargar configuraciones,
        establecer conexiones o preparar datos necesarios.
        
        Returns
        -------
        bool
            True si la precarga es exitosa, False en caso contrario
            
        Examples
        --------
        >>> cmd = HelloWorld()
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
        if not self.is_validated:
            logger.error("No se puede precargar: el comando no ha sido validado")
            return False
            
        logger.debug("Precargando recursos para HelloWorld", detail={
            "validation_status": self.is_validated,
            "args": self.args
        })
        
        # Precarga simple: preparar mensaje personalizado si hay nombre
        if "name" in self.args:
            logger.debug("Preparando saludo personalizado", detail={
                "target_name": self.args["name"]
            })
        
        self.is_preloaded = True
        logger.debug("Precarga de HelloWorld completada exitosamente")
        
        return True
        
    def execute(self) -> int:
        """
        Ejecuta la lógica principal del comando HelloWorld.
        
        Núcleo del comando que realiza la acción principal: mostrar
        un saludo "hola mundo" usando el logger del sistema.
        
        Returns
        -------
        int
            Código de salida (0 para éxito, 1 para error)
            
        Examples
        --------
        >>> cmd = HelloWorld()
        >>> cmd.validate()
        True
        >>> cmd.preload()
        True
        >>> cmd.execute()
        0
        
        >>> cmd_with_name = HelloWorld({"name": "Pablo"})
        >>> cmd_with_name.validate()
        True
        >>> cmd_with_name.preload()
        True
        >>> cmd_with_name.execute()
        0
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        if not self.is_validated:
            logger.error("No se puede ejecutar: el comando no ha sido validado")
            return 1
            
        if not self.is_preloaded:
            logger.error("No se puede ejecutar: el comando no ha sido precargado")
            return 1
            
        logger.info("Ejecutando comando HelloWorld", detail={
            "validation_status": self.is_validated,
            "preload_status": self.is_preloaded,
            "args_provided": len(self.args) > 0
        })
        
        # Núcleo del comando: saludo personalizado o genérico
        if "name" in self.args and self.args["name"]:
            logger.success(f"¡Hola mundo, {self.args['name']}!")
        else:
            logger.success("¡Hola mundo!")
            
        logger.info("Comando HelloWorld ejecutado exitosamente")
        return 0


# Función de conveniencia para crear y ejecutar el comando
def create_hello_world_command(args: Optional[Dict[str, Any]] = None) -> HelloWorld:
    """
    Crea una instancia del comando HelloWorld con los argumentos dados.
    
    Parameters
    ----------
    args : Dict[str, Any], optional
        Argumentos para el comando
        
    Returns
    -------
    HelloWorld
        Instancia configurada del comando
        
    Examples
    --------
    >>> cmd = create_hello_world_command()
    >>> isinstance(cmd, HelloWorld)
    True
    
    >>> cmd = create_hello_world_command({"name": "Mundo"})
    >>> cmd.args["name"]
    'Mundo'
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return HelloWorld(args)


# Función para ejecutar el ciclo completo del comando
def run_hello_world_command(args: Optional[Dict[str, Any]] = None) -> int:
    """
    Ejecuta el ciclo completo del comando HelloWorld usando BaseCommand.
    
    Parameters
    ----------
    args : Dict[str, Any], optional
        Argumentos para el comando
        
    Returns
    -------
    int
        Código de salida del comando (0 éxito, 1+ error)
        
    Examples
    --------
    >>> result = run_hello_world_command()
    >>> result in [0, 1, 2, 3]
    True
    
    >>> result = run_hello_world_command({"name": "Usuario"})
    >>> result in [0, 1, 2, 3]
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    cmd = create_hello_world_command(args)
    return cmd.run_command_cycle()


# API pública del módulo
__all__ = [
    'HelloWorld',
    'create_hello_world_command', 
    'run_hello_world_command'
]