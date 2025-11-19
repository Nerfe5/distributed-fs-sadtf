"""
config_manager.py
=================
Módulo para gestionar la configuración del sistema SADTF.

Este módulo lee el archivo config.json y proporciona acceso
a los parámetros de configuración en todo el sistema.

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfigManager:
    """
    Gestor de configuración del sistema.
    
    Lee y valida el archivo config.json y proporciona métodos
    para acceder a los diferentes parámetros del sistema.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_path: Ruta al archivo config.json. Si es None,
                        busca en la ruta por defecto ../config/config.json
        """
        if config_path is None:
            # Obtener la ruta del directorio del proyecto
            # Este archivo está en src/, el config está en config/
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.json"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Carga la configuración desde el archivo JSON.
        
        Raises:
            FileNotFoundError: Si el archivo config.json no existe
            json.JSONDecodeError: Si el archivo JSON está mal formado
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Archivo de configuración no encontrado: {self.config_path}"
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✓ Configuración cargada desde: {self.config_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Error al parsear config.json: {e.msg}",
                e.doc,
                e.pos
            )
    
    def reload(self) -> None:
        """
        Recarga la configuración desde el archivo.
        Útil si el archivo cambia durante la ejecución.
        """
        self._load_config()
    
    # ========================================================================
    # Métodos para acceder a configuración del sistema
    # ========================================================================
    
    def get_system_name(self) -> str:
        """Retorna el nombre del sistema (SADTF)."""
        return self.config.get("sistema", {}).get("nombre", "SADTF")
    
    def get_system_version(self) -> str:
        """Retorna la versión del sistema."""
        return self.config.get("sistema", {}).get("version", "1.0.0")
    
    # ========================================================================
    # Métodos para acceder a configuración de almacenamiento
    # ========================================================================
    
    def get_block_size_mb(self) -> int:
        """Retorna el tamaño de bloque en MB (por defecto 1 MB)."""
        return self.config.get("almacenamiento", {}).get("tamaño_bloque_mb", 1)
    
    def get_block_size_bytes(self) -> int:
        """Retorna el tamaño de bloque en bytes."""
        return self.get_block_size_mb() * 1024 * 1024
    
    def get_shared_space_size_mb(self) -> int:
        """Retorna el tamaño del espacio compartido en MB."""
        return self.config.get("almacenamiento", {}).get(
            "tamaño_espacio_compartido_mb", 70
        )
    
    def get_blocks_directory(self) -> Path:
        """
        Retorna la ruta completa al directorio de bloques (espacioCompartido).
        """
        project_root = Path(__file__).parent.parent
        dir_name = self.config.get("almacenamiento", {}).get(
            "directorio_bloques", "espacioCompartido"
        )
        return project_root / dir_name
    
    def get_metadata_directory(self) -> Path:
        """Retorna la ruta completa al directorio de metadatos."""
        project_root = Path(__file__).parent.parent
        dir_name = self.config.get("almacenamiento", {}).get(
            "directorio_metadata", "metadata"
        )
        return project_root / dir_name
    
    def get_logs_directory(self) -> Path:
        """Retorna la ruta completa al directorio de logs."""
        project_root = Path(__file__).parent.parent
        dir_name = self.config.get("almacenamiento", {}).get(
            "directorio_logs", "logs"
        )
        return project_root / dir_name
    
    # ========================================================================
    # Métodos para acceder a configuración de red
    # ========================================================================
    
    def get_coordinator_port(self) -> int:
        """Retorna el puerto del coordinador."""
        return self.config.get("red", {}).get("puerto_coordinador", 5000)
    
    def get_node_port(self) -> int:
        """Retorna el puerto por defecto de los nodos."""
        return self.config.get("red", {}).get("puerto_nodo", 5001)
    
    def get_timeout_seconds(self) -> int:
        """Retorna el timeout en segundos para operaciones de red."""
        return self.config.get("red", {}).get("timeout_segundos", 5)
    
    def get_heartbeat_interval(self) -> int:
        """Retorna el intervalo de heartbeat en segundos."""
        return self.config.get("red", {}).get("intervalo_heartbeat_segundos", 3)
    
    # ========================================================================
    # Métodos para acceder a configuración de nodos
    # ========================================================================
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Retorna la lista completa de nodos configurados.
        
        Returns:
            Lista de diccionarios con información de cada nodo:
            - id: Identificador único del nodo
            - nombre: Nombre descriptivo
            - ip: Dirección IP
            - puerto: Puerto de escucha
            - capacidad_mb: Capacidad en MB
            - activo: Si está activo inicialmente
            - es_coordinador: Si es el coordinador
        """
        return self.config.get("nodos", [])
    
    def get_node_by_id(self, node_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de un nodo específico por su ID.
        
        Args:
            node_id: ID del nodo a buscar
            
        Returns:
            Diccionario con la configuración del nodo, o None si no existe
        """
        for node in self.get_nodes():
            if node.get("id") == node_id:
                return node
        return None
    
    def get_coordinator_node(self) -> Optional[Dict[str, Any]]:
        """
        Retorna el nodo configurado como coordinador.
        
        Returns:
            Diccionario con la configuración del coordinador, o None
        """
        for node in self.get_nodes():
            if node.get("es_coordinador", False):
                return node
        return None
    
    def get_total_capacity_mb(self) -> int:
        """
        Calcula la capacidad total del sistema en MB.
        
        Returns:
            Suma de las capacidades de todos los nodos activos
        """
        total = 0
        for node in self.get_nodes():
            if node.get("activo", False):
                total += node.get("capacidad_mb", 0)
        return total
    
    def get_total_blocks(self) -> int:
        """
        Calcula el número total de bloques en el sistema.
        
        Returns:
            Total de bloques = capacidad_total_mb / tamaño_bloque_mb
        """
        return self.get_total_capacity_mb() // self.get_block_size_mb()
    
    # ========================================================================
    # Métodos para acceder a configuración de replicación
    # ========================================================================
    
    def get_num_replicas(self) -> int:
        """
        Retorna el número de réplicas por bloque.
        Por defecto 1 (significa 2 copias totales: original + 1 réplica).
        """
        return self.config.get("replicacion", {}).get("numero_replicas", 1)
    
    def get_replication_strategy(self) -> str:
        """Retorna la estrategia de replicación."""
        return self.config.get("replicacion", {}).get("estrategia", "distribuida")
    
    # ========================================================================
    # Métodos para acceder a configuración de seguridad
    # ========================================================================
    
    def should_verify_integrity(self) -> bool:
        """Retorna si se debe verificar la integridad de los archivos."""
        return self.config.get("seguridad", {}).get("verificar_integridad", True)
    
    def get_hash_algorithm(self) -> str:
        """Retorna el algoritmo de hash a usar (sha256, md5, etc.)."""
        return self.config.get("seguridad", {}).get("algoritmo_hash", "sha256")
    
    # ========================================================================
    # Métodos para acceder a configuración de GUI
    # ========================================================================
    
    def get_gui_title(self) -> str:
        """Retorna el título de la ventana de la GUI."""
        return self.config.get("gui", {}).get("titulo", "SADTF")
    
    def get_gui_width(self) -> int:
        """Retorna el ancho de la ventana de la GUI."""
        return self.config.get("gui", {}).get("ancho", 900)
    
    def get_gui_height(self) -> int:
        """Retorna el alto de la ventana de la GUI."""
        return self.config.get("gui", {}).get("alto", 500)
    
    def get_gui_header_color(self) -> str:
        """Retorna el color del header de la GUI."""
        return self.config.get("gui", {}).get("color_header", "#1B5E7E")
    
    def get_gui_update_interval(self) -> int:
        """Retorna el intervalo de actualización de la GUI en segundos."""
        return self.config.get("gui", {}).get("actualizar_cada_segundos", 2)
    
    # ========================================================================
    # Métodos de utilidad
    # ========================================================================
    
    def print_config_summary(self) -> None:
        """
        Imprime un resumen de la configuración actual.
        Útil para debugging y verificación.
        """
        print("\n" + "="*60)
        print(f"  {self.get_system_name()} v{self.get_system_version()}")
        print("="*60)
        print(f"\n📦 ALMACENAMIENTO:")
        print(f"   Tamaño de bloque: {self.get_block_size_mb()} MB")
        print(f"   Espacio por nodo: {self.get_shared_space_size_mb()} MB")
        print(f"   Capacidad total: {self.get_total_capacity_mb()} MB")
        print(f"   Total de bloques: {self.get_total_blocks()}")
        
        print(f"\n🌐 RED:")
        print(f"   Puerto coordinador: {self.get_coordinator_port()}")
        print(f"   Timeout: {self.get_timeout_seconds()}s")
        print(f"   Heartbeat: {self.get_heartbeat_interval()}s")
        
        print(f"\n💻 NODOS CONFIGURADOS:")
        for node in self.get_nodes():
            coord = " [COORDINADOR]" if node.get("es_coordinador") else ""
            estado = "✓" if node.get("activo") else "✗"
            print(f"   {estado} Nodo {node['id']}: {node['nombre']} "
                  f"({node['ip']}:{node['puerto']}) - "
                  f"{node['capacidad_mb']} MB{coord}")
        
        print(f"\n🔄 REPLICACIÓN:")
        print(f"   Réplicas por bloque: {self.get_num_replicas()}")
        print(f"   Estrategia: {self.get_replication_strategy()}")
        
        print(f"\n🔒 SEGURIDAD:")
        print(f"   Verificar integridad: {self.should_verify_integrity()}")
        print(f"   Algoritmo hash: {self.get_hash_algorithm()}")
        
        print("\n" + "="*60 + "\n")


# ============================================================================
# Función de utilidad para obtener una instancia global de ConfigManager
# ============================================================================

_config_manager_instance = None


def get_config() -> ConfigManager:
    """
    Retorna una instancia global de ConfigManager (patrón Singleton).
    
    Esta función facilita el acceso a la configuración desde cualquier
    parte del código sin tener que pasar el objeto ConfigManager.
    
    Returns:
        Instancia de ConfigManager
    
    Example:
        >>> from config_manager import get_config
        >>> config = get_config()
        >>> block_size = config.get_block_size_mb()
    """
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance


# ============================================================================
# Código de prueba (se ejecuta solo si se corre este archivo directamente)
# ============================================================================

if __name__ == "__main__":
    print("Probando ConfigManager...\n")
    
    try:
        # Crear instancia del gestor de configuración
        config = ConfigManager()
        
        # Imprimir resumen de la configuración
        config.print_config_summary()
        
        # Pruebas de acceso a diferentes parámetros
        print("🧪 PRUEBAS DE ACCESO:")
        print(f"   Tamaño de bloque en bytes: {config.get_block_size_bytes():,}")
        print(f"   Directorio de bloques: {config.get_blocks_directory()}")
        print(f"   Coordinador: {config.get_coordinator_node()['nombre']}")
        print(f"   GUI: {config.get_gui_width()}x{config.get_gui_height()}")
        
        print("\n✅ Todas las pruebas pasaron correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
