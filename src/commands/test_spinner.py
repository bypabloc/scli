from typing import Dict
from typing import Any
from typing import Optional
from time import sleep as time_sleep

from src.utils.logger import logger
from src.utils.spinner import create_spinner
from src.utils.base_command import BaseCommand


class TestSpinner(BaseCommand):
    """
    Comando para demostrar la funcionalidad del spinner dinámico de SCLI.
    
    Esta clase implementa una demostración completa del sistema de spinners,
    mostrando diferentes estados y transiciones durante un período de tiempo
    controlado para verificar la sincronización con el logger.
    """
    
    def __init__(self, args: Optional[Dict[str, Any]] = None):
        """
        Inicializa el comando TestSpinner.
        
        Parameters
        ----------
        args : Dict[str, Any], optional
            Argumentos del comando (conversión de tipos en preload)
            
        Examples
        --------
        >>> cmd = TestSpinner()
        >>> isinstance(cmd, TestSpinner)
        True
        
        >>> cmd = TestSpinner({"duration": "5"})
        >>> isinstance(cmd, TestSpinner)
        True
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        super().__init__(args)
        self.spinner = None
        self.total_duration = None  # Se definirá en preload()
        
    def validate(self) -> bool:
        """
        Valida argumentos básicos y capacidades del sistema.
        
        Verifica que la configuración del spinner esté disponible y que
        los argumentos proporcionados sean válidos antes de la conversión.
        
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
        """
        logger.debug("Validando comando TestSpinner", detail={
            "args_count": len(self.args),
            "args_keys": list(self.args.keys())
        })
        
        # Validar argumentos sin convertir tipos (eso se hace en preload)
        if "duration" in self.args:
            duration_raw = self.args["duration"]
            # Validar que pueda convertirse a entero
            try:
                duration_test = int(duration_raw)
                if duration_test <= 0:
                    logger.error("La duración debe ser mayor a 0", detail={
                        "provided_duration": duration_raw
                    })
                    return False
                if duration_test > 60:
                    logger.warning("Duración muy larga para test de spinner", detail={
                        "duration": duration_raw,
                        "recommended_max": 60
                    })
            except (ValueError, TypeError):
                logger.error("El valor de duration debe ser un número entero", detail={
                    "provided_value": duration_raw,
                    "provided_type": type(duration_raw).__name__
                })
                return False
            
        # Verificar que podemos crear un spinner
        try:
            test_spinner = create_spinner("Test validation")
            if test_spinner is None:
                logger.error("No se pudo crear instancia de spinner para validación")
                return False
        except Exception as e:
            logger.error("Error al validar spinner", detail={
                "error": str(e)
            })
            return False
            
        self.is_validated = True
        logger.debug("Validación de TestSpinner completada exitosamente")
        
        return True
        
    def preload(self) -> bool:
        """
        Precarga recursos, convierte tipos de argumentos y prepara el spinner.
        
        Define y convierte los tipos esperados de argumentos:
        - duration: int (segundos de duración, default: 8)
        
        Returns
        -------
        bool
            True si la precarga es exitosa, False en caso contrario
            
        Examples
        --------
        >>> cmd = TestSpinner()
        >>> cmd.validate()
        True
        >>> cmd.preload()
        True
        
        >>> cmd.total_duration
        8
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        if not self.is_validated:
            logger.error("No se puede precargar: el comando no ha sido validado")
            return False
            
        logger.debug("Precargando recursos para TestSpinner", detail={
            "validation_status": self.is_validated,
            "raw_args": self.args
        })
        
        # Definir y convertir tipos de argumentos esperados
        try:
            # duration: int (segundos de duración)
            duration_raw = self.args.get("duration", 8)
            if duration_raw == 8:  # Valor por defecto
                self.total_duration = 8
            else:
                self.total_duration = self._convert_to_int("duration", duration_raw, default=8)
                
            logger.debug("Argumentos procesados", detail={
                "total_duration": self.total_duration,
                "duration_type": type(self.total_duration).__name__
            })
            
        except Exception as e:
            logger.error("Error al convertir argumentos", detail={
                "error": str(e),
                "args": self.args
            })
            return False
        
        # Crear spinner con configuración de app_config
        try:
            self.spinner = create_spinner("Initializing test")
            if self.spinner is None:
                logger.error("No se pudo crear el spinner durante la precarga")
                return False
        except Exception as e:
            logger.error("Error al crear spinner en precarga", detail={
                "error": str(e)
            })
            return False
            
        self.is_preloaded = True
        logger.debug("Precarga de TestSpinner completada exitosamente")
        
        return True
    
    def _convert_to_int(self, param_name: str, value: Any, default: int) -> int:
        """
        Convierte un valor a entero con validación y logging.
        
        Parameters
        ----------
        param_name : str
            Nombre del parámetro para logging
        value : Any
            Valor a convertir
        default : int
            Valor por defecto si la conversión falla
            
        Returns
        -------
        int
            Valor convertido o default
            
        Examples
        --------
        >>> cmd = TestSpinner()
        >>> cmd._convert_to_int("duration", "10", 8)
        10
        
        >>> cmd._convert_to_int("duration", "invalid", 8)
        8
        
        :Authors:
            - Pablo Contreras
            
        :Created:
            - 2025-08-31
        """
        try:
            converted = int(value)
            logger.debug(f"Conversión exitosa: {param_name}", detail={
                "original": value,
                "converted": converted,
                "type": type(converted).__name__
            })
            return converted
        except (ValueError, TypeError) as e:
            logger.warning(f"Conversión fallida para {param_name}, usando default", detail={
                "original_value": value,
                "original_type": type(value).__name__,
                "default_value": default,
                "error": str(e)
            })
            return default
        
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
            # Calcular duración por fase
            phase_duration = self.total_duration / 4
            
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
            
        except Exception as e:
            if self.spinner:
                self.spinner.stop("❌ Spinner test failed")
            logger.error("Error durante la ejecución del test de spinner", detail={
                "error": str(e)
            })
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