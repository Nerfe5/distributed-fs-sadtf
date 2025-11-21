"""
block_manager.py
================
Módulo para gestión de bloques en el sistema SADTF.

Este módulo se encarga de:
- Dividir archivos grandes en bloques de tamaño fijo (1 MB)
- Unir bloques para reconstruir archivos originales
- Calcular hashes para verificar integridad
- Leer y escribir bloques en disco

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import hashlib
import os
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BlockInfo:
    """
    Información sobre un bloque de archivo.
    
    Attributes:
        block_id: ID único del bloque (número secuencial)
        file_name: Nombre del archivo original
        block_index: Índice del bloque dentro del archivo (0, 1, 2, ...)
        size_bytes: Tamaño del bloque en bytes
        hash: Hash SHA256 del contenido del bloque
    """
    block_id: int
    file_name: str
    block_index: int
    size_bytes: int
    hash: str


class BlockManager:
    """
    Gestor de bloques del sistema de archivos distribuido.
    
    Se encarga de todas las operaciones relacionadas con la división
    y reconstrucción de archivos en bloques.
    """
    
    def __init__(self, block_size_bytes: int = 1024 * 1024):
        """
        Inicializa el gestor de bloques.
        
        Args:
            block_size_bytes: Tamaño de cada bloque en bytes (por defecto 1 MB)
        """
        self.block_size_bytes = block_size_bytes
    
    # ========================================================================
    # Métodos para dividir archivos en bloques
    # ========================================================================
    
    def split_file_to_blocks(
        self, 
        file_path: str, 
        output_dir: str
    ) -> List[BlockInfo]:
        """
        Divide un archivo en bloques y los guarda en el directorio especificado.
        
        Args:
            file_path: Ruta del archivo a dividir
            output_dir: Directorio donde guardar los bloques
            
        Returns:
            Lista de BlockInfo con información de cada bloque creado
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            IOError: Si hay problemas al leer/escribir
        
        Example:
            >>> bm = BlockManager()
            >>> blocks = bm.split_file_to_blocks("video.mp4", "bloques/")
            >>> print(f"Archivo dividido en {len(blocks)} bloques")
        """
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        
        # Verificar que el archivo existe
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Crear directorio de salida si no existe
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Obtener información del archivo
        file_name = file_path.name
        file_size = file_path.stat().st_size
        
        # Calcular número de bloques necesarios
        num_blocks = (file_size + self.block_size_bytes - 1) // self.block_size_bytes
        
        print(f"\n📄 Dividiendo archivo: {file_name}")
        print(f"   Tamaño: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        print(f"   Bloques a crear: {num_blocks}")
        
        blocks_info = []
        
        # Leer el archivo y dividirlo en bloques
        with open(file_path, 'rb') as f:
            for block_index in range(num_blocks):
                # Leer un bloque de datos
                block_data = f.read(self.block_size_bytes)
                
                # Calcular hash del bloque
                block_hash = self._calculate_hash(block_data)
                
                # Nombre del archivo de bloque: bloque_000.bin, bloque_001.bin, etc.
                block_filename = f"bloque_{block_index:03d}.bin"
                block_path = output_dir / block_filename
                
                # Guardar el bloque en disco
                with open(block_path, 'wb') as block_file:
                    block_file.write(block_data)
                
                # Crear información del bloque
                block_info = BlockInfo(
                    block_id=block_index,  # Por ahora usamos el índice como ID
                    file_name=file_name,
                    block_index=block_index,
                    size_bytes=len(block_data),
                    hash=block_hash
                )
                
                blocks_info.append(block_info)
                
                # Mostrar progreso
                progress = ((block_index + 1) / num_blocks) * 100
                print(f"   [{progress:5.1f}%] Bloque {block_index + 1}/{num_blocks} "
                      f"({len(block_data):,} bytes) → {block_filename}")
        
        print(f"✅ Archivo dividido exitosamente en {len(blocks_info)} bloques\n")
        return blocks_info
    
    def split_file_to_memory(self, file_path: str) -> List[Tuple[bytes, str]]:
        """
        Divide un archivo en bloques pero los mantiene en memoria (no los guarda).
        Útil para enviar bloques por red directamente.
        
        Args:
            file_path: Ruta del archivo a dividir
            
        Returns:
            Lista de tuplas (datos_bloque, hash_bloque)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        blocks = []
        
        with open(file_path, 'rb') as f:
            while True:
                block_data = f.read(self.block_size_bytes)
                if not block_data:
                    break
                
                block_hash = self._calculate_hash(block_data)
                blocks.append((block_data, block_hash))
        
        return blocks
    
    # ========================================================================
    # Métodos para unir bloques y reconstruir archivos
    # ========================================================================
    
    def join_blocks_to_file(
        self, 
        blocks_dir: str, 
        output_file: str,
        num_blocks: int,
        verify_hashes: Optional[List[str]] = None
    ) -> bool:
        """
        Une bloques para reconstruir el archivo original.
        
        Args:
            blocks_dir: Directorio donde están los bloques
            output_file: Ruta donde guardar el archivo reconstruido
            num_blocks: Número total de bloques a unir
            verify_hashes: Lista opcional de hashes para verificar integridad
            
        Returns:
            True si se unió correctamente, False si hubo errores
            
        Example:
            >>> bm = BlockManager()
            >>> success = bm.join_blocks_to_file("bloques/", "video_recuperado.mp4", 12)
        """
        blocks_dir = Path(blocks_dir)
        output_file = Path(output_file)
        
        print(f"\n🔗 Uniendo {num_blocks} bloques...")
        print(f"   Directorio: {blocks_dir}")
        print(f"   Archivo destino: {output_file}")
        
        # Crear directorio de salida si no existe
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Abrir archivo de salida para escribir
        with open(output_file, 'wb') as out_f:
            for block_index in range(num_blocks):
                # Nombre del bloque
                block_filename = f"bloque_{block_index:03d}.bin"
                block_path = blocks_dir / block_filename
                
                # Verificar que el bloque existe
                if not block_path.exists():
                    print(f"❌ Error: Bloque {block_filename} no encontrado")
                    return False
                
                # Leer el bloque
                with open(block_path, 'rb') as block_f:
                    block_data = block_f.read()
                
                # Verificar hash si se proporcionó
                if verify_hashes and block_index < len(verify_hashes):
                    expected_hash = verify_hashes[block_index]
                    actual_hash = self._calculate_hash(block_data)
                    
                    if expected_hash != actual_hash:
                        print(f"❌ Error: Hash del bloque {block_index} no coincide")
                        print(f"   Esperado: {expected_hash}")
                        print(f"   Actual:   {actual_hash}")
                        return False
                
                # Escribir el bloque en el archivo de salida
                out_f.write(block_data)
                
                # Mostrar progreso
                progress = ((block_index + 1) / num_blocks) * 100
                print(f"   [{progress:5.1f}%] Bloque {block_index + 1}/{num_blocks}")
        
        # Verificar que el archivo se creó
        if output_file.exists():
            final_size = output_file.stat().st_size
            print(f"✅ Archivo reconstruido exitosamente")
            print(f"   Tamaño: {final_size:,} bytes ({final_size / (1024*1024):.2f} MB)\n")
            return True
        else:
            print(f"❌ Error: No se pudo crear el archivo\n")
            return False
    
    # ========================================================================
    # Métodos para operaciones con bloques individuales
    # ========================================================================
    
    def read_block(self, block_path: str) -> bytes:
        """
        Lee un bloque desde disco.
        
        Args:
            block_path: Ruta del archivo de bloque
            
        Returns:
            Contenido del bloque en bytes
        """
        with open(block_path, 'rb') as f:
            return f.read()
    
    def write_block(self, block_path: str, data: bytes) -> None:
        """
        Escribe un bloque en disco.
        
        Args:
            block_path: Ruta donde guardar el bloque
            data: Datos del bloque
        """
        block_path = Path(block_path)
        block_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(block_path, 'wb') as f:
            f.write(data)
    
    def delete_block(self, block_path: str) -> bool:
        """
        Elimina un bloque del disco.
        
        Args:
            block_path: Ruta del bloque a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        block_path = Path(block_path)
        if block_path.exists():
            block_path.unlink()
            return True
        return False
    
    # ========================================================================
    # Métodos para cálculo de hashes e integridad
    # ========================================================================
    
    def _calculate_hash(self, data: bytes, algorithm: str = "sha256") -> str:
        """
        Calcula el hash de un bloque de datos.
        
        Args:
            data: Datos a hashear
            algorithm: Algoritmo de hash (sha256, md5, sha1)
            
        Returns:
            Hash en formato hexadecimal
        """
        if algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(data).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(data).hexdigest()
        else:
            raise ValueError(f"Algoritmo de hash no soportado: {algorithm}")
    
    def calculate_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """
        Calcula el hash de un archivo completo.
        Alias de calculate_file_hash para compatibilidad con file_operations.
        
        Args:
            file_path: Ruta del archivo
            algorithm: Algoritmo de hash
            
        Returns:
            Hash del archivo completo
        """
        return self.calculate_file_hash(file_path, algorithm)
    
    def calculate_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """
        Calcula el hash de un archivo completo.
        Útil para verificar que el archivo reconstruido es idéntico al original.
        
        Args:
            file_path: Ruta del archivo
            algorithm: Algoritmo de hash
            
        Returns:
            Hash del archivo completo
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Leer el archivo en chunks para no saturar la memoria
            while True:
                chunk = f.read(8192)  # 8 KB por chunk
                if not chunk:
                    break
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def verify_file_integrity(
        self, 
        original_file: str, 
        reconstructed_file: str
    ) -> bool:
        """
        Verifica que dos archivos son idénticos comparando sus hashes.
        
        Args:
            original_file: Ruta del archivo original
            reconstructed_file: Ruta del archivo reconstruido
            
        Returns:
            True si son idénticos, False si son diferentes
        """
        hash_original = self.calculate_file_hash(original_file)
        hash_reconstructed = self.calculate_file_hash(reconstructed_file)
        
        print(f"\n🔍 Verificando integridad:")
        print(f"   Hash original:      {hash_original}")
        print(f"   Hash reconstruido:  {hash_reconstructed}")
        
        if hash_original == hash_reconstructed:
            print(f"   ✅ Los archivos son idénticos\n")
            return True
        else:
            print(f"   ❌ Los archivos son diferentes\n")
            return False
    
    # ========================================================================
    # Métodos de utilidad
    # ========================================================================
    
    def get_num_blocks_for_file(self, file_path: str) -> int:
        """
        Calcula cuántos bloques se necesitan para un archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Número de bloques necesarios
        """
        file_size = Path(file_path).stat().st_size
        return (file_size + self.block_size_bytes - 1) // self.block_size_bytes
    
    def format_block_name(self, block_index: int) -> str:
        """
        Genera el nombre estándar para un bloque.
        
        Args:
            block_index: Índice del bloque
            
        Returns:
            Nombre del archivo: "bloque_XXX.bin"
        """
        return f"bloque_{block_index:03d}.bin"


# ============================================================================
# Código de prueba
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("  Probando BlockManager")
    print("="*60)
    
    # Crear un archivo de prueba
    test_dir = Path("tests/temp")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / "archivo_prueba.txt"
    
    # Generar contenido de prueba (3.5 MB)
    print("\n1️⃣ Creando archivo de prueba...")
    with open(test_file, 'w') as f:
        for i in range(100000):
            f.write(f"Esta es la línea {i} del archivo de prueba. " * 3 + "\n")
    
    file_size = test_file.stat().st_size
    print(f"   ✓ Archivo creado: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    # Calcular hash del archivo original
    bm = BlockManager()
    original_hash = bm.calculate_file_hash(str(test_file))
    print(f"   ✓ Hash original: {original_hash}")
    
    # Dividir en bloques
    print("\n2️⃣ Dividiendo en bloques...")
    blocks_dir = test_dir / "bloques"
    blocks_info = bm.split_file_to_blocks(str(test_file), str(blocks_dir))
    print(f"   ✓ Creados {len(blocks_info)} bloques")
    
    # Reconstruir archivo
    print("\n3️⃣ Reconstruyendo archivo...")
    reconstructed_file = test_dir / "archivo_reconstruido.txt"
    success = bm.join_blocks_to_file(
        str(blocks_dir), 
        str(reconstructed_file), 
        len(blocks_info)
    )
    
    # Verificar integridad
    if success:
        print("4️⃣ Verificando integridad...")
        is_identical = bm.verify_file_integrity(
            str(test_file), 
            str(reconstructed_file)
        )
        
        if is_identical:
            print("✅ ¡Todas las pruebas pasaron correctamente!")
        else:
            print("❌ Error: Los archivos no son idénticos")
    else:
        print("❌ Error al reconstruir el archivo")
    
    print("\n" + "="*60)
