"""
file_operations.py
==================
Módulo de operaciones de archivos de alto nivel para SADTF.

Este módulo proporciona la API principal para que usuarios interactúen
con el sistema de archivos distribuido:
- upload_file(): Subir archivos al sistema
- download_file(): Descargar archivos del sistema
- delete_file(): Eliminar archivos del sistema
- list_files(): Listar archivos almacenados
- get_file_info(): Obtener atributos de un archivo

Este módulo integra:
- Coordinator: para asignación de bloques
- BlockManager: para división/unión de archivos
- MetadataManager: para gestión de metadatos
- NetworkManager: para comunicación con nodos

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.config_manager import get_config
from src.block_manager import BlockManager
from src.metadata_manager import MetadataManager, FileMetadata, BlockEntry
from src.network import NetworkManager, NetworkMessage


class FileOperationResult:
    """
    Resultado de una operación de archivo.
    
    Attributes:
        success: Si la operación fue exitosa
        message: Mensaje descriptivo del resultado
        data: Datos adicionales (opcional)
    """
    
    def __init__(self, success: bool, message: str, data: Optional[Dict] = None):
        self.success = success
        self.message = message
        self.data = data or {}
    
    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} {self.message}"


class FileOperations:
    """
    API de alto nivel para operaciones de archivos en SADTF.
    
    Esta clase se ejecuta en el nodo coordinador y proporciona
    métodos para gestionar el ciclo completo de vida de archivos.
    """
    
    def __init__(self, coordinator_node_id: int):
        """
        Inicializa el gestor de operaciones de archivos.
        
        Args:
            coordinator_node_id: ID del nodo coordinador (puede ser local o remoto)
        """
        self.coordinator_id = coordinator_node_id
        self.config = get_config()
        
        # Obtener configuración del coordinador
        coordinator_config = self.config.get_coordinator_node()
        if not coordinator_config:
            raise ValueError("No hay ningún nodo configurado como coordinador")
        
        self.coordinator_id = coordinator_config['id']
        
        # Configurar logging
        self.logger = logging.getLogger(f"FileOperations-Coord{self.coordinator_id}")
        self.logger.setLevel(logging.INFO)
        
        # Inicializar componentes
        self.block_manager = BlockManager(self.config.get_block_size_bytes())
        
        # Metadata: todos los nodos acceden a los metadatos del coordinador
        metadata_dir = self.config.get_metadata_directory()
        total_blocks = self.config.get_total_blocks()
        self.metadata = MetadataManager(str(metadata_dir), total_blocks)
        
        # Network manager para comunicarse con otros nodos
        self.network = NetworkManager(
            node_id=self.coordinator_id,
            host=coordinator_config['ip'],
            port=coordinator_config['puerto'],
            timeout=self.config.get_timeout_seconds()
        )
        
        self.logger.info("✅ FileOperations inicializado")
    
    # ========================================================================
    # Operación: UPLOAD (Subir archivo)
    # ========================================================================
    
    def upload_file(
        self,
        file_path: str,
        active_nodes: List[int]
    ) -> FileOperationResult:
        """
        Sube un archivo al sistema distribuido.
        
        Proceso:
        1. Divide el archivo en bloques
        2. Calcula hash del archivo completo
        3. Asigna bloques a nodos (primario + réplica)
        4. Envía bloques a nodos
        5. Registra metadatos
        
        Args:
            file_path: Ruta del archivo a subir
            active_nodes: Lista de IDs de nodos activos (sin coordinador)
            
        Returns:
            FileOperationResult con el resultado de la operación
        """
        file_path = Path(file_path)
        file_name = file_path.name
        
        print(f"\n{'='*70}")
        print(f"  📤 SUBIENDO ARCHIVO: {file_name}")
        print(f"{'='*70}\n")
        
        # Validaciones previas
        if not file_path.exists():
            return FileOperationResult(
                False,
                f"Archivo no encontrado: {file_path}"
            )
        
        if self.metadata.file_exists(file_name):
            return FileOperationResult(
                False,
                f"El archivo '{file_name}' ya existe en el sistema"
            )
        
        if len(active_nodes) < 2:
            return FileOperationResult(
                False,
                f"Se necesitan al menos 2 nodos activos. Disponibles: {len(active_nodes)}"
            )
        
        try:
            # Paso 1: Dividir archivo en bloques (en memoria)
            print("📦 Dividiendo archivo en bloques...")
            blocks_data = self.block_manager.split_file_to_memory(str(file_path))
            num_blocks = len(blocks_data)
            file_size = file_path.stat().st_size
            
            print(f"   ✓ {num_blocks} bloques creados ({file_size:,} bytes)")
            
            # Paso 2: Calcular hash del archivo completo
            print("🔐 Calculando hash del archivo...")
            file_hash = self.block_manager.calculate_hash(str(file_path))
            print(f"   ✓ Hash: {file_hash[:16]}...")
            
            # Paso 3: Obtener bloques libres y asignar a nodos
            print("🎯 Asignando bloques a nodos...")
            free_blocks = self.metadata.get_free_blocks(num_blocks)
            
            # Asignar usando round-robin con replicación
            assignments = []
            for i, block_id in enumerate(free_blocks):
                primary_node = active_nodes[i % len(active_nodes)]
                replica_node = active_nodes[(i + 1) % len(active_nodes)]
                
                # Asegurar que sean diferentes
                if primary_node == replica_node and len(active_nodes) > 1:
                    replica_node = active_nodes[(i + 2) % len(active_nodes)]
                
                assignments.append((block_id, primary_node, replica_node))
            
            print(f"   ✓ Bloques asignados a {len(active_nodes)} nodos")
            
            # Paso 4: Enviar bloques a nodos
            print("📡 Enviando bloques a nodos...")
            
            for i, (block_id, primary_node, replica_node) in enumerate(assignments):
                block_data, block_hash = blocks_data[i]
                
                # Obtener configuración de nodos
                primary_config = self.config.get_node_by_id(primary_node)
                replica_config = self.config.get_node_by_id(replica_node)
                
                # Enviar a nodo primario
                success_primary = self._send_block_to_node(
                    block_id,
                    block_data,
                    block_hash,
                    file_name,
                    primary_config['ip'],
                    primary_config['puerto']
                )
                
                # Enviar a nodo réplica
                success_replica = self._send_block_to_node(
                    block_id,
                    block_data,
                    block_hash,
                    file_name,
                    replica_config['ip'],
                    replica_config['puerto']
                )
                
                if not success_primary or not success_replica:
                    # Rollback: eliminar bloques ya enviados
                    self._rollback_upload(assignments[:i], file_name)
                    return FileOperationResult(
                        False,
                        f"Error al enviar bloque {block_id} a nodos"
                    )
                
                # Actualizar metadatos del bloque
                self.metadata.allocate_block(
                    block_id=block_id,
                    file_name=file_name,
                    block_index=i,
                    primary_node=primary_node,
                    replica_node=replica_node,
                    size_bytes=len(block_data),
                    block_hash=block_hash
                )
                
                progress = ((i + 1) / num_blocks) * 100
                print(f"   [{progress:5.1f}%] Bloque {i+1}/{num_blocks} → "
                      f"Nodo {primary_node} (primario), Nodo {replica_node} (réplica)")
            
            # Paso 5: Registrar archivo en metadatos
            print("💾 Registrando archivo en metadatos...")
            self.metadata.register_file(
                file_name=file_name,
                total_size=file_size,
                block_ids=free_blocks,
                file_hash=file_hash
            )
            
            print(f"\n✅ Archivo '{file_name}' subido exitosamente")
            print(f"   Bloques: {num_blocks}")
            print(f"   Tamaño: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
            print(f"   Hash: {file_hash[:16]}...\n")
            
            return FileOperationResult(
                True,
                f"Archivo '{file_name}' subido correctamente",
                {
                    'file_name': file_name,
                    'size': file_size,
                    'num_blocks': num_blocks,
                    'hash': file_hash
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error al subir archivo: {e}")
            return FileOperationResult(False, f"Error: {str(e)}")
    
    def _send_block_to_node(
        self,
        block_id: int,
        block_data: bytes,
        block_hash: str,
        file_name: str,
        node_ip: str,
        node_port: int
    ) -> bool:
        """
        Envía un bloque a un nodo específico.
        
        Args:
            block_id: ID del bloque
            block_data: Datos del bloque
            block_hash: Hash del bloque
            file_name: Nombre del archivo al que pertenece el bloque
            node_ip: IP del nodo
            node_port: Puerto del nodo
            
        Returns:
            True si se envió correctamente
        """
        try:
            message = NetworkMessage(
                NetworkMessage.UPLOAD_BLOCK,
                {
                    'block_id': block_id,
                    'file_name': file_name,
                    'data': block_data.hex(),  # Convertir a hex para JSON
                    'hash': block_hash,
                    'size': len(block_data)
                },
                self.coordinator_id
            )
            
            response = self.network.send_message_to_node(
                node_ip,
                node_port,
                message
            )
            
            return response and response.type != NetworkMessage.ERROR
            
        except Exception as e:
            self.logger.error(f"Error enviando bloque {block_id} a {node_ip}:{node_port}: {e}")
            return False
    
    def _rollback_upload(
        self,
        assignments: List[tuple],
        file_name: str
    ) -> None:
        """
        Revierte una subida fallida eliminando bloques ya enviados.
        
        Args:
            assignments: Lista de (block_id, primary_node, replica_node)
            file_name: Nombre del archivo
        """
        print("⚠️ Realizando rollback...")
        
        for block_id, primary_node, replica_node in assignments:
            # Intentar eliminar de nodo primario
            primary_config = self.config.get_node_by_id(primary_node)
            self._delete_block_from_node(
                block_id,
                primary_config['ip'],
                primary_config['puerto']
            )
            
            # Intentar eliminar de nodo réplica
            replica_config = self.config.get_node_by_id(replica_node)
            self._delete_block_from_node(
                block_id,
                replica_config['ip'],
                replica_config['puerto']
            )
            
            # Liberar bloque en metadatos
            try:
                self.metadata.free_block(block_id)
            except:
                pass
    
    # ========================================================================
    # Operación: DOWNLOAD (Descargar archivo)
    # ========================================================================
    
    def download_file(
        self,
        file_name: str,
        output_path: str,
        active_nodes: List[int]
    ) -> FileOperationResult:
        """
        Descarga un archivo del sistema distribuido.
        
        Proceso:
        1. Obtiene metadatos del archivo
        2. Recupera bloques desde nodos
        3. Reconstruye el archivo
        4. Verifica integridad con hash
        
        Args:
            file_name: Nombre del archivo a descargar
            output_path: Ruta donde guardar el archivo
            active_nodes: Lista de IDs de nodos activos
            
        Returns:
            FileOperationResult con el resultado de la operación
        """
        print(f"\n{'='*70}")
        print(f"  📥 DESCARGANDO ARCHIVO: {file_name}")
        print(f"{'='*70}\n")
        
        # Validaciones
        if not self.metadata.file_exists(file_name):
            return FileOperationResult(
                False,
                f"Archivo '{file_name}' no existe en el sistema"
            )
        
        output_path = Path(output_path)
        if output_path.exists():
            return FileOperationResult(
                False,
                f"Ya existe un archivo en: {output_path}"
            )
        
        try:
            # Paso 1: Obtener metadatos del archivo
            print("📋 Obteniendo metadatos del archivo...")
            file_metadata = self.metadata.get_file_metadata(file_name)
            
            print(f"   ✓ Archivo: {file_name}")
            print(f"   ✓ Tamaño: {file_metadata.tamaño_total:,} bytes")
            print(f"   ✓ Bloques: {file_metadata.num_bloques}")
            
            # Paso 2: Recuperar bloques desde nodos
            print("📡 Recuperando bloques desde nodos...")
            
            blocks_data = []
            
            for i, block_id in enumerate(file_metadata.bloques):
                # Obtener información del bloque
                block_entry = self.metadata.get_block_entry(block_id)
                
                # Intentar desde nodo primario
                block_data = self._retrieve_block_from_node(
                    block_id,
                    block_entry.nodo_primario,
                    active_nodes
                )
                
                # Si falla, intentar desde réplica
                if not block_data and block_entry.nodo_replica:
                    block_data = self._retrieve_block_from_node(
                        block_id,
                        block_entry.nodo_replica,
                        active_nodes
                    )
                
                if not block_data:
                    return FileOperationResult(
                        False,
                        f"No se pudo recuperar bloque {block_id}"
                    )
                
                # Verificar hash del bloque
                block_hash = self.block_manager._calculate_hash(block_data)
                if block_hash != block_entry.hash:
                    return FileOperationResult(
                        False,
                        f"Hash incorrecto en bloque {block_id} (corrupto)"
                    )
                
                blocks_data.append(block_data)
                
                progress = ((i + 1) / file_metadata.num_bloques) * 100
                print(f"   [{progress:5.1f}%] Bloque {i+1}/{file_metadata.num_bloques} "
                      f"recuperado desde Nodo {block_entry.nodo_primario}")
            
            # Paso 3: Reconstruir archivo
            print("🔨 Reconstruyendo archivo...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for block_data in blocks_data:
                    f.write(block_data)
            
            print(f"   ✓ Archivo escrito en: {output_path}")
            
            # Paso 4: Verificar integridad
            print("🔐 Verificando integridad...")
            downloaded_hash = self.block_manager.calculate_hash(str(output_path))
            
            if downloaded_hash != file_metadata.hash_completo:
                output_path.unlink()  # Eliminar archivo corrupto
                return FileOperationResult(
                    False,
                    "Hash del archivo no coincide (archivo corrupto)"
                )
            
            print(f"   ✓ Hash verificado: {downloaded_hash[:16]}...")
            
            print(f"\n✅ Archivo '{file_name}' descargado exitosamente")
            print(f"   Ubicación: {output_path}")
            print(f"   Tamaño: {file_metadata.tamaño_total:,} bytes\n")
            
            return FileOperationResult(
                True,
                f"Archivo '{file_name}' descargado correctamente",
                {
                    'file_name': file_name,
                    'output_path': str(output_path),
                    'size': file_metadata.tamaño_total,
                    'hash': downloaded_hash
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error al descargar archivo: {e}")
            return FileOperationResult(False, f"Error: {str(e)}")
    
    def _retrieve_block_from_node(
        self,
        block_id: int,
        node_id: int,
        active_nodes: List[int]
    ) -> Optional[bytes]:
        """
        Recupera un bloque desde un nodo específico.
        
        Args:
            block_id: ID del bloque
            node_id: ID del nodo
            active_nodes: Lista de nodos activos
            
        Returns:
            Datos del bloque o None si falla
        """
        # Verificar que el nodo esté activo
        if node_id not in active_nodes:
            return None
        
        try:
            node_config = self.config.get_node_by_id(node_id)
            
            message = NetworkMessage(
                NetworkMessage.DOWNLOAD_BLOCK,
                {'block_id': block_id},
                self.coordinator_id
            )
            
            response = self.network.send_message_to_node(
                node_config['ip'],
                node_config['puerto'],
                message
            )
            
            if response and response.type != NetworkMessage.ERROR:
                # Convertir hex de vuelta a bytes
                return bytes.fromhex(response.data.get('data', ''))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error recuperando bloque {block_id} de nodo {node_id}: {e}")
            return None
    
    # ========================================================================
    # Operación: DELETE (Eliminar archivo)
    # ========================================================================
    
    def delete_file(
        self,
        file_name: str,
        active_nodes: List[int]
    ) -> FileOperationResult:
        """
        Elimina un archivo del sistema distribuido.
        
        Proceso:
        1. Obtiene metadatos del archivo
        2. Elimina bloques de nodos
        3. Elimina metadatos del archivo
        
        Args:
            file_name: Nombre del archivo a eliminar
            active_nodes: Lista de IDs de nodos activos
            
        Returns:
            FileOperationResult con el resultado de la operación
        """
        print(f"\n{'='*70}")
        print(f"  🗑️  ELIMINANDO ARCHIVO: {file_name}")
        print(f"{'='*70}\n")
        
        # Validaciones
        if not self.metadata.file_exists(file_name):
            return FileOperationResult(
                False,
                f"Archivo '{file_name}' no existe en el sistema"
            )
        
        try:
            # Paso 1: Obtener metadatos
            print("📋 Obteniendo metadatos del archivo...")
            file_metadata = self.metadata.get_file_metadata(file_name)
            
            print(f"   ✓ Bloques a eliminar: {file_metadata.num_bloques}")
            
            # Paso 2: Eliminar bloques de nodos
            print("🗑️  Eliminando bloques de nodos...")
            
            deleted_count = 0
            
            for i, block_id in enumerate(file_metadata.bloques):
                block_entry = self.metadata.get_block_entry(block_id)
                
                # Eliminar de nodo primario
                if block_entry.nodo_primario:
                    primary_config = self.config.get_node_by_id(block_entry.nodo_primario)
                    if self._delete_block_from_node(
                        block_id,
                        primary_config['ip'],
                        primary_config['puerto']
                    ):
                        deleted_count += 1
                
                # Eliminar de nodo réplica
                if block_entry.nodo_replica:
                    replica_config = self.config.get_node_by_id(block_entry.nodo_replica)
                    if self._delete_block_from_node(
                        block_id,
                        replica_config['ip'],
                        replica_config['puerto']
                    ):
                        deleted_count += 1
                
                # Liberar bloque en metadatos
                self.metadata.free_block(block_id)
                
                progress = ((i + 1) / file_metadata.num_bloques) * 100
                print(f"   [{progress:5.1f}%] Bloque {i+1}/{file_metadata.num_bloques} eliminado")
            
            # Paso 3: Eliminar archivo de metadatos
            print("💾 Eliminando registro del archivo...")
            self.metadata.delete_file(file_name)
            
            print(f"\n✅ Archivo '{file_name}' eliminado exitosamente")
            print(f"   Bloques eliminados: {deleted_count}")
            print(f"   Espacio liberado: {file_metadata.tamaño_total:,} bytes\n")
            
            return FileOperationResult(
                True,
                f"Archivo '{file_name}' eliminado correctamente",
                {
                    'file_name': file_name,
                    'blocks_deleted': deleted_count,
                    'space_freed': file_metadata.tamaño_total
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error al eliminar archivo: {e}")
            return FileOperationResult(False, f"Error: {str(e)}")
    
    def _delete_block_from_node(
        self,
        block_id: int,
        node_ip: str,
        node_port: int
    ) -> bool:
        """
        Elimina un bloque de un nodo específico.
        
        Args:
            block_id: ID del bloque
            node_ip: IP del nodo
            node_port: Puerto del nodo
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            message = NetworkMessage(
                NetworkMessage.DELETE_BLOCK,
                {'block_id': block_id},
                self.coordinator_id
            )
            
            response = self.network.send_message_to_node(
                node_ip,
                node_port,
                message
            )
            
            return response and response.type != NetworkMessage.ERROR
            
        except Exception as e:
            self.logger.error(f"Error eliminando bloque {block_id} de {node_ip}:{node_port}: {e}")
            return False
    
    # ========================================================================
    # Operación: LIST (Listar archivos)
    # ========================================================================
    
    def list_files(self) -> FileOperationResult:
        """
        Lista todos los archivos en el sistema.
        
        Returns:
            FileOperationResult con lista de archivos
        """
        try:
            files = self.metadata.list_all_files()
            
            if not files:
                return FileOperationResult(
                    True,
                    "No hay archivos en el sistema",
                    {'files': []}
                )
            
            files_info = []
            for file_name in files:
                metadata = self.metadata.get_file_metadata(file_name)
                files_info.append({
                    'nombre': metadata.nombre,
                    'tamaño': metadata.tamaño_total,
                    'tamaño_mb': metadata.tamaño_total / (1024 * 1024),
                    'num_bloques': metadata.num_bloques,
                    'fecha_subida': metadata.fecha_subida,
                    'hash': metadata.hash_completo
                })
            
            return FileOperationResult(
                True,
                f"{len(files)} archivo(s) encontrado(s)",
                {'files': files_info}
            )
            
        except Exception as e:
            self.logger.error(f"Error al listar archivos: {e}")
            return FileOperationResult(False, f"Error: {str(e)}")
    
    # ========================================================================
    # Operación: GET FILE INFO (Obtener atributos de archivo)
    # ========================================================================
    
    def get_file_info(self, file_name: str) -> FileOperationResult:
        """
        Obtiene información detallada de un archivo.
        
        Args:
            file_name: Nombre del archivo
            
        Returns:
            FileOperationResult con información del archivo
        """
        if not self.metadata.file_exists(file_name):
            return FileOperationResult(
                False,
                f"Archivo '{file_name}' no existe"
            )
        
        try:
            metadata = self.metadata.get_file_metadata(file_name)
            
            # Obtener información de bloques
            blocks_info = []
            for block_id in metadata.bloques:
                entry = self.metadata.get_block_entry(block_id)
                blocks_info.append({
                    'block_id': block_id,
                    'nodo_primario': entry.nodo_primario,
                    'nodo_replica': entry.nodo_replica,
                    'tamaño': entry.tamaño_bytes,
                    'hash': entry.hash
                })
            
            info = {
                'nombre': metadata.nombre,
                'tamaño_bytes': metadata.tamaño_total,
                'tamaño_mb': metadata.tamaño_total / (1024 * 1024),
                'num_bloques': metadata.num_bloques,
                'fecha_subida': metadata.fecha_subida,
                'hash_completo': metadata.hash_completo,
                'bloques': blocks_info
            }
            
            return FileOperationResult(
                True,
                f"Información de '{file_name}'",
                info
            )
            
        except Exception as e:
            self.logger.error(f"Error al obtener info de archivo: {e}")
            return FileOperationResult(False, f"Error: {str(e)}")
    
    # ========================================================================
    # Utilidades
    # ========================================================================
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema.
        
        Returns:
            Diccionario con estadísticas
        """
        return self.metadata.get_statistics()
