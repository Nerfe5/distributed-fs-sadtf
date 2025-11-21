"""
metadata_manager.py
===================
Módulo para gestionar la tabla de bloques y metadatos del sistema SADTF.

Este módulo se encarga de:
- Mantener la tabla de bloques global
- Registrar qué bloques pertenecen a qué archivos
- Controlar bloques libres/ocupados
- Gestionar ubicación de bloques (nodo primario + réplicas)
- Persistir metadatos en disco

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class BlockEntry:
    """
    Entrada en la tabla de bloques.
    
    Attributes:
        block_id: ID único del bloque (0, 1, 2, ...)
        estado: 'libre' u 'ocupado'
        archivo: Nombre del archivo al que pertenece (None si libre)
        parte: Índice del bloque dentro del archivo (0, 1, 2, ...)
        nodo_primario: ID del nodo donde está el bloque primario
        nodo_replica: ID del nodo donde está la réplica
        tamaño_bytes: Tamaño del bloque en bytes
        hash: Hash SHA256 del bloque
        fecha_creacion: Timestamp de cuándo se creó
    """
    block_id: int
    estado: str  # 'libre' u 'ocupado'
    archivo: Optional[str] = None
    parte: Optional[int] = None
    nodo_primario: Optional[int] = None
    nodo_replica: Optional[int] = None
    tamaño_bytes: Optional[int] = None
    hash: Optional[str] = None
    fecha_creacion: Optional[str] = None


@dataclass
class FileMetadata:
    """
    Metadatos de un archivo en el sistema.
    
    Attributes:
        nombre: Nombre del archivo
        tamaño_total: Tamaño total en bytes
        num_bloques: Cantidad de bloques
        bloques: Lista de IDs de bloques que componen el archivo
        hash_completo: Hash del archivo completo
        fecha_subida: Timestamp de cuándo se subió
    """
    nombre: str
    tamaño_total: int
    num_bloques: int
    bloques: List[int]
    hash_completo: str
    fecha_subida: str


class MetadataManager:
    """
    Gestor de metadatos y tabla de bloques del sistema.
    
    Mantiene el estado global de todos los bloques y archivos,
    con persistencia en disco en formato JSON.
    """
    
    def __init__(self, metadata_dir: str, total_blocks: int):
        """
        Inicializa el gestor de metadatos.
        
        Args:
            metadata_dir: Directorio donde guardar metadatos
            total_blocks: Número total de bloques en el sistema
        """
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        self.total_blocks = total_blocks
        
        # Tabla de bloques: dict[block_id -> BlockEntry]
        self.block_table: Dict[int, BlockEntry] = {}
        
        # Índice de archivos: dict[nombre_archivo -> FileMetadata]
        self.file_index: Dict[str, FileMetadata] = {}
        
        # Lock para operaciones concurrentes
        self.lock = threading.Lock()
        
        # Archivos de persistencia
        self.block_table_file = self.metadata_dir / "block_table.json"
        self.file_index_file = self.metadata_dir / "file_index.json"
        
        # Cargar o inicializar
        self._load_or_initialize()
    
    # ========================================================================
    # Inicialización y persistencia
    # ========================================================================
    
    def _load_or_initialize(self) -> None:
        """Carga metadatos desde disco o inicializa tabla vacía."""
        if self.block_table_file.exists() and self.file_index_file.exists():
            self._load_from_disk()
            print(f"✓ Metadatos cargados desde disco")
        else:
            self._initialize_empty_table()
            print(f"✓ Tabla de bloques inicializada: {self.total_blocks} bloques")
    
    def _initialize_empty_table(self) -> None:
        """Inicializa una tabla de bloques vacía."""
        with self.lock:
            self.block_table = {}
            for block_id in range(self.total_blocks):
                self.block_table[block_id] = BlockEntry(
                    block_id=block_id,
                    estado='libre'
                )
            self.file_index = {}
            self._save_to_disk()
    
    def _load_from_disk(self) -> None:
        """Carga metadatos desde archivos JSON."""
        with self.lock:
            # Cargar tabla de bloques
            with open(self.block_table_file, 'r') as f:
                data = json.load(f)
                self.block_table = {
                    int(k): BlockEntry(**v) for k, v in data.items()
                }
            
            # Cargar índice de archivos
            with open(self.file_index_file, 'r') as f:
                data = json.load(f)
                self.file_index = {
                    k: FileMetadata(**v) for k, v in data.items()
                }
    
    def _save_to_disk(self) -> None:
        """Guarda metadatos en archivos JSON."""
        # No necesita lock porque se llama desde funciones con lock
        
        # Guardar tabla de bloques
        data = {
            str(k): asdict(v) for k, v in self.block_table.items()
        }
        with open(self.block_table_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Guardar índice de archivos
        data = {
            k: asdict(v) for k, v in self.file_index.items()
        }
        with open(self.file_index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ========================================================================
    # Operaciones con bloques
    # ========================================================================
    
    def get_free_blocks(self, count: int) -> List[int]:
        """
        Obtiene una lista de bloques libres.
        
        Args:
            count: Cantidad de bloques necesarios
            
        Returns:
            Lista de IDs de bloques libres
            
        Raises:
            ValueError: Si no hay suficientes bloques libres
        """
        with self.lock:
            free_blocks = [
                block_id for block_id, entry in self.block_table.items()
                if entry.estado == 'libre'
            ]
            
            if len(free_blocks) < count:
                raise ValueError(
                    f"No hay suficientes bloques libres. "
                    f"Necesarios: {count}, Disponibles: {len(free_blocks)}"
                )
            
            return free_blocks[:count]
    
    def allocate_block(
        self,
        block_id: int,
        file_name: str = None,
        block_index: int = None,
        primary_node: int = None,
        replica_node: int = None,
        size_bytes: int = None,
        block_hash: str = None,
        # Aliases para compatibilidad
        archivo: str = None,
        parte: int = None,
        nodo_primario: int = None,
        nodo_replica: int = None,
        tamaño_bytes: int = None,
        hash: str = None
    ) -> None:
        """
        Asigna un bloque a un archivo.
        
        Acepta tanto nombres en inglés (file_name, block_index, etc.) como
        en español (archivo, parte, etc.) para compatibilidad.
        
        Args:
            block_id: ID del bloque a asignar
            file_name/archivo: Nombre del archivo
            block_index/parte: Índice de la parte dentro del archivo
            primary_node/nodo_primario: ID del nodo primario
            replica_node/nodo_replica: ID del nodo réplica
            size_bytes/tamaño_bytes: Tamaño del bloque
            block_hash/hash: Hash del bloque
        """
        # Resolver aliases
        file_name = file_name or archivo
        block_index = block_index if block_index is not None else parte
        primary_node = primary_node or nodo_primario
        replica_node = replica_node or nodo_replica
        size_bytes = size_bytes or tamaño_bytes
        block_hash = block_hash or hash
        
        with self.lock:
            if block_id not in self.block_table:
                raise ValueError(f"Bloque {block_id} no existe")
            
            if self.block_table[block_id].estado == 'ocupado':
                raise ValueError(f"Bloque {block_id} ya está ocupado")
            
            self.block_table[block_id] = BlockEntry(
                block_id=block_id,
                estado='ocupado',
                archivo=file_name,
                parte=block_index,
                nodo_primario=primary_node,
                nodo_replica=replica_node,
                tamaño_bytes=size_bytes,
                hash=block_hash,
                fecha_creacion=datetime.now().isoformat()
            )
            
            self._save_to_disk()
    
    def free_block(self, block_id: int) -> None:
        """
        Libera un bloque ocupado.
        
        Args:
            block_id: ID del bloque a liberar
        """
        with self.lock:
            if block_id not in self.block_table:
                raise ValueError(f"Bloque {block_id} no existe")
            
            self.block_table[block_id] = BlockEntry(
                block_id=block_id,
                estado='libre'
            )
            
            self._save_to_disk()
    
    def get_block_info(self, block_id: int) -> BlockEntry:
        """
        Obtiene información de un bloque.
        
        Args:
            block_id: ID del bloque
            
        Returns:
            BlockEntry con la información del bloque
        """
        with self.lock:
            if block_id not in self.block_table:
                raise ValueError(f"Bloque {block_id} no existe")
            return self.block_table[block_id]
    
    # ========================================================================
    # Operaciones con archivos
    # ========================================================================
    
    def register_file(
        self,
        file_name: str = None,
        total_size: int = None,
        block_ids: List[int] = None,
        file_hash: str = None,
        # Aliases en español
        nombre: str = None,
        tamaño_total: int = None,
        num_bloques: int = None,
        bloques: List[int] = None,
        hash_completo: str = None
    ) -> None:
        """
        Registra un nuevo archivo en el sistema.
        
        Acepta tanto parámetros en inglés como en español para compatibilidad.
        
        Args:
            file_name/nombre: Nombre del archivo
            total_size/tamaño_total: Tamaño total en bytes
            block_ids/bloques: Lista de IDs de bloques
            file_hash/hash_completo: Hash del archivo completo
            num_bloques: Número de bloques (se calcula si no se proporciona)
        """
        # Resolver aliases
        file_name = file_name or nombre
        total_size = total_size or tamaño_total
        block_ids = block_ids or bloques
        file_hash = file_hash or hash_completo
        num_bloques = num_bloques or (len(block_ids) if block_ids else 0)
        
        with self.lock:
            if file_name in self.file_index:
                raise ValueError(f"El archivo '{file_name}' ya existe")
            
            self.file_index[file_name] = FileMetadata(
                nombre=file_name,
                tamaño_total=total_size,
                num_bloques=num_bloques,
                bloques=block_ids,
                hash_completo=file_hash,
                fecha_subida=datetime.now().isoformat()
            )
            
            self._save_to_disk()
    
    def delete_file(self, nombre: str) -> List[int]:
        """
        Elimina un archivo del sistema.
        
        Args:
            nombre: Nombre del archivo a eliminar
            
        Returns:
            Lista de IDs de bloques que fueron liberados
        """
        with self.lock:
            if nombre not in self.file_index:
                raise ValueError(f"El archivo '{nombre}' no existe")
            
            # Obtener bloques del archivo
            file_meta = self.file_index[nombre]
            bloques = file_meta.bloques
            
            # Liberar cada bloque
            for block_id in bloques:
                if block_id in self.block_table:
                    self.block_table[block_id] = BlockEntry(
                        block_id=block_id,
                        estado='libre'
                    )
            
            # Eliminar del índice
            del self.file_index[nombre]
            
            self._save_to_disk()
            
            return bloques
    
    def get_file_info(self, nombre: str) -> FileMetadata:
        """
        Obtiene metadatos de un archivo.
        
        Args:
            nombre: Nombre del archivo
            
        Returns:
            FileMetadata con la información del archivo
        """
        with self.lock:
            if nombre not in self.file_index:
                raise ValueError(f"El archivo '{nombre}' no existe")
            return self.file_index[nombre]
    
    def list_files(self) -> List[FileMetadata]:
        """
        Lista todos los archivos en el sistema.
        
        Returns:
            Lista de FileMetadata de todos los archivos
        """
        with self.lock:
            return list(self.file_index.values())
    
    def file_exists(self, nombre: str) -> bool:
        """Verifica si un archivo existe."""
        with self.lock:
            return nombre in self.file_index
    
    def list_all_files(self) -> List[str]:
        """
        Lista los nombres de todos los archivos en el sistema.
        
        Returns:
            Lista de nombres de archivos
        """
        with self.lock:
            return list(self.file_index.keys())
    
    def get_file_metadata(self, nombre: str) -> FileMetadata:
        """
        Obtiene metadatos de un archivo (alias de get_file_info).
        
        Args:
            nombre: Nombre del archivo
            
        Returns:
            FileMetadata con la información del archivo
        """
        return self.get_file_info(nombre)
    
    def get_block_entry(self, block_id: int) -> BlockEntry:
        """
        Obtiene una entrada de bloque (alias de get_block_info).
        
        Args:
            block_id: ID del bloque
            
        Returns:
            BlockEntry con la información del bloque
        """
        return self.get_block_info(block_id)
    
    # ========================================================================
    # Estadísticas y utilidades
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Obtiene estadísticas del sistema.
        
        Returns:
            Diccionario con estadísticas
        """
        with self.lock:
            total_blocks = len(self.block_table)
            used_blocks = sum(
                1 for entry in self.block_table.values()
                if entry.estado == 'ocupado'
            )
            free_blocks = total_blocks - used_blocks
            
            total_files = len(self.file_index)
            total_size = sum(
                file_meta.tamaño_total
                for file_meta in self.file_index.values()
            )
            
            return {
                'total_blocks': total_blocks,
                'used_blocks': used_blocks,
                'free_blocks': free_blocks,
                'usage_percentage': (used_blocks / total_blocks * 100) if total_blocks > 0 else 0,
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024)
            }
    
    def print_block_table(self, max_entries: int = 20) -> None:
        """
        Imprime la tabla de bloques.
        
        Args:
            max_entries: Máximo número de entradas a mostrar
        """
        with self.lock:
            print("\n" + "="*80)
            print("  TABLA DE BLOQUES")
            print("="*80)
            print(f"{'ID':<5} {'Estado':<10} {'Archivo':<25} {'Parte':<6} {'Nodo1':<6} {'Nodo2':<6}")
            print("-"*80)
            
            count = 0
            for block_id, entry in sorted(self.block_table.items()):
                if count >= max_entries and entry.estado == 'libre':
                    continue
                
                archivo = entry.archivo[:22] + "..." if entry.archivo and len(entry.archivo) > 25 else (entry.archivo or "-")
                parte = str(entry.parte) if entry.parte is not None else "-"
                nodo1 = str(entry.nodo_primario) if entry.nodo_primario is not None else "-"
                nodo2 = str(entry.nodo_replica) if entry.nodo_replica is not None else "-"
                
                print(f"{block_id:<5} {entry.estado:<10} {archivo:<25} {parte:<6} {nodo1:<6} {nodo2:<6}")
                
                count += 1
                if count >= max_entries:
                    break
            
            if len(self.block_table) > max_entries:
                print(f"... (mostrando {max_entries} de {len(self.block_table)} bloques)")
            
            print("="*80 + "\n")
    
    def print_file_index(self) -> None:
        """Imprime el índice de archivos."""
        with self.lock:
            print("\n" + "="*80)
            print("  ÍNDICE DE ARCHIVOS")
            print("="*80)
            
            if not self.file_index:
                print("  (No hay archivos en el sistema)")
            else:
                print(f"{'Nombre':<30} {'Tamaño':<15} {'Bloques':<10} {'Fecha':<20}")
                print("-"*80)
                
                for nombre, file_meta in self.file_index.items():
                    tamaño_mb = file_meta.tamaño_total / (1024 * 1024)
                    fecha = file_meta.fecha_subida[:19]  # Solo fecha y hora
                    nombre_corto = nombre[:27] + "..." if len(nombre) > 30 else nombre
                    
                    print(f"{nombre_corto:<30} {tamaño_mb:>10.2f} MB   {file_meta.num_bloques:<10} {fecha:<20}")
            
            print("="*80 + "\n")


# ============================================================================
# Código de prueba
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("  Probando MetadataManager")
    print("="*80)
    
    # Crear gestor con 10 bloques para prueba
    metadata = MetadataManager("tests/temp/metadata", total_blocks=10)
    
    print("\n1️⃣ Tabla inicial:")
    metadata.print_block_table()
    
    print("\n2️⃣ Obteniendo 3 bloques libres...")
    free_blocks = metadata.get_free_blocks(3)
    print(f"   Bloques libres: {free_blocks}")
    
    print("\n3️⃣ Asignando bloques a un archivo...")
    for i, block_id in enumerate(free_blocks):
        metadata.allocate_block(
            block_id=block_id,
            archivo="video.mp4",
            parte=i,
            nodo_primario=1,
            nodo_replica=2,
            tamaño_bytes=1048576,
            hash=f"hash_{block_id}"
        )
    
    print("\n4️⃣ Registrando archivo...")
    metadata.register_file(
        nombre="video.mp4",
        tamaño_total=3145728,
        num_bloques=3,
        bloques=free_blocks,
        hash_completo="hash_completo_video"
    )
    
    print("\n5️⃣ Tabla después de asignar:")
    metadata.print_block_table()
    
    print("\n6️⃣ Índice de archivos:")
    metadata.print_file_index()
    
    print("\n7️⃣ Estadísticas:")
    stats = metadata.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n8️⃣ Eliminando archivo...")
    freed_blocks = metadata.delete_file("video.mp4")
    print(f"   Bloques liberados: {freed_blocks}")
    
    print("\n9️⃣ Tabla después de eliminar:")
    metadata.print_block_table()
    
    print("\n✅ ¡Todas las pruebas pasaron correctamente!")
    print("="*80)
