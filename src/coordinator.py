"""
coordinator.py
==============
Módulo del coordinador maestro del sistema SADTF.

Este módulo se encarga de:
- Coordinar todos los nodos del sistema
- Mantener la tabla de bloques global
- Asignar bloques a nodos (balanceo de carga)
- Detectar nodos activos/caídos (heartbeat)
- Gestionar operaciones de archivos
- Sincronizar metadatos entre nodos

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.config_manager import get_config
from src.metadata_manager import MetadataManager
from src.network import NetworkManager, NetworkMessage


class NodeStatus:
    """Estado de un nodo en el sistema."""
    
    def __init__(self, node_id: int, ip: str, puerto: int, capacidad_mb: int):
        self.node_id = node_id
        self.ip = ip
        self.puerto = puerto
        self.capacidad_mb = capacidad_mb
        self.activo = False
        self.ultimo_heartbeat = 0
        self.bloques_usados = 0
        self.bloques_disponibles = capacidad_mb  # 1 bloque = 1 MB


class Coordinator:
    """
    Coordinador maestro del sistema de archivos distribuido.
    
    Gestiona:
    - Metadatos globales
    - Estado de nodos
    - Asignación de bloques
    - Operaciones de archivos
    """
    
    def __init__(self, node_id: int):
        """
        Inicializa el coordinador.
        
        Args:
            node_id: ID de este nodo (debe ser el coordinador en config)
        """
        self.node_id = node_id
        self.config = get_config()
        
        # Verificar que este nodo sea el coordinador
        node_config = self.config.get_node_by_id(node_id)
        if not node_config or not node_config.get('es_coordinador', False):
            raise ValueError(f"El nodo {node_id} no está configurado como coordinador")
        
        self.node_ip = node_config['ip']
        self.node_port = node_config['puerto']
        
        # Configurar logging
        self.logger = logging.getLogger(f"Coordinator-Node{node_id}")
        self.logger.setLevel(logging.INFO)
        
        # Inicializar gestor de metadatos
        metadata_dir = self.config.get_metadata_directory()
        total_blocks = self.config.get_total_blocks()
        self.metadata = MetadataManager(str(metadata_dir), total_blocks)
        
        # Inicializar gestor de red
        self.network = NetworkManager(
            node_id=node_id,
            host=self.node_ip,
            port=self.node_port,
            timeout=self.config.get_timeout_seconds()
        )
        
        # Estado de nodos
        self.nodes: Dict[int, NodeStatus] = {}
        self._initialize_nodes()
        
        # Control de ejecución
        self.is_running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        
        # Registrar handlers de red
        self._register_network_handlers()
        
        self.logger.info(f"✅ Coordinador inicializado en {self.node_ip}:{self.node_port}")
    
    # ========================================================================
    # Inicialización
    # ========================================================================
    
    def _initialize_nodes(self) -> None:
        """Inicializa el estado de todos los nodos del sistema."""
        for node_config in self.config.get_nodes():
            node_id = node_config['id']
            
            # Crear estado del nodo
            self.nodes[node_id] = NodeStatus(
                node_id=node_id,
                ip=node_config['ip'],
                puerto=node_config['puerto'],
                capacidad_mb=node_config['capacidad_mb']
            )
            
            # El coordinador siempre está activo
            if node_id == self.node_id:
                self.nodes[node_id].activo = True
                self.nodes[node_id].ultimo_heartbeat = time.time()
        
        self.logger.info(f"Nodos inicializados: {len(self.nodes)} nodos")
    
    def _register_network_handlers(self) -> None:
        """Registra handlers para mensajes de red."""
        self.network.register_handler(
            NetworkMessage.PING,
            self._handle_ping
        )
        self.network.register_handler(
            NetworkMessage.GET_STATUS,
            self._handle_get_status
        )
        # Más handlers se agregarán según sea necesario
    
    # ========================================================================
    # Control del coordinador
    # ========================================================================
    
    def start(self) -> bool:
        """
        Inicia el coordinador.
        
        Returns:
            True si se inició correctamente
        """
        print("\n" + "="*70)
        print("  🚀 INICIANDO COORDINADOR SADTF")
        print("="*70)
        print(f"Nodo ID: {self.node_id}")
        print(f"Dirección: {self.node_ip}:{self.node_port}")
        print(f"Bloques totales: {self.config.get_total_blocks()}")
        print(f"Capacidad total: {self.config.get_total_capacity_mb()} MB")
        print("="*70 + "\n")
        
        # Iniciar servidor de red
        if not self.network.start_server():
            self.logger.error("❌ Error al iniciar servidor de red")
            return False
        
        # Iniciar thread de heartbeat
        self.is_running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self.heartbeat_thread.start()
        
        # Detectar nodos activos
        self._discover_nodes()
        
        # Mostrar estadísticas iniciales
        self._print_status()
        
        self.logger.info("✅ Coordinador iniciado correctamente")
        return True
    
    def stop(self) -> None:
        """Detiene el coordinador."""
        print("\n🛑 Deteniendo coordinador...")
        
        self.is_running = False
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
        
        self.network.stop_server()
        
        self.logger.info("Coordinador detenido")
        print("👋 Coordinador detenido correctamente\n")
    
    # ========================================================================
    # Heartbeat y detección de nodos
    # ========================================================================
    
    def _heartbeat_loop(self) -> None:
        """Loop de heartbeat para detectar nodos activos."""
        interval = self.config.get_heartbeat_interval()
        
        while self.is_running:
            self._check_nodes_health()
            time.sleep(interval)
    
    def _discover_nodes(self) -> None:
        """Descubre nodos activos en el sistema."""
        print("🔍 Descubriendo nodos activos...")
        
        for node_id, node in self.nodes.items():
            if node_id == self.node_id:
                continue  # Saltar el coordinador mismo
            
            # Hacer ping al nodo
            if self.network.ping_node(node.ip, node.puerto):
                node.activo = True
                node.ultimo_heartbeat = time.time()
                print(f"   ✅ Nodo {node_id} ({node.ip}:{node.puerto}) - ACTIVO")
            else:
                node.activo = False
                print(f"   ❌ Nodo {node_id} ({node.ip}:{node.puerto}) - INACTIVO")
        
        print()
    
    def _check_nodes_health(self) -> None:
        """Verifica el estado de salud de todos los nodos."""
        timeout = self.config.get_timeout_seconds()
        current_time = time.time()
        
        for node_id, node in self.nodes.items():
            if node_id == self.node_id:
                continue  # El coordinador siempre está activo
            
            # Si el nodo está marcado como activo, verificar heartbeat
            if node.activo:
                time_since_heartbeat = current_time - node.ultimo_heartbeat
                
                if time_since_heartbeat > (timeout * 3):
                    # Hacer ping para confirmar
                    if not self.network.ping_node(node.ip, node.puerto):
                        node.activo = False
                        self.logger.warning(
                            f"⚠️ Nodo {node_id} marcado como INACTIVO "
                            f"(sin respuesta por {time_since_heartbeat:.1f}s)"
                        )
                    else:
                        node.ultimo_heartbeat = current_time
    
    def get_active_nodes(self) -> List[int]:
        """
        Obtiene lista de nodos activos (excluyendo coordinador).
        
        Returns:
            Lista de IDs de nodos activos
        """
        return [
            node_id for node_id, node in self.nodes.items()
            if node.activo and node_id != self.node_id
        ]
    
    # ========================================================================
    # Asignación de bloques
    # ========================================================================
    
    def assign_blocks_for_file(
        self,
        num_blocks: int
    ) -> List[Tuple[int, int, int]]:
        """
        Asigna bloques para un archivo con replicación.
        
        Args:
            num_blocks: Número de bloques necesarios
            
        Returns:
            Lista de tuplas (block_id, nodo_primario, nodo_replica)
            
        Raises:
            ValueError: Si no hay suficientes bloques o nodos
        """
        # Obtener bloques libres
        free_blocks = self.metadata.get_free_blocks(num_blocks)
        
        # Obtener nodos activos
        active_nodes = self.get_active_nodes()
        
        if len(active_nodes) < 2:
            raise ValueError(
                "Se necesitan al menos 2 nodos activos para replicación. "
                f"Activos: {len(active_nodes)}"
            )
        
        # Asignar bloques usando round-robin con replicación
        assignments = []
        
        for i, block_id in enumerate(free_blocks):
            # Seleccionar nodo primario (round-robin)
            primary_node = active_nodes[i % len(active_nodes)]
            
            # Seleccionar nodo réplica (siguiente en la lista)
            replica_node = active_nodes[(i + 1) % len(active_nodes)]
            
            # Asegurar que sean diferentes
            if primary_node == replica_node and len(active_nodes) > 1:
                replica_node = active_nodes[(i + 2) % len(active_nodes)]
            
            assignments.append((block_id, primary_node, replica_node))
        
        return assignments
    
    # ========================================================================
    # Handlers de red
    # ========================================================================
    
    def _handle_ping(self, message: NetworkMessage) -> NetworkMessage:
        """Handler para mensajes PING."""
        sender_id = message.sender
        
        # Actualizar heartbeat del nodo
        if sender_id in self.nodes:
            self.nodes[sender_id].activo = True
            self.nodes[sender_id].ultimo_heartbeat = time.time()
        
        return NetworkMessage(NetworkMessage.PONG, {}, self.node_id)
    
    def _handle_get_status(self, message: NetworkMessage) -> NetworkMessage:
        """Handler para solicitud de estado."""
        stats = self.metadata.get_statistics()
        
        active_nodes = self.get_active_nodes()
        
        status = {
            'status': 'online',
            'node_id': self.node_id,
            'role': 'coordinator',
            'total_blocks': stats['total_blocks'],
            'used_blocks': stats['used_blocks'],
            'free_blocks': stats['free_blocks'],
            'usage_percentage': stats['usage_percentage'],
            'total_files': stats['total_files'],
            'active_nodes': len(active_nodes) + 1,  # +1 por el coordinador
            'nodes_list': active_nodes + [self.node_id]
        }
        
        return NetworkMessage(
            NetworkMessage.STATUS_RESPONSE,
            status,
            self.node_id
        )
    
    # ========================================================================
    # Utilidades y visualización
    # ========================================================================
    
    def _print_status(self) -> None:
        """Imprime el estado actual del sistema."""
        print("\n" + "="*70)
        print("  📊 ESTADO DEL SISTEMA")
        print("="*70)
        
        # Estado de nodos
        print("\n💻 NODOS:")
        for node_id, node in sorted(self.nodes.items()):
            status = "✅ ACTIVO" if node.activo else "❌ INACTIVO"
            role = " [COORDINADOR]" if node_id == self.node_id else ""
            print(f"   Nodo {node_id}: {status} - {node.ip}:{node.puerto}{role}")
        
        # Estadísticas de metadatos
        stats = self.metadata.get_statistics()
        print("\n📦 ALMACENAMIENTO:")
        print(f"   Total de bloques: {stats['total_blocks']}")
        print(f"   Bloques usados: {stats['used_blocks']}")
        print(f"   Bloques libres: {stats['free_blocks']}")
        print(f"   Uso: {stats['usage_percentage']:.1f}%")
        print(f"   Archivos: {stats['total_files']}")
        print(f"   Tamaño total: {stats['total_size_mb']:.2f} MB")
        
        print("="*70 + "\n")
    
    def print_detailed_status(self) -> None:
        """Imprime estado detallado con tablas."""
        self._print_status()
        self.metadata.print_file_index()
        self.metadata.print_block_table(max_entries=15)
    
    def run_interactive(self) -> None:
        """
        Ejecuta el coordinador en modo interactivo.
        Muestra menú y permite operaciones manuales.
        """
        if not self.start():
            return
        
        print("\n🎮 MODO INTERACTIVO")
        print("Comandos disponibles:")
        print("  status  - Ver estado del sistema")
        print("  nodes   - Listar nodos")
        print("  files   - Listar archivos")
        print("  table   - Ver tabla de bloques")
        print("  refresh - Re-descubrir nodos")
        print("  quit    - Salir")
        print()
        
        try:
            while True:
                cmd = input("coordinator> ").strip().lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'status':
                    self._print_status()
                elif cmd == 'nodes':
                    print("\n💻 Nodos activos:")
                    for node_id in self.get_active_nodes():
                        node = self.nodes[node_id]
                        print(f"   Nodo {node_id}: {node.ip}:{node.puerto}")
                    print()
                elif cmd == 'files':
                    self.metadata.print_file_index()
                elif cmd == 'table':
                    self.metadata.print_block_table(max_entries=20)
                elif cmd == 'refresh':
                    self._discover_nodes()
                elif cmd == 'help':
                    print("\nComandos: status, nodes, files, table, refresh, quit")
                elif cmd == '':
                    continue
                else:
                    print(f"Comando desconocido: '{cmd}'. Escribe 'help' para ver comandos.")
        
        except KeyboardInterrupt:
            print("\n")
        
        finally:
            self.stop()


# ============================================================================
# Código de prueba
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("  Probando Coordinator")
    print("="*70)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Crear coordinador (Nodo 1 según config)
        coordinator = Coordinator(node_id=1)
        
        # Ejecutar en modo interactivo
        coordinator.run_interactive()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
