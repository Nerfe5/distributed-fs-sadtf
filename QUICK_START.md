# 🚀 GUÍA RÁPIDA - Sistema de Archivos Distribuido

## ✅ SISTEMA COMPLETADO Y LISTO

Has construido un sistema de archivos distribuido completamente funcional con:
- **4,342 líneas de código Python**
- **8 módulos principales**
- **Interfaz gráfica con Tkinter**
- **Comunicación de red TCP/IP**
- **Base de datos de metadatos SQLite**
- **Sistema de replicación**

---

## 📋 COMANDOS PARA EJECUTAR

### 1️⃣ Iniciar como COORDINADOR (Servidor principal)

```bash
cd ~/distributed-fs
python3 main.py --coordinador
```

Esto iniciará:
- El coordinador maestro en el puerto 5001
- Sistema de heartbeat para detectar nodos
- Servidor de red para comunicación
- Interfaz gráfica con 4 botones

### 2️⃣ Iniciar como NODO trabajador (En otra máquina)

```bash
cd ~/distributed-fs
python3 main.py --nodo --id 2
```

Esto iniciará:
- Nodo trabajador con ID 2
- Conexión al coordinador
- Almacenamiento de bloques local
- Interfaz gráfica

### 3️⃣ Solo GUI (Modo prueba - sin red)

```bash
cd ~/distributed-fs
python3 main.py --gui
```

---

## 🖥️ INTERFAZ GRÁFICA

Cuando ejecutes el sistema, verás una ventana con:

```
╔═══════════════════════════════════════╗
║              SADTF                    ║
╠═══════════════════════════════════════╣
║                                       ║
║  [Lista de archivos]                  ║
║  - archivo1.pdf    01/11/2025  1250KB║
║  - video.mp4       15/11/2025  25MB   ║
║  - documento.docx  20/11/2025  45KB   ║
║                                       ║
╠═══════════════════════════════════════╣
║  [Cargar] [Atributos] [Tabla] [⬇️]    ║
╚═══════════════════════════════════════╝
```

### Botones:
- **Cargar**: Sube un archivo al sistema distribuido
- **Atributos**: Ver detalles y distribución de bloques de un archivo
- **Tabla**: Ver tabla completa de bloques (paginada)
- **Descargar**: Bajar archivo seleccionado

---

## ⚙️ CONFIGURACIÓN

Edita `config/config.json` para cambiar:

### IPs de los nodos:
```json
"nodos": [
  {
    "id": 1,
    "ip": "192.168.0.151",    ← Cambia a tu IP
    "puerto": 5001,
    "es_coordinador": true
  }
]
```

### Obtener tu IP:
```bash
# En Ubuntu/WSL:
hostname -I

# O más detallado:
ip addr show
```

---

## 📂 ESTRUCTURA DEL PROYECTO

```
distributed-fs/
├── main.py                 ← EJECUTA ESTO
├── config/
│   └── config.json        ← Configuración del sistema
├── src/                   ← Código fuente (8 módulos)
│   ├── config_manager.py  ← Gestión de configuración
│   ├── block_manager.py   ← División/unión bloques
│   ├── metadata_manager.py← Base de datos de metadatos
│   ├── coordinator.py     ← Coordinador maestro
│   ├── node.py           ← Nodo trabajador
│   ├── network.py        ← Comunicación TCP/IP
│   ├── file_operations.py← Operaciones de archivos
│   └── gui.py            ← Interfaz gráfica
├── espacioCompartido/    ← Bloques almacenados
├── metadata/             ← Base de datos SQLite
└── logs/                 ← Archivos de log
```

---

## 🎯 EJEMPLO DE USO COMPLETO

### Escenario: 2 computadoras conectadas en red local

#### En el Servidor Ubuntu (192.168.0.151):
```bash
cd ~/distributed-fs
python3 main.py --coordinador
# Se abre la GUI
```

#### En WSL o segunda computadora (172.19.127.188):
```bash
cd ~/distributed-fs
python3 main.py --nodo --id 2
# Se abre la GUI
```

#### Subir un archivo:
1. En cualquier GUI, click **"Cargar"**
2. Selecciona un archivo (ej: `video.mp4`)
3. El sistema:
   - Divide el archivo en bloques de 1 MB
   - Distribuye entre los 2 nodos
   - Crea réplicas
   - Actualiza metadatos

#### Descargar el archivo:
1. Selecciona el archivo en la lista
2. Click **"Descargar"**
3. Elige dónde guardarlo
4. El sistema reconstruye el archivo desde los bloques

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "No se puede conectar al coordinador"
```bash
# Verifica que el coordinador esté ejecutándose
# Verifica la IP en config.json
# Verifica que no haya firewall bloqueando el puerto 5001
```

### Error: Tkinter no funciona
```bash
# Si estás en WSL y la GUI no se abre:
# Necesitas un servidor X (VcXsrv o WSLg)
# En Windows 11, WSLg viene integrado
```

### Ver logs del sistema:
```bash
tail -f logs/system.log
```

---

## 📊 VERIFICAR QUE TODO FUNCIONA

```bash
cd ~/distributed-fs

# Ver estructura del proyecto
ls -la

# Ver módulos Python
ls -la src/

# Verificar configuración
cat config/config.json

# Probar importaciones
python3 -c "from src.gui import SADTFGUI; print('OK')"

# Ver ayuda
python3 main.py --help
```

---

## 🎉 ¡LISTO PARA USAR!

El sistema está **100% funcional**. Solo ejecuta:

```bash
python3 main.py --gui
```

Y verás la interfaz gráfica inmediatamente.

Para un sistema completo con múltiples nodos, configura las IPs en `config.json` y ejecuta el coordinador en una máquina y nodos en otras.

---

## 📚 MÁS INFORMACIÓN

- **README.md**: Documentación completa del sistema
- **config/config.json**: Todos los parámetros configurables
- **src/**: Código fuente bien documentado

**Autor**: Nerfe5  
**Fecha**: Noviembre 2025  
**Versión**: 1.0.0
