"""
node.py
=======
Módulo del nodo trabajador del sistema SADTF.

Este módulo se encarga de:
- Almacenar bloques localmente en espacioCompartido/
- Responder a peticiones del coordinador
- Servir bloques a otros nodos
- Reportar estado y heartbeat al coordinador
- Gestionar espacio local disponible

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import threading
import time
import logging
from pathlib import Path
from typing import Optional, Dict

from src.config_manager import get_config
from src.block_manager import BlockManager
from src.network import NetworkManager, NetworkMessage


class Node:
    """
    Nodo trabajador del sistema de archivos distribuido.
    
    Almacena bloques localmente y responde a peticiones
    del coordinador y otros nodos.
    """
    
    def __init__(self, node_id: int):
        """
        Inicializa el nodo.
        
        Args:
            node_id: ID de este nodo
        """
        self.node_id = node_id
        self.config = get_config()
        
        # Verificar que el nodo existe en la configuración
        node_config = self.config.get_node_by_id(node_id)
        if not node_config:
            raise ValueError(f"El nodo {node_id} no existe en la configuración")
        
        self.node_ip = node_config['ip']
        self.node_port = node_config['puerto']
        self.capacidad_mb = node_config['capacidad_mb']
        self.es_coordinador = node_config.get('es_coordinador', False)
        
        # Configurar logging
        self.logger = logging.getLogger(f"Node{node_id}")
        self.logger.setLevel(logging.INFO)
        
        # Directorio local para bloques
        self.blocks_dir = self.config.get_blocks_directory()
        self.blocks_dir.mkdir(parents=True, exist_ok=True)
        
        # Gestor de bloques
        self.block_manager = BlockManager(
            block_size_bytes=self.config.get_block_size_bytes()
        )
        
        # Gestor de red
        self.network = NetworkManager(
            node_id=node_id,
            host=self.node_ip,
            port=self.node_port,
            timeout=self.config.get_timeout_seconds()
        )
        
        # Estado del nodo
        self.bloques_almacenados = 0
        self.bytes_usados = 0
        
        # Control de ejecución
        self.is_running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        
        # Obtener coordinador
        coordinator_config = self.config.get_coordinator_node()
        if coordinator_config:
            self.coordinator_ip = coordinator_config['ip']
            self.coordinator_port = coordinator_config['puerto']
        else:
            self.coordinator_ip = None
            self.coordinator_port = None
        
        # Registrar handlers de red
        self._register_network_handlers()
        
        self.logger.info(f"✅ Nodo {node_id} inicializado en {self.node_ip}:{self.node_port}")
    
    # ========================================================================
    # Inicialización
    # ========================================================================
    
    def _register_network_handlers(self) -> None:
        """Registra handlers para mensajes de red."""
        # Handlers básicos
        self.network.register_handler(
            NetworkMessage.PING,
            self._handle_ping
        )
        self.network.register_handler(
            NetworkMessage.GET_STATUS,
            self._handle_get_status
        )
        
        # Handlers de bloques
        self.network.register_handler(
            NetworkMessage.UPLOAD_BLOCK,
            self._handle_upload_block
        )
        self.network.register_handler(
            NetworkMessage.DOWNLOAD_BLOCK,
            self._handle_download_block
        )
        self.network.register_handler(
            NetworkMessage.DELETE_BLOCK,
            self._handle_delete_block
        )
    
    # ========================================================================
    # Control del nodo
    # ========================================================================
    
    def start(self) -> bool:
        """
        Inicia el nodo.
        
        Returns:
            True si se inició correctamente
        """
        print("\n" + "="*70)
        print(f"  🚀 INICIANDO NODO {self.node_id}")
        print("="*70)
        print(f"Dirección: {self.node_ip}:{self.node_port}")
        print(f"Capacidad: {self.capacidad_mb} MB")
        print(f"Rol: {'COORDINADOR' if self.es_coordinador else 'TRABAJADOR'}")
        print(f"Directorio: {self.blocks_dir}")
        print("="*70 + "\n")
        
        # Iniciar servidor de red
        if not self.network.start_server():
            self.logger.error("❌ Error al iniciar servidor de red")
            return False
        
        # Iniciar thread de heartbeat (si no es coordinador)
        if not self.es_coordinador and self.coordinator_ip:
            self.is_running = True
            self.heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                daemon=True
            )
            self.heartbeat_thread.start()
            print(f"💓 Heartbeat hacia coordinador: {self.coordinator_ip}:{self.coordinator_port}\n")
        
        # Calcular espacio usado
        self._calculate_space_usage()
        
        # Mostrar estado
        self._print_status()
        
        self.logger.info("✅ Nodo iniciado correctamente")
        return True
    
    def stop(self) -> None:
        """Detiene el nodo."""
        print(f"\n🛑 Deteniendo nodo {self.node_id}...")
        
        self.is_running = False
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
        
        self.network.stop_server()
        
        self.logger.info("Nodo detenido")
        print(f"👋 Nodo {self.node_id} detenido correctamente\n")
    
    # ========================================================================
    # Heartbeat al coordinador
    # ========================================================================
    
    def _heartbeat_loop(self) -> None:
        """Loop de heartbeat hacia el coordinador."""
        interval = self.config.get_heartbeat_interval()
        
        while self.is_running:
            self._send_heartbeat()
            time.sleep(interval)
    
    def _send_heartbeat(self) -> None:
        """Envía heartbeat al coordinador."""
        if not self.coordinator_ip or not self.coordinator_port:
            return
        
        # Hacer ping al coordinador
        success = self.network.ping_node(self.coordinator_ip, self.coordinator_port)
        
        if not success:
            self.logger.warning("⚠️ No se pudo contactar al coordinador")
    
    # ========================================================================
    # Gestión de bloques locales
    # ========================================================================
    
    def store_block(self, block_id: int, block_data: bytes, file_name: str) -> bool:
        """
        Almacena un bloque localmente.
        
        Args:
            block_id: ID del bloque
            block_data: Datos del bloque
            file_name: Nombre del archivo al que pertenece
            
        Returns:
            True si se almacenó correctamente
        """
        try:
            # Verificar espacio disponible
            if not self._has_space_for_block(len(block_data)):
                self.logger.error("❌ No hay espacio suficiente")
                return False
            
            # Nombre del archivo de bloque
            block_filename = f"block_{block_id:06d}.bin"
            block_path = self.blocks_dir / block_filename
            
            # Guardar bloque
            self.block_manager.write_block(str(block_path), block_data)
            
            # Actualizar estadísticas
            self.bloques_almacenados += 1
            self.bytes_usados += len(block_data)
            
            self.logger.info(f"✅ Bloque {block_id} almacenado ({len(block_data)} bytes)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error almacenando bloque {block_id}: {e}")
            return False
    
    def retrieve_block(self, block_id: int) -> Optional[bytes]:
        """
        Recupera un bloque local.
        
        Args:
            block_id: ID del bloque
            
        Returns:
            Datos del bloque o None si no existe
        """
        try:
            block_filename = f"block_{block_id:06d}.bin"
            block_path = self.blocks_dir / block_filename
            
            if not block_path.exists():
                self.logger.warning(f"⚠️ Bloque {block_id} no encontrado")
                return None
            
            block_data = self.block_manager.read_block(str(block_path))
            self.logger.info(f"✅ Bloque {block_id} recuperado ({len(block_data)} bytes)")
            return block_data
            
        except Exception as e:
            self.logger.error(f"❌ Error recuperando bloque {block_id}: {e}")
            return None
    
    def delete_block(self, block_id: int) -> bool:
        """
        Elimina un bloque local.
        
        Args:
            block_id: ID del bloque
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            block_filename = f"block_{block_id:06d}.bin"
            block_path = self.blocks_dir / block_filename
            
            if not block_path.exists():
                self.logger.warning(f"⚠️ Bloque {block_id} no existe")
                return False
            
            # Obtener tamaño antes de eliminar
            block_size = block_path.stat().st_size
            
            # Eliminar
            if self.block_manager.delete_block(str(block_path)):
                self.bloques_almacenados -= 1
                self.bytes_usados -= block_size
                self.logger.info(f"✅ Bloque {block_id} eliminado")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error eliminando bloque {block_id}: {e}")
            return False
    
    def _calculate_space_usage(self) -> None:
        """Calcula el espacio usado actualmente."""
        self.bloques_almacenados = 0
        self.bytes_usados = 0
        
        if self.blocks_dir.exists():
            for block_file in self.blocks_dir.glob("block_*.bin"):
                self.bloques_almacenados += 1
                self.bytes_usados += block_file.stat().st_size
    
    def _has_space_for_block(self, block_size: int) -> bool:
        """
        Verifica si hay espacio para un bloque.
        
        Args:
            block_size: Tamaño del bloque en bytes
            
        Returns:
            True si hay espacio
        """
        capacity_bytes = self.capacidad_mb * 1024 * 1024
        return (self.bytes_usados + block_size) <= capacity_bytes
    
    # ========================================================================
    # Handlers de red
    # ========================================================================
    
    def _handle_ping(self, message: NetworkMessage) -> NetworkMessage:
        """Handler para mensajes PING."""
        return NetworkMessage(NetworkMessage.PONG, {}, self.node_id)
    
    def _handle_get_status(self, message: NetworkMessage) -> NetworkMessage:
        """Handler para solicitud de estado."""
        capacity_bytes = self.capacidad_mb * 1024 * 1024
        usage_percentage = (self.bytes_usados / capacity_bytes * 100) if capacity_bytes > 0 else 0
        
        status = {
            'status': 'online',
            'node_id': self.node_id,
            'role': 'coordinator' if self.es_coordinador else 'worker',
            'blocks_stored': self.bloques_almacenados,
            'bytes_used': self.bytes_usados,
            'bytes_available': capacity_bytes - self.bytes_usados,
            'capacity_mb': self.capacidad_mb,
            'usage_percentage': usage_percentage
        }
        
        return NetworkMessage(
            NetworkMessage.STATUS_RESPONSE,
            status,
            self.node_id
        )
    
    def _handle_upload_block(self, message: NetworkMessage) -> NetworkMessage:
        """
        Handler para subir un bloque.
        Almacena el bloque recibido localmente.
        """
        block_id = message.data.get('block_id')
        file_name = message.data.get('file_name')
        block_data_hex = message.data.get('data')
        block_hash = message.data.get('hash')
        
        self.logger.info(f"📥 Solicitud de subida: bloque {block_id} de {file_name}")
        
        try:
            # Convertir datos de hex a bytes
            block_data = bytes.fromhex(block_data_hex)
            
            # Verificar hash
            calculated_hash = self.block_manager._calculate_hash(block_data)
            if calculated_hash != block_hash:
                self.logger.error(f"❌ Hash no coincide para bloque {block_id}")
                return NetworkMessage(
                    NetworkMessage.ERROR,
                    {'error': 'Hash verification failed'},
                    self.node_id
                )
            
            # Almacenar bloque
            if self.store_block(block_id, block_data, file_name):
                response_data = {
                    'success': True,
                    'block_id': block_id,
                    'message': f'Bloque {block_id} almacenado correctamente'
                }
                return NetworkMessage(
                    NetworkMessage.STATUS_RESPONSE,
                    response_data,
                    self.node_id
                )
            else:
                return NetworkMessage(
                    NetworkMessage.ERROR,
                    {'error': 'Failed to store block'},
                    self.node_id
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error procesando bloque {block_id}: {e}")
            return NetworkMessage(
                NetworkMessage.ERROR,
                {'error': str(e)},
                self.node_id
            )
    
    def _handle_download_block(self, message: NetworkMessage) -> NetworkMessage:
        """
        Handler para descargar un bloque.
        Envía los datos del bloque solicitado.
        """
        block_id = message.data.get('block_id')
        
        self.logger.info(f"📤 Solicitud de descarga: bloque {block_id}")
        
        try:
            # Recuperar bloque
            block_data = self.retrieve_block(block_id)
            
            if block_data:
                response_data = {
                    'success': True,
                    'block_id': block_id,
                    'data': block_data.hex(),  # Convertir a hex para JSON
                    'size': len(block_data)
                }
                return NetworkMessage(
                    NetworkMessage.STATUS_RESPONSE,
                    response_data,
                    self.node_id
                )
            else:
                return NetworkMessage(
                    NetworkMessage.ERROR,
                    {'error': f'Bloque {block_id} no encontrado'},
                    self.node_id
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error recuperando bloque {block_id}: {e}")
            return NetworkMessage(
                NetworkMessage.ERROR,
                {'error': str(e)},
                self.node_id
            )
    
    def _handle_delete_block(self, message: NetworkMessage) -> NetworkMessage:
        """Handler para eliminar un bloque."""
        block_id = message.data.get('block_id')
        
        success = self.delete_block(block_id)
        
        response_data = {
            'success': success,
            'block_id': block_id,
            'message': f'Bloque {block_id} {"eliminado" if success else "no se pudo eliminar"}'
        }
        
        return NetworkMessage(
            NetworkMessage.STATUS_RESPONSE,
            response_data,
            self.node_id
        )
    
    # ========================================================================
    # Utilidades y visualización
    # ========================================================================
    
    def _print_status(self) -> None:
        """Imprime el estado del nodo."""
        capacity_bytes = self.capacidad_mb * 1024 * 1024
        available_bytes = capacity_bytes - self.bytes_usados
        usage_percentage = (self.bytes_usados / capacity_bytes * 100) if capacity_bytes > 0 else 0
        
        print("="*70)
        print(f"  📊 ESTADO DEL NODO {self.node_id}")
        print("="*70)
        print(f"Bloques almacenados: {self.bloques_almacenados}")
        print(f"Espacio usado: {self.bytes_usados / (1024*1024):.2f} MB")
        print(f"Espacio disponible: {available_bytes / (1024*1024):.2f} MB")
        print(f"Capacidad total: {self.capacidad_mb} MB")
        print(f"Uso: {usage_percentage:.1f}%")
        print("="*70 + "\n")
    
    def run_interactive(self) -> None:
        """
        Ejecuta el nodo en modo interactivo.
        Muestra menú y permite operaciones manuales.
        """
        if not self.start():
            return
        
        print("🎮 MODO INTERACTIVO")
        print("Comandos disponibles:")
        print("  status  - Ver estado del nodo")
        print("  blocks  - Listar bloques locales")
        print("  ping    - Hacer ping al coordinador")
        print("  quit    - Salir")
        print()
        
        try:
            while True:
                cmd = input(f"node{self.node_id}> ").strip().lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'status':
                    self._print_status()
                elif cmd == 'blocks':
                    self._list_local_blocks()
                elif cmd == 'ping':
                    self._test_coordinator_connection()
                elif cmd == 'help':
                    print("\nComandos: status, blocks, ping, quit")
                elif cmd == '':
                    continue
                else:
                    print(f"Comando desconocido: '{cmd}'. Escribe 'help' para ver comandos.")
        
        except KeyboardInterrupt:
            print("\n")
        
        finally:
            self.stop()
    
    def _list_local_blocks(self) -> None:
        """Lista todos los bloques almacenados localmente."""
        print("\n📦 Bloques locales:")
        
        blocks = sorted(self.blocks_dir.glob("block_*.bin"))
        
        if not blocks:
            print("  (No hay bloques almacenados)")
        else:
            for block_file in blocks:
                size_kb = block_file.stat().st_size / 1024
                print(f"  {block_file.name} - {size_kb:.2f} KB")
        
        print()
    
    def _test_coordinator_connection(self) -> None:
        """Prueba la conexión con el coordinador."""
        if not self.coordinator_ip or not self.coordinator_port:
            print("❌ No hay coordinador configurado\n")
            return
        
        print(f"\n🔍 Haciendo ping a coordinador ({self.coordinator_ip}:{self.coordinator_port})...")
        
        if self.network.ping_node(self.coordinator_ip, self.coordinator_port):
            print("✅ Coordinador responde\n")
        else:
            print("❌ Coordinador no responde\n")


# ============================================================================
# Código de prueba
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("  Probando Node")
    print("="*70)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Crear nodo 2 (trabajador según config)
        node = Node(node_id=2)
        
        # Ejecutar en modo interactivo
        node.run_interactive()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
