"""
gui.py
======
Interfaz gráfica del sistema SADTF con tkinter.

Interfaz simple con:
- Título "SADTF" en barra superior
- Tabla de archivos (nombre, fecha DD/MM/YYYY, tamaño KB)
- 4 botones: Cargar, Atributos de archivo, Tabla, Descargar

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, List
from datetime import datetime
import threading

from src.file_operations import FileOperations, FileOperationResult


class SADTFGUI:
    """
    Interfaz gráfica principal del sistema SADTF.
    
    Permite a los usuarios:
    - Ver archivos almacenados
    - Cargar nuevos archivos
    - Descargar archivos
    - Ver atributos de archivos
    - Ver tabla de bloques
    """
    
    def __init__(self, coordinator_node_id: int, active_nodes_callback, is_coordinator: bool = True):
        """
        Inicializa la interfaz gráfica.
        
        Args:
            coordinator_node_id: ID del nodo coordinador
            active_nodes_callback: Función que devuelve lista de nodos activos
            is_coordinator: Si este nodo es el coordinador
        """
        self.coordinator_node_id = coordinator_node_id
        self.get_active_nodes = active_nodes_callback
        self.is_coordinator = is_coordinator
        
        # Inicializar FileOperations solo si es coordinador
        self.file_ops = None
        if is_coordinator:
            self.file_ops = FileOperations(coordinator_node_id)
        else:
            # En nodos trabajadores, las operaciones se hacen vía red al coordinador
            # Por ahora, la GUI es de solo lectura
            print("⚠️  Nodo trabajador: GUI en modo solo lectura")
        
        # Crear ventana principal
        self.root = tk.Tk()
        self.root.title("SADTF")
        self.root.geometry("900x500")
        self.root.resizable(False, False)
        
        # Configurar estilo
        self._setup_style()
        
        # Crear widgets
        self._create_widgets()
        
        # Cargar archivos iniciales
        self._refresh_file_list()
    
    def _setup_style(self):
        """Configura el estilo visual de la interfaz."""
        # Colores del tema
        self.color_header = "#2C5F7C"  # Azul oscuro
        self.color_bg = "#F5F5F5"      # Gris claro
        self.color_button = "#E0E0E0"  # Gris botones
        
        # Configurar estilo ttk
        style = ttk.Style()
        style.theme_use('clam')
        
        # Estilo para Treeview (tabla)
        style.configure(
            "Files.Treeview",
            background="white",
            foreground="black",
            rowheight=30,
            fieldbackground="white",
            borderwidth=1,
            relief="solid"
        )
        style.configure(
            "Files.Treeview.Heading",
            background=self.color_header,
            foreground="white",
            font=('Arial', 10, 'bold')
        )
        style.map('Files.Treeview', background=[('selected', '#0078D7')])
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        # Frame principal
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ============================================================
        # BARRA DE TÍTULO - "SADTF"
        # ============================================================
        title_frame = tk.Frame(main_frame, bg=self.color_header, height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="SADTF",
            bg=self.color_header,
            fg="white",
            font=("Arial", 20, "bold")
        )
        title_label.pack(expand=True)
        
        # ============================================================
        # TABLA DE ARCHIVOS
        # ============================================================
        table_frame = tk.Frame(main_frame, bg="white", padx=20, pady=20)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear Treeview SIN encabezados visibles
        self.tree = ttk.Treeview(
            table_frame,
            columns=("nombre", "fecha", "tamaño"),
            show="",  # NO mostrar encabezados ni tree column
            style="Files.Treeview",
            selectmode="browse"
        )
        
        # Configurar columnas
        self.tree.column("#0", width=0, stretch=False)  # Ocultar columna tree
        self.tree.column("nombre", width=400, anchor="w")
        self.tree.column("fecha", width=200, anchor="center")
        self.tree.column("tamaño", width=200, anchor="e")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar tabla y scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ============================================================
        # BOTONES
        # ============================================================
        button_frame = tk.Frame(main_frame, bg="white", pady=20)
        button_frame.pack(fill=tk.X)
        
        # Estilo de botones
        button_config = {
            'font': ('Arial', 12),
            'bg': self.color_button,
            'fg': 'black',
            'width': 18,
            'height': 2,
            'relief': 'raised',
            'borderwidth': 2,
            'cursor': 'hand2'
        }
        
        # Crear los 4 botones
        btn_cargar = tk.Button(
            button_frame,
            text="Cargar",
            command=self._btn_cargar_clicked,
            **button_config
        )
        btn_cargar.pack(side=tk.LEFT, padx=10, expand=True)
        
        btn_atributos = tk.Button(
            button_frame,
            text="Atributos de archivo",
            command=self._btn_atributos_clicked,
            **button_config
        )
        btn_atributos.pack(side=tk.LEFT, padx=10, expand=True)
        
        btn_tabla = tk.Button(
            button_frame,
            text="Tabla",
            command=self._btn_tabla_clicked,
            **button_config
        )
        btn_tabla.pack(side=tk.LEFT, padx=10, expand=True)
        
        btn_descargar = tk.Button(
            button_frame,
            text="Descargar",
            command=self._btn_descargar_clicked,
            **button_config
        )
        btn_descargar.pack(side=tk.LEFT, padx=10, expand=True)
    
    # ========================================================================
    # Gestión de la tabla de archivos
    # ========================================================================
    
    def _refresh_file_list(self):
        """Actualiza la lista de archivos en la tabla."""
        # Limpiar tabla actual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Solo disponible en coordinador
        if not self.file_ops:
            return
        
        # Obtener lista de archivos
        result = self.file_ops.list_files()
        
        if not result.success:
            return
        
        files = result.data.get('files', [])
        
        # Agregar archivos a la tabla
        for file_info in files:
            nombre = file_info['nombre']
            
            # Formatear fecha: DD/MM/YYYY
            fecha_iso = file_info['fecha_subida']
            try:
                fecha_obj = datetime.fromisoformat(fecha_iso)
                fecha = fecha_obj.strftime("%d/%m/%Y")
            except:
                fecha = fecha_iso[:10]  # Fallback
            
            # Formatear tamaño en KB
            tamaño_bytes = file_info['tamaño']
            tamaño_kb = int(tamaño_bytes / 1024)
            tamaño = f"{tamaño_kb} KB"
            
            # Insertar en tabla
            self.tree.insert("", "end", values=(nombre, fecha, tamaño))
    
    def _get_selected_file(self) -> Optional[str]:
        """
        Obtiene el nombre del archivo seleccionado.
        
        Returns:
            Nombre del archivo o None si no hay selección
        """
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        return item['values'][0]  # Columna "nombre"
    
    # ========================================================================
    # Handlers de botones
    # ========================================================================
    
    def _btn_cargar_clicked(self):
        """Handler para botón Cargar."""
        # Solo disponible en coordinador
        if not self.file_ops:
            messagebox.showwarning(
                "No disponible",
                "Esta operación solo está disponible en el coordinador.\n"
                "Usa la GUI del coordinador para cargar archivos."
            )
            return
        
        # Abrir diálogo de selección de archivo
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo para cargar",
            filetypes=[("Todos los archivos", "*.*")]
        )
        
        if not file_path:
            return  # Usuario canceló
        
        # Mostrar ventana de progreso
        self._show_progress_window("Cargando archivo...")
        
        # Ejecutar upload en thread separado
        thread = threading.Thread(
            target=self._upload_file_thread,
            args=(file_path,)
        )
        thread.start()
    
    def _upload_file_thread(self, file_path: str):
        """Thread para subir archivo sin bloquear la GUI."""
        active_nodes = self.get_active_nodes()
        
        result = self.file_ops.upload_file(file_path, active_nodes)
        
        # Actualizar GUI en main thread
        self.root.after(0, self._upload_complete, result)
    
    def _upload_complete(self, result: FileOperationResult):
        """Callback cuando termina la subida."""
        self._close_progress_window()
        
        if result.success:
            messagebox.showinfo("Éxito", result.message)
            self._refresh_file_list()
        else:
            messagebox.showerror("Error", result.message)
    
    def _btn_descargar_clicked(self):
        """Handler para botón Descargar."""
        # Solo disponible en coordinador
        if not self.file_ops:
            messagebox.showwarning(
                "No disponible",
                "Esta operación solo está disponible en el coordinador."
            )
            return
        
        file_name = self._get_selected_file()
        
        if not file_name:
            messagebox.showwarning(
                "Advertencia",
                "Por favor seleccione un archivo de la lista"
            )
            return
        
        # Abrir diálogo para guardar archivo
        output_path = filedialog.asksaveasfilename(
            title="Guardar archivo como",
            initialfile=file_name,
            defaultextension="",
            filetypes=[("Todos los archivos", "*.*")]
        )
        
        if not output_path:
            return  # Usuario canceló
        
        # Mostrar ventana de progreso
        self._show_progress_window("Descargando archivo...")
        
        # Ejecutar download en thread separado
        thread = threading.Thread(
            target=self._download_file_thread,
            args=(file_name, output_path)
        )
        thread.start()
    
    def _download_file_thread(self, file_name: str, output_path: str):
        """Thread para descargar archivo sin bloquear la GUI."""
        active_nodes = self.get_active_nodes()
        
        result = self.file_ops.download_file(file_name, output_path, active_nodes)
        
        # Actualizar GUI en main thread
        self.root.after(0, self._download_complete, result)
    
    def _download_complete(self, result: FileOperationResult):
        """Callback cuando termina la descarga."""
        self._close_progress_window()
        
        if result.success:
            messagebox.showinfo("Éxito", result.message)
        else:
            messagebox.showerror("Error", result.message)
    
    def _btn_atributos_clicked(self):
        """Handler para botón Atributos de archivo."""
        # Solo disponible en coordinador
        if not self.file_ops:
            messagebox.showwarning(
                "No disponible",
                "Esta operación solo está disponible en el coordinador."
            )
            return
        
        file_name = self._get_selected_file()
        
        if not file_name:
            messagebox.showwarning(
                "Advertencia",
                "Por favor seleccione un archivo de la lista"
            )
            return
        
        # Obtener información del archivo
        result = self.file_ops.get_file_info(file_name)
        
        if not result.success:
            messagebox.showerror("Error", result.message)
            return
        
        # Mostrar ventana con atributos
        self._show_file_attributes(result.data)
    
    def _btn_tabla_clicked(self):
        """Handler para botón Tabla."""
        # Solo disponible en coordinador
        if not self.file_ops:
            messagebox.showwarning(
                "No disponible",
                "Esta operación solo está disponible en el coordinador."
            )
            return
        
        # Obtener estadísticas y tabla de bloques
        stats = self.file_ops.get_system_statistics()
        
        # Mostrar ventana con tabla de bloques
        self._show_block_table(stats)
    
    # ========================================================================
    # Ventanas secundarias
    # ========================================================================
    
    def _show_file_attributes(self, file_info: dict):
        """
        Muestra ventana con atributos detallados de un archivo.
        
        Args:
            file_info: Diccionario con información del archivo
        """
        window = tk.Toplevel(self.root)
        window.title(f"Atributos - {file_info['nombre']}")
        window.geometry("700x500")
        window.resizable(False, False)
        
        # Frame principal
        main_frame = tk.Frame(window, bg="white", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Información general
        info_text = f"""
ARCHIVO: {file_info['nombre']}

Tamaño: {file_info['tamaño_bytes']:,} bytes ({file_info['tamaño_mb']:.2f} MB)
Bloques: {file_info['num_bloques']}
Fecha de subida: {file_info['fecha_subida']}
Hash SHA256: {file_info['hash_completo'][:32]}...

DISTRIBUCIÓN DE BLOQUES:
{'='*60}
"""
        
        # Crear área de texto con scroll
        text_area = scrolledtext.ScrolledText(
            main_frame,
            font=('Courier', 10),
            wrap=tk.WORD,
            height=20
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert('1.0', info_text)
        
        # Agregar información de cada bloque
        for i, block_info in enumerate(file_info['bloques']):
            block_text = f"""
Bloque {i+1} (ID: {block_info['block_id']}):
  └─ Nodo primario: {block_info['nodo_primario']}
  └─ Nodo réplica:  {block_info['nodo_replica']}
  └─ Tamaño:        {block_info['tamaño']:,} bytes
  └─ Hash:          {block_info['hash'][:32]}...
"""
            text_area.insert(tk.END, block_text)
        
        text_area.config(state='disabled')  # Solo lectura
        
        # Botón cerrar
        btn_close = tk.Button(
            main_frame,
            text="Cerrar",
            command=window.destroy,
            font=('Arial', 11),
            bg=self.color_button,
            width=15,
            height=2
        )
        btn_close.pack(pady=10)
    
    def _show_block_table(self, stats: dict):
        """
        Muestra ventana con tabla completa de bloques del sistema.
        
        Args:
            stats: Estadísticas del sistema
        """
        window = tk.Toplevel(self.root)
        window.title("Tabla de Bloques del Sistema")
        window.geometry("900x600")
        
        # Frame principal
        main_frame = tk.Frame(window, bg="white", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Estadísticas generales
        stats_frame = tk.Frame(main_frame, bg="#F0F0F0", relief="ridge", borderwidth=2)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        stats_text = f"""
    ESTADÍSTICAS DEL SISTEMA
    
    Bloques totales: {stats['total_blocks']}    |    Bloques usados: {stats['used_blocks']}    |    Bloques libres: {stats['free_blocks']}    |    Uso: {stats['usage_percentage']:.1f}%
    Archivos: {stats['total_files']}    |    Espacio usado: {stats['total_size_mb']:.2f} MB
"""
        
        stats_label = tk.Label(
            stats_frame,
            text=stats_text,
            bg="#F0F0F0",
            font=('Courier', 9),
            justify=tk.LEFT,
            padx=10,
            pady=10
        )
        stats_label.pack()
        
        # Tabla de bloques
        table_frame = tk.Frame(main_frame, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear Treeview para bloques
        columns = ("id", "estado", "archivo", "parte", "nodo1", "nodo2")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurar encabezados
        tree.heading("id", text="ID")
        tree.heading("estado", text="Estado")
        tree.heading("archivo", text="Archivo")
        tree.heading("parte", text="Parte")
        tree.heading("nodo1", text="Nodo 1")
        tree.heading("nodo2", text="Nodo 2")
        
        # Configurar columnas
        tree.column("id", width=60, anchor="center")
        tree.column("estado", width=100, anchor="center")
        tree.column("archivo", width=300, anchor="w")
        tree.column("parte", width=80, anchor="center")
        tree.column("nodo1", width=80, anchor="center")
        tree.column("nodo2", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Obtener tabla de bloques desde metadata
        metadata = self.file_ops.metadata
        
        # Insertar datos (mostrando máximo 100 bloques ocupados + algunos libres)
        count = 0
        max_entries = 100
        
        for block_id, entry in sorted(metadata.block_table.items()):
            if count >= max_entries and entry.estado == 'libre':
                continue
            
            archivo = entry.archivo if entry.archivo else "-"
            parte = str(entry.parte) if entry.parte is not None else "-"
            nodo1 = str(entry.nodo_primario) if entry.nodo_primario is not None else "-"
            nodo2 = str(entry.nodo_replica) if entry.nodo_replica is not None else "-"
            
            tree.insert("", "end", values=(
                block_id,
                entry.estado,
                archivo,
                parte,
                nodo1,
                nodo2
            ))
            
            count += 1
        
        # Empaquetar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botón cerrar
        btn_close = tk.Button(
            main_frame,
            text="Cerrar",
            command=window.destroy,
            font=('Arial', 11),
            bg=self.color_button,
            width=15,
            height=2
        )
        btn_close.pack(pady=10)
    
    # ========================================================================
    # Ventana de progreso
    # ========================================================================
    
    def _show_progress_window(self, message: str):
        """Muestra ventana modal de progreso."""
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Procesando...")
        self.progress_window.geometry("300x100")
        self.progress_window.resizable(False, False)
        
        # Centrar ventana
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        label = tk.Label(
            self.progress_window,
            text=message,
            font=('Arial', 12)
        )
        label.pack(expand=True)
        
        # Progress bar indeterminada
        progress = ttk.Progressbar(
            self.progress_window,
            mode='indeterminate',
            length=250
        )
        progress.pack(pady=10)
        progress.start(10)
    
    def _close_progress_window(self):
        """Cierra la ventana de progreso."""
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()
            del self.progress_window
    
    # ========================================================================
    # Ejecución
    # ========================================================================
    
    def run(self):
        """Inicia el loop principal de la GUI."""
        self.root.mainloop()


# ============================================================================
# Función auxiliar para testing
# ============================================================================

def main():
    """Función de prueba de la GUI (requiere coordinador activo)."""
    print("Iniciando GUI de prueba...")
    print("NOTA: Esta es una versión de prueba independiente")
    print("      En producción, la GUI se inicia desde main.py\n")
    
    # Mock de función get_active_nodes
    def mock_get_active_nodes():
        return [2]  # Simular nodo 2 activo
    
    # Crear y ejecutar GUI
    try:
        app = SADTFGUI(
            coordinator_node_id=1,
            active_nodes_callback=mock_get_active_nodes
        )
        app.run()
    except Exception as e:
        print(f"Error al iniciar GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
