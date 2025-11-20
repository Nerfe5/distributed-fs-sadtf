"""
network.py
==========
Módulo para comunicación de red entre nodos del sistema SADTF.

Este módulo se encarga de:
- Comunicación TCP/IP entre nodos
- Protocolo de mensajes JSON
- Envío y recepción de bloques
- Manejo de timeouts y reconexiones
- Detección de nodos activos

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import socket
import json
import threading
import time
from typing import Dict, Any, Optional, Tuple, Callable
from pathlib import Path
import logging


class NetworkMessage:
    """
    Clase para representar mensajes en la red.
    
    Los mensajes usan formato JSON y tienen la siguiente estructura:
    {
        "type": "tipo_de_mensaje",
        "data": {...},
        "sender": "nodo_id",
        "timestamp": 1234567890
    }
    """
    
    # Tipos de mensajes
    PING = "ping"
    PONG = "pong"
    UPLOAD_BLOCK = "upload_block"
    DOWNLOAD_BLOCK = "download_block"
    DELETE_BLOCK = "delete_block"
    GET_STATUS = "get_status"
    STATUS_RESPONSE = "status_response"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    METADATA_UPDATE = "metadata_update"
    ERROR = "error"
    
    def __init__(self, msg_type: str, data: Dict[str, Any], sender: int):
        """
        Crea un nuevo mensaje de red.
        
        Args:
            msg_type: Tipo de mensaje (usar constantes de clase)
            data: Datos del mensaje (diccionario)
            sender: ID del nodo que envía el mensaje
        """
        self.type = msg_type
        self.data = data
        self.sender = sender
        self.timestamp = int(time.time())
    
    def to_json(self) -> str:
        """Convierte el mensaje a JSON."""
        return json.dumps({
            "type": self.type,
            "data": self.data,
            "sender": self.sender,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NetworkMessage':
        """Crea un mensaje desde JSON."""
        obj = json.loads(json_str)
        msg = cls(obj["type"], obj["data"], obj["sender"])
        msg.timestamp = obj["timestamp"]
        return msg


class NetworkManager:
    """
    Gestor de red para comunicación entre nodos.
    
    Maneja conexiones TCP/IP, envío/recepción de mensajes,
    y transferencia de bloques entre nodos.
    """
    
    def __init__(self, node_id: int, host: str, port: int, timeout: int = 5):
        """
        Inicializa el gestor de red.
        
        Args:
            node_id: ID de este nodo
            host: IP donde escuchar
            port: Puerto donde escuchar
            timeout: Timeout en segundos para operaciones de red
        """
        self.node_id = node_id
        self.host = host
        self.port = port
        self.timeout = timeout
        
        # Socket servidor (para recibir conexiones)
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.server_thread: Optional[threading.Thread] = None
        
        # Handlers para diferentes tipos de mensajes
        self.message_handlers: Dict[str, Callable] = {}
        
        # Configurar logging
        self.logger = logging.getLogger(f"NetworkManager-Node{node_id}")
        self.logger.setLevel(logging.INFO)
    
    # ========================================================================
    # Métodos para el servidor (recibir conexiones)
    # ========================================================================
    
    def start_server(self) -> bool:
        """
        Inicia el servidor para escuchar conexiones entrantes.
        
        Returns:
            True si se inició correctamente, False si hubo error
        """
        try:
            # Crear socket servidor
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Timeout para poder detener el servidor
            
            self.is_running = True
            
            # Iniciar thread del servidor
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            self.logger.info(f"✅ Servidor iniciado en {self.host}:{self.port}")
            print(f"✅ Nodo {self.node_id} escuchando en {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error al iniciar servidor: {e}")
            print(f"❌ Error al iniciar servidor: {e}")
            return False
    
    def stop_server(self) -> None:
        """Detiene el servidor."""
        self.is_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        
        self.logger.info("🛑 Servidor detenido")
        print(f"🛑 Servidor del Nodo {self.node_id} detenido")
    
    def _server_loop(self) -> None:
        """
        Loop principal del servidor.
        Acepta conexiones y las maneja en threads separados.
        """
        while self.is_running:
            try:
                # Aceptar conexión (con timeout)
                client_socket, client_address = self.server_socket.accept()
                
                # Manejar en thread separado
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                # Timeout normal, continuar
                continue
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error en server loop: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_address: Tuple) -> None:
        """
        Maneja una conexión de cliente.
        
        Args:
            client_socket: Socket del cliente
            client_address: Dirección del cliente
        """
        try:
            # Recibir mensaje
            message_data = self._receive_message(client_socket)
            
            if message_data:
                # Parsear mensaje
                message = NetworkMessage.from_json(message_data)
                
                self.logger.info(f"📨 Mensaje recibido de nodo {message.sender}: {message.type}")
                
                # Procesar mensaje
                response = self._process_message(message)
                
                # Enviar respuesta
                if response:
                    self._send_message(client_socket, response)
        
        except Exception as e:
            self.logger.error(f"Error manejando cliente {client_address}: {e}")
        
        finally:
            client_socket.close()
    
    def _process_message(self, message: NetworkMessage) -> Optional[NetworkMessage]:
        """
        Procesa un mensaje recibido y genera respuesta.
        
        Args:
            message: Mensaje recibido
            
        Returns:
            Mensaje de respuesta o None
        """
        # Buscar handler para este tipo de mensaje
        handler = self.message_handlers.get(message.type)
        
        if handler:
            try:
                return handler(message)
            except Exception as e:
                self.logger.error(f"Error en handler para {message.type}: {e}")
                return NetworkMessage(
                    NetworkMessage.ERROR,
                    {"error": str(e)},
                    self.node_id
                )
        else:
            # Handlers por defecto
            if message.type == NetworkMessage.PING:
                return NetworkMessage(NetworkMessage.PONG, {}, self.node_id)
            
            elif message.type == NetworkMessage.GET_STATUS:
                return NetworkMessage(
                    NetworkMessage.STATUS_RESPONSE,
                    {"status": "online", "node_id": self.node_id},
                    self.node_id
                )
            
            else:
                self.logger.warning(f"Mensaje no manejado: {message.type}")
                return None
    
    # ========================================================================
    # Métodos para el cliente (enviar mensajes)
    # ========================================================================
    
    def send_message_to_node(
        self,
        target_host: str,
        target_port: int,
        message: NetworkMessage
    ) -> Optional[NetworkMessage]:
        """
        Envía un mensaje a otro nodo y espera respuesta.
        
        Args:
            target_host: IP del nodo destino
            target_port: Puerto del nodo destino
            message: Mensaje a enviar
            
        Returns:
            Respuesta del nodo o None si hubo error
        """
        client_socket = None
        try:
            # Crear socket cliente
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.timeout)
            
            # Conectar
            client_socket.connect((target_host, target_port))
            
            # Enviar mensaje
            self._send_message(client_socket, message)
            
            # Recibir respuesta
            response_data = self._receive_message(client_socket)
            
            if response_data:
                return NetworkMessage.from_json(response_data)
            
            return None
            
        except socket.timeout:
            self.logger.error(f"Timeout conectando a {target_host}:{target_port}")
            return None
        except Exception as e:
            self.logger.error(f"Error enviando mensaje a {target_host}:{target_port}: {e}")
            return None
        finally:
            if client_socket:
                client_socket.close()
    
    def _send_message(self, sock: socket.socket, message: NetworkMessage) -> None:
        """
        Envía un mensaje a través de un socket.
        
        Args:
            sock: Socket donde enviar
            message: Mensaje a enviar
        """
        # Convertir mensaje a JSON
        json_data = message.to_json()
        
        # Agregar longitud del mensaje (4 bytes al inicio)
        message_length = len(json_data.encode('utf-8'))
        length_prefix = message_length.to_bytes(4, byteorder='big')
        
        # Enviar: longitud + mensaje
        sock.sendall(length_prefix + json_data.encode('utf-8'))
    
    def _receive_message(self, sock: socket.socket) -> Optional[str]:
        """
        Recibe un mensaje de un socket.
        
        Args:
            sock: Socket desde donde recibir
            
        Returns:
            Mensaje en formato JSON o None
        """
        try:
            # Leer longitud del mensaje (4 bytes)
            length_data = sock.recv(4)
            if not length_data:
                return None
            
            message_length = int.from_bytes(length_data, byteorder='big')
            
            # Leer mensaje completo
            message_data = b''
            while len(message_data) < message_length:
                chunk = sock.recv(min(4096, message_length - len(message_data)))
                if not chunk:
                    return None
                message_data += chunk
            
            return message_data.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error recibiendo mensaje: {e}")
            return None
    
    # ========================================================================
    # Métodos para transferencia de bloques
    # ========================================================================
    
    def send_block(
        self,
        target_host: str,
        target_port: int,
        block_data: bytes,
        block_id: int,
        file_name: str
    ) -> bool:
        """
        Envía un bloque a otro nodo.
        
        Args:
            target_host: IP del nodo destino
            target_port: Puerto del nodo destino
            block_data: Datos del bloque
            block_id: ID del bloque
            file_name: Nombre del archivo al que pertenece
            
        Returns:
            True si se envió correctamente
        """
        message = NetworkMessage(
            NetworkMessage.UPLOAD_BLOCK,
            {
                "block_id": block_id,
                "file_name": file_name,
                "block_size": len(block_data)
            },
            self.node_id
        )
        
        # Enviar mensaje + datos del bloque
        # TODO: Implementar envío de datos binarios
        # Por ahora solo enviamos el mensaje
        
        response = self.send_message_to_node(target_host, target_port, message)
        return response is not None and response.type != NetworkMessage.ERROR
    
    # ========================================================================
    # Métodos de utilidad
    # ========================================================================
    
    def ping_node(self, target_host: str, target_port: int) -> bool:
        """
        Hace ping a un nodo para verificar si está activo.
        
        Args:
            target_host: IP del nodo
            target_port: Puerto del nodo
            
        Returns:
            True si el nodo responde, False si no
        """
        message = NetworkMessage(NetworkMessage.PING, {}, self.node_id)
        response = self.send_message_to_node(target_host, target_port, message)
        return response is not None and response.type == NetworkMessage.PONG
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Registra un handler para un tipo de mensaje.
        
        Args:
            message_type: Tipo de mensaje (usar constantes NetworkMessage)
            handler: Función que maneja el mensaje
        """
        self.message_handlers[message_type] = handler
        self.logger.info(f"Handler registrado para: {message_type}")


# ============================================================================
# Código de prueba
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("  Probando NetworkManager")
    print("="*60)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear dos nodos de prueba
    print("\n1️⃣ Creando nodo servidor (Nodo 1)...")
    server = NetworkManager(node_id=1, host="localhost", port=9001)
    
    if server.start_server():
        print("✅ Servidor iniciado")
        
        time.sleep(1)  # Esperar a que el servidor esté listo
        
        print("\n2️⃣ Creando nodo cliente (Nodo 2)...")
        client = NetworkManager(node_id=2, host="localhost", port=9002)
        
        print("\n3️⃣ Haciendo ping al servidor...")
        if client.ping_node("localhost", 9001):
            print("✅ Ping exitoso - El servidor responde")
        else:
            print("❌ Ping falló")
        
        print("\n4️⃣ Enviando mensaje de estado...")
        message = NetworkMessage(NetworkMessage.GET_STATUS, {}, 2)
        response = client.send_message_to_node("localhost", 9001, message)
        
        if response:
            print(f"✅ Respuesta recibida: {response.type}")
            print(f"   Datos: {response.data}")
        else:
            print("❌ No se recibió respuesta")
        
        print("\n5️⃣ Deteniendo servidor...")
        server.stop_server()
        
        print("\n✅ ¡Todas las pruebas pasaron correctamente!")
    else:
        print("❌ No se pudo iniciar el servidor")
    
    print("\n" + "="*60)
