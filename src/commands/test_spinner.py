from typing import Dict
from typing import Any
from typing import Optional
from time import sleep as time_sleep

from pydantic import BaseModel
from pydantic import Field

from src.utils.logger import logger
from src.utils.spinner import create_spinner
from src.utils.base_command import BaseCommand


class TestSpinnerArgs(BaseModel):
    """
    Modelo de validación para los argumentos del comando TestSpinner.
    
    Attributes
    ----------
    duration : int
        Duración en segundos para la demostración del spinner.
        Debe estar entre 1 y 60 segundos para evitar ejecuciones muy largas.
        
    Examples
    --------
    >>> args = TestSpinnerArgs()
    >>> args.duration
    8
    
    >>> args = TestSpinnerArgs(duration=5)
    >>> args.duration
    5
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    duration: int = Field(
        default=8,
        description="Duración en segundos para la demostración del spinner",
        ge=1,
        le=60,
        examples=[3, 5, 8, 10]
    )


class TestSpinner(BaseCommand):
    """
    Comando para demostrar la funcionalidad del spinner dinámico de SCLI.
    
    Esta clase implementa una demostración completa del sistema de spinners,
    mostrando diferentes estados y transiciones durante un período de tiempo
    controlado para verificar la sincronización con el logger.
    """
    
    description = "Comando para demostrar la funcionalidad del spinner dinámico de SCLI."
    order = 2
    args_model = TestSpinnerArgs
    
    def __init__(self, args: Optional[Dict[str, Any]] = None):
        """
        Inicializa el comando TestSpinner con validación Pydantic.
        
        Parameters
        ----------
        args : Dict[str, Any], optional
            Argumentos del comando (validados automáticamente con TestSpinnerArgs)
            
        Examples
        --------
        >>> cmd = TestSpinner()
        >>> isinstance(cmd, TestSpinner)
        True
        
        >>> cmd = TestSpinner({"duration": 5})
        >>> cmd.validated_args["duration"]
        5
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
            
        :Updated:
            - 2025-08-31 (Simplificado con validación Pydantic automática)
        """
        super().__init__(args)
        self.spinner = None
        # total_duration se obtiene directamente de validated_args
        
    def validate(self) -> bool:
        """
        Valida que el comando pueda ejecutarse correctamente.
        
        Con Pydantic, la validación de argumentos ya se hizo automáticamente
        en __init__, por lo que solo necesitamos verificar capacidades del sistema.
        
        Returns
        -------
        bool
            True si la validación es exitosa, False en caso contrario
            
        Examples
        --------
        >>> cmd = TestSpinner()
        >>> cmd.validate()
        True
        
        >>> cmd.is_validated
        True
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
            
        :Updated:
            - 2025-08-31 (Simplificado - Pydantic maneja validación de argumentos)
        """
        logger.debug("Validando comando TestSpinner", detail={
            "validated_args": self.validated_args
        })
        
        # Los argumentos ya fueron validados por Pydantic automáticamente
        # Solo verificamos que podemos crear un spinner
        try:
            test_spinner = create_spinner("Test validation")
            if test_spinner is None:
                logger.error("No se pudo crear instancia de spinner para validación")
                return False
        except Exception:
            logger.critical("Error al validar spinner")
            return False
            
        self.is_validated = True
        logger.debug("Validación de TestSpinner completada exitosamente")
        
        return True
        
    def preload(self) -> bool:
        """
        Precarga recursos y prepara el spinner para la demostración.
        
        Los argumentos ya fueron validados por Pydantic automáticamente,
        por lo que solo necesitamos preparar el spinner y recursos.
        
        Returns
        -------
        bool
            True si la precarga es exitosa, False en caso contrario
            
        Examples
        --------
        >>> cmd = TestSpinner({"duration": 5})
        >>> cmd.validate()
        True
        >>> cmd.preload()
        True
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
            
        :Updated:
            - 2025-08-31 (Simplificado con validación Pydantic automática)
        """
        if not self.is_validated:
            logger.error("No se puede precargar: el comando no ha sido validado")
            return False
            
        logger.debug("Precargando recursos para TestSpinner", detail={
            "validation_status": self.is_validated,
            "validated_args": self.validated_args,
            "duration": self.validated_args["duration"]
        })
        
        # Crear spinner - los argumentos ya están validados y convertidos por Pydantic
        try:
            self.spinner = create_spinner("Initializing test")
            if self.spinner is None:
                logger.error("No se pudo crear el spinner durante la precarga")
                return False
                
            logger.debug("Spinner creado exitosamente", detail={
                "duration_configured": self.validated_args["duration"]
            })
            
        except Exception:
            logger.critical("Error al crear spinner en precarga")
            return False
            
        self.is_preloaded = True
        logger.debug("Precarga de TestSpinner completada exitosamente")
        
        return True
    
    def execute(self) -> int:
        """
        Ejecuta la demostración completa del spinner.
        
        Núcleo del comando que realiza una demostración de 4 fases del spinner
        con diferentes textos y duraciones para mostrar las capacidades del
        sistema de animación.
        
        Returns
        -------
        int
            Código de salida (0 para éxito, 1 para error)
            
        Examples
        --------
        >>> cmd = TestSpinner({"duration": 2})
        >>> cmd.validate()
        True
        >>> cmd.preload()
        True
        >>> cmd.execute()  # doctest: +SKIP
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
            
        if self.spinner is None:
            logger.error("No se puede ejecutar: el spinner no fue inicializado")
            return 1
            
        logger.info("Starting spinner test demonstration")
        
        try:
            # Calcular duración por fase usando argumentos validados
            total_duration = self.validated_args["duration"]
            phase_duration = total_duration / 4
            
            # Iniciar spinner
            self.spinner.start()
            
            # Primera fase - Initialization
            logger.debug("Fase 1: Inicialización", detail={"duration": phase_duration})
            time_sleep(phase_duration)
            self.spinner.update_text("Loading configuration")
            
            # Segunda fase - Loading configuration
            logger.debug("Fase 2: Cargando configuración", detail={"duration": phase_duration})
            time_sleep(phase_duration)
            self.spinner.update_text("Processing data")
            
            # Tercera fase - Processing data
            logger.debug("Fase 3: Procesando datos", detail={"duration": phase_duration})
            time_sleep(phase_duration)
            self.spinner.update_text("Finalizing operations")
            
            # Cuarta fase - Finalizing operations
            logger.debug("Fase 4: Finalizando operaciones", detail={"duration": phase_duration})
            time_sleep(phase_duration)
            
            # Completar spinner
            self.spinner.stop()
            
        except Exception:
            if self.spinner:
                self.spinner.stop("❌ Spinner test failed")
            logger.critical("Error durante la ejecución del test de spinner")
            return 1
            
        logger.success("Spinner test demonstration completed")
        return 0


# Función de conveniencia para crear y ejecutar el comando
def create_test_spinner_command(args: Optional[Dict[str, Any]] = None) -> TestSpinner:
    """
    Crea una instancia del comando TestSpinner con los argumentos dados.
    
    Parameters
    ----------
    args : Dict[str, Any], optional
        Argumentos para el comando (ej: {"duration": 5})
        
    Returns
    -------
    TestSpinner
        Instancia configurada del comando
        
    Examples
    --------
    >>> cmd = create_test_spinner_command()
    >>> isinstance(cmd, TestSpinner)
    True
    
    >>> cmd = create_test_spinner_command({"duration": 3})
    >>> cmd.args["duration"]
    3
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    return TestSpinner(args)


# Función para ejecutar el ciclo completo del comando
def run_test_spinner_command(args: Optional[Dict[str, Any]] = None) -> int:
    """
    Ejecuta el ciclo completo del comando TestSpinner usando BaseCommand.
    
    Parameters
    ----------
    args : Dict[str, Any], optional
        Argumentos para el comando (ej: {"duration": 10})
        
    Returns
    -------
    int
        Código de salida del comando (0 éxito, 1+ error)
        
    Examples
    --------
    >>> result = run_test_spinner_command({"duration": 1})  # doctest: +SKIP
    >>> result in [0, 1, 2, 3]
    True
    
    :Authors:
        - Pablo Contreras
        
    :Created:
        - 2025-08-31
    """
    cmd = create_test_spinner_command(args)
    return cmd.run_command_cycle()


# API pública del módulo
__all__ = [
    'TestSpinner',
    'create_test_spinner_command', 
    'run_test_spinner_command'
]