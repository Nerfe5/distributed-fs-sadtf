#!/usr/bin/env python3
"""
main.py
=======
Punto de entrada principal del Sistema de Archivos Distribuido (SADTF).

Uso:
    # Iniciar como coordinador
    python3 main.py --coordinador
    
    # Iniciar como nodo específico
    python3 main.py --nodo --id 2
    
    # Iniciar con GUI solamente (modo prueba)
    python3 main.py --gui

Autor: Nerfe5
Fecha: Noviembre 2025
"""

import sys
import os
import argparse
import logging
import signal
import time

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import get_config
from src.coordinator import Coordinator
from src.node import Node
from src.gui import SADTFGUI


def setup_logging(log_level=logging.INFO):
    """Configura el sistema de logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/system.log')
        ]
    )


def start_coordinador():
    """Inicia el sistema como coordinador."""
    print("\n" + "="*70)
    print("  🎯 INICIANDO COMO COORDINADOR")
    print("="*70 + "\n")
    
    config = get_config()
    
    # Buscar el nodo configurado como coordinador
    coordinador_node = None
    for node in config.get_nodes():
        if node.get('es_coordinador', False):
            coordinador_node = node
            break
    
    if not coordinador_node:
        print("❌ ERROR: No hay ningún nodo configurado como coordinador en config.json")
        return False
    
    node_id = coordinador_node['id']
    
    try:
        # Crear coordinador
        coordinator = Coordinator(node_id)
        
        # Iniciar coordinador
        if not coordinator.start():
            print("❌ Error al iniciar coordinador")
            return False
        
        # Iniciar GUI
        print("\n🖥️  Iniciando interfaz gráfica...\n")
        
        # Callback para obtener nodos activos del coordinador
        def get_active_nodes():
            return [n.node_id for n in coordinator.nodes.values() if n.activo]
        
        gui = SADTFGUI(node_id, get_active_nodes)
        
        # Manejar señales para cierre limpio
        def signal_handler(sig, frame):
            print("\n\n🛑 Señal de interrupción recibida...")
            coordinator.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Ejecutar GUI (blocking)
        gui.run()
        
        # Cuando se cierra la GUI, detener coordinador
        coordinator.stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Error al iniciar coordinador: {e}")
        import traceback
        traceback.print_exc()
        return False


def start_nodo(node_id: int):
    """Inicia el sistema como nodo trabajador."""
    print("\n" + "="*70)
    print(f"  🎯 INICIANDO COMO NODO {node_id}")
    print("="*70 + "\n")
    
    config = get_config()
    
    # Verificar que el nodo existe y no es coordinador
    node_config = config.get_node_by_id(node_id)
    if not node_config:
        print(f"❌ ERROR: No existe el nodo con ID {node_id} en config.json")
        return False
    
    if node_config.get('es_coordinador', False):
        print(f"❌ ERROR: El nodo {node_id} está configurado como coordinador.")
        print("   Usa --coordinador en su lugar.")
        return False
    
    try:
        # Crear nodo
        node = Node(node_id)
        
        # Iniciar nodo
        if not node.start():
            print("❌ Error al iniciar nodo")
            return False
        
        # Iniciar GUI
        print("\n🖥️  Iniciando interfaz gráfica...\n")
        
        # Callback para obtener nodos activos (desde el nodo)
        def get_active_nodes():
            # En nodos trabajadores, solo el coordinador conoce todos los nodos
            # Por ahora retornar lista vacía, la GUI consultará al coordinador
            return []
        
        gui = SADTFGUI(node_id, get_active_nodes)
        
        # Manejar señales para cierre limpio
        def signal_handler(sig, frame):
            print("\n\n🛑 Señal de interrupción recibida...")
            node.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Ejecutar GUI (blocking)
        gui.run()
        
        # Cuando se cierra la GUI, detener nodo
        node.stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Error al iniciar nodo: {e}")
        import traceback
        traceback.print_exc()
        return False


def start_gui_only(node_id: int = 1):
    """Inicia solo la GUI (modo prueba)."""
    print("\n" + "="*70)
    print("  🖥️  INICIANDO GUI (MODO PRUEBA)")
    print("="*70 + "\n")
    
    try:
        # Callback dummy para modo prueba
        def get_active_nodes():
            return [1]  # Solo el nodo actual
        
        gui = SADTFGUI(node_id, get_active_nodes)
        gui.run()
        return True
    except Exception as e:
        print(f"❌ Error al iniciar GUI: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Sistema de Archivos Distribuido Tolerante a Fallas (SADTF)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Iniciar como coordinador
  python3 main.py --coordinador
  
  # Iniciar como nodo trabajador
  python3 main.py --nodo --id 2
  
  # Solo GUI (prueba)
  python3 main.py --gui
        """
    )
    
    parser.add_argument(
        '--coordinador',
        action='store_true',
        help='Iniciar como coordinador maestro'
    )
    
    parser.add_argument(
        '--nodo',
        action='store_true',
        help='Iniciar como nodo trabajador'
    )
    
    parser.add_argument(
        '--id',
        type=int,
        help='ID del nodo (requerido con --nodo)'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Solo iniciar GUI (modo prueba)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Habilitar modo debug (más logging)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    
    # Validar argumentos
    if not (args.coordinador or args.nodo or args.gui):
        parser.print_help()
        print("\n❌ ERROR: Debes especificar --coordinador, --nodo, o --gui")
        return 1
    
    if args.coordinador and args.nodo:
        print("❌ ERROR: No puedes usar --coordinador y --nodo al mismo tiempo")
        return 1
    
    if args.nodo and not args.id:
        print("❌ ERROR: --nodo requiere --id <ID_DEL_NODO>")
        return 1
    
    # Crear directorios necesarios
    os.makedirs('logs', exist_ok=True)
    os.makedirs('metadata', exist_ok=True)
    os.makedirs('espacioCompartido', exist_ok=True)
    
    # Ejecutar según el modo
    success = False
    
    if args.gui:
        success = start_gui_only(args.id if args.id else 1)
    elif args.coordinador:
        success = start_coordinador()
    elif args.nodo:
        success = start_nodo(args.id)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
