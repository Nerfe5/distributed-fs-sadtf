# SADTF - Sistema de Archivos Distribuido Tolerante a Fallas

## 📋 Descripción

SADTF es un sistema de archivos distribuido que permite almacenar y gestionar archivos grandes aprovechando la capacidad de disco de múltiples computadoras conectadas en red. El sistema divide los archivos en bloques de 1 MB y los distribuye entre los nodos, manteniendo réplicas para tolerancia a fallos.

### Características Principales

✅ **Distribución de archivos**: Divide archivos grandes en bloques de 1 MB  
✅ **Tolerancia a fallas**: Cada bloque tiene una réplica en otro nodo  
✅ **Interfaz gráfica**: GUI intuitiva con tkinter  
✅ **Multiplataforma**: Compatible con Linux y Windows  
✅ **Sin dependencias externas**: Solo usa bibliotecas estándar de Python  
✅ **Tabla de bloques**: Sistema de paginación para gestionar bloques  
✅ **Sincronización**: Vista consistente en todos los nodos  

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────┐
│         INTERFAZ GRÁFICA (SADTF)            │
│  [Cargar] [Atributos] [Tabla] [Descargar]  │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│      COORDINADOR (Nodo Maestro)             │
│  - Tabla de bloques global                  │
│  - Gestión de metadatos                     │
│  - Sincronización entre nodos               │
└─────────────────────────────────────────────┘
                    ↕
┌──────────┬──────────┬──────────┬───────────┐
│  Nodo 1  │  Nodo 2  │  Nodo 3  │  Nodo 4   │
│ (Ubuntu) │  (WSL)   │ (Linux)  │ (Windows) │
│  70 MB   │  70 MB   │ 100 MB   │  80 MB    │
└──────────┴──────────┴──────────┴───────────┘
```

## 📁 Estructura del Proyecto

```
distributed-fs/
├── src/                    # Código fuente
│   ├── config_manager.py   # Gestión de configuración
│   ├── block_manager.py    # División/unión de bloques
│   ├── coordinator.py      # Servidor maestro
│   ├── node.py             # Lógica de nodo
│   ├── network.py          # Comunicación de red
│   ├── gui.py              # Interfaz gráfica
│   └── file_operations.py  # Operaciones de archivos
├── config/                 # Configuración
│   └── config.json         # Parámetros del sistema
├── espacioCompartido/      # Bloques de archivos (no versionado)
├── metadata/               # Tabla de bloques (no versionado)
├── logs/                   # Archivos de log (no versionado)
├── tests/                  # Pruebas unitarias
├── docs/                   # Documentación adicional
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias (vacío - solo stdlib)
├── .gitignore              # Archivos ignorados por Git
└── README.md               # Este archivo
```

## 🚀 Instalación y Configuración

### Requisitos Previos

- **Python 3.8 o superior**
- **Tkinter** (incluido en Python en la mayoría de distribuciones)
- **Red local** o acceso a máquinas remotas

### Verificar Python y Tkinter

```bash
# Verificar versión de Python
python3 --version

# Verificar que tkinter está instalado
python3 -c "import tkinter; print('Tkinter OK')"

# Si tkinter no está instalado (Ubuntu/Debian):
sudo apt-get update
sudo apt-get install python3-tk
```

### Instalación del Proyecto

#### En cada nodo (servidor Ubuntu y WSL):

```bash
# 1. Clonar el repositorio
cd ~
git clone <URL_DEL_REPOSITORIO> distributed-fs
cd distributed-fs

# 2. Crear carpetas necesarias (si no existen)
mkdir -p espacioCompartido metadata logs

# 3. No requiere instalación de dependencias (usa stdlib)
```

### Configuración de Nodos

Edita `config/config.json` para configurar tus nodos:

```json
{
  "nodos": [
    {
      "id": 1,
      "nombre": "servidor-ubuntu",
      "ip": "192.168.1.100",  ← Cambia a la IP real de tu servidor
      "puerto": 5001,
      "capacidad_mb": 70,
      "es_coordinador": true   ← Un nodo debe ser coordinador
    },
    {
      "id": 2,
      "nombre": "wsl-local",
      "ip": "localhost",       ← O la IP de tu WSL
      "puerto": 5002,
      "capacidad_mb": 70,
      "es_coordinador": false
    }
  ]
}
```

#### ¿Cómo obtener la IP de tu servidor Ubuntu?

```bash
# En el servidor Ubuntu:
ip addr show | grep inet

# O más simple:
hostname -I
```

#### ¿Cómo obtener la IP de WSL?

```bash
# En WSL:
ip addr show eth0 | grep inet
```

### Ajustar Capacidad de Almacenamiento

En `config/config.json`, cambia `tamaño_espacio_compartido_mb`:

```json
"almacenamiento": {
  "tamaño_bloque_mb": 1,
  "tamaño_espacio_compartido_mb": 70  ← Cambiar entre 50-100 MB
}
```

## ▶️ Ejecución

### 1. Iniciar el Coordinador (Servidor Ubuntu)

```bash
cd ~/distributed-fs
python3 main.py --coordinador
```

### 2. Iniciar Nodos (WSL y otras máquinas)

```bash
cd ~/distributed-fs
python3 main.py --nodo --id 2
```

### 3. Interfaz Gráfica

La GUI se abrirá automáticamente en cada nodo con las siguientes opciones:

- **Cargar**: Subir un archivo al sistema distribuido
- **Atributos de archivo**: Ver detalles y distribución de bloques
- **Tabla**: Ver tabla completa de bloques del sistema
- **Descargar**: Bajar un archivo seleccionado

## 🔧 Operaciones del Sistema

### Subir un Archivo

1. Click en botón **"Cargar"**
2. Seleccionar archivo del sistema
3. El sistema:
   - Divide el archivo en bloques de 1 MB
   - Distribuye bloques entre nodos disponibles
   - Crea réplica de cada bloque en otro nodo
   - Actualiza la tabla de bloques
   - Muestra el archivo en la lista

### Descargar un Archivo

1. Seleccionar archivo de la lista
2. Click en botón **"Descargar"**
3. Elegir ubicación de destino
4. El sistema:
   - Recupera bloques del nodo primario
   - Si un nodo falla, usa la réplica
   - Une todos los bloques
   - Verifica integridad (hash SHA256)
   - Guarda archivo completo

### Ver Atributos

1. Seleccionar archivo de la lista
2. Click en **"Atributos de archivo"**
3. Ventana muestra:
   - Nombre, fecha, tamaño
   - Lista de bloques
   - Ubicación de cada bloque (nodo primario y réplica)
   - Hash de verificación

### Ver Tabla de Bloques

1. Click en botón **"Tabla"**
2. Ventana muestra:
   - Todas las entradas de la tabla
   - Estado de cada bloque (libre/ocupado)
   - Archivo al que pertenece
   - Nodos donde está almacenado

## 🧪 Pruebas

### Prueba Básica

```bash
# Ejecutar tests
python3 -m pytest tests/

# O ejecutar manualmente
python3 tests/test_block_manager.py
```

### Prueba de Tolerancia a Fallas

1. Subir un archivo grande (>10 MB)
2. Verificar que se distribuye en varios nodos
3. Detener uno de los nodos (Ctrl+C)
4. Intentar descargar el archivo
5. ✅ Debe descargarse correctamente usando réplicas

## 📊 Casos de Uso

### 1. Laboratorio Educativo
- **Escenario**: Universidad con 20-30 PCs en laboratorio
- **Beneficio**: Aprovechar espacio no usado de todas las PCs
- **Ejemplo**: Estudiantes comparten datasets y proyectos grandes

### 2. Pequeña Empresa sin Servidor
- **Escenario**: Oficina con 5-10 computadoras
- **Beneficio**: Almacenamiento compartido sin inversión adicional
- **Ejemplo**: Archivos de diseño, documentos, backups

### 3. Investigación Científica
- **Escenario**: Laboratorio con workstations
- **Beneficio**: Tolerancia a fallas para datos críticos
- **Ejemplo**: Datasets experimentales, logs de sensores

## 🛠️ Desarrollo

### Componentes del Sistema

#### 1. config_manager.py
- Lee y valida `config.json`
- Proporciona acceso a configuración en todo el sistema
- Gestiona parámetros ajustables

#### 2. block_manager.py
- Divide archivos en bloques de 1 MB
- Une bloques para reconstruir archivos
- Calcula hash SHA256 para verificación de integridad
- Gestiona lectura/escritura de bloques

#### 3. coordinator.py
- Mantiene tabla de bloques global
- Asigna bloques a nodos (balanceo de carga)
- Sincroniza estado entre nodos
- Detecta nodos caídos (heartbeat)

#### 4. node.py
- Servidor que escucha peticiones de otros nodos
- Almacena bloques en `espacioCompartido/`
- Responde a solicitudes de lectura/escritura
- Reporta estado al coordinador

#### 5. network.py
- Comunicación TCP/IP entre nodos
- Protocolo JSON para mensajes
- Manejo de timeouts y reconexiones
- Transferencia de bloques

#### 6. gui.py
- Interfaz gráfica con Tkinter
- 4 botones principales
- Tabla de archivos
- Ventanas emergentes para atributos y tabla

#### 7. file_operations.py
- Operaciones de alto nivel (subir/bajar/eliminar)
- Coordina entre GUI y backend
- Manejo de errores y validaciones

### Flujo de Datos

```
Usuario → GUI → file_operations → Coordinador → Nodos → espacioCompartido/
```

## 📝 TODO / Roadmap

### Versión 1.0 (MVP) - Actual
- [x] Estructura base del proyecto
- [x] Sistema de configuración
- [x] Gestión de bloques
- [ ] Coordinador básico
- [ ] Comunicación de red
- [ ] Interfaz gráfica
- [ ] Pruebas básicas

### Versión 1.5
- [ ] Compatibilidad completa con Windows
- [ ] Mejor manejo de errores
- [ ] Re-replicación automática cuando nodo se recupera
- [ ] Logs detallados

### Versión 2.0
- [ ] Coordinador con failover (elección de nuevo líder)
- [ ] Compresión de bloques
- [ ] Encriptación de datos
- [ ] Autenticación de nodos
- [ ] Dashboard web

## 🤝 Contribuir

Este es un proyecto educativo. Para contribuir:

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📄 Licencia

Proyecto educativo - Sistemas Operativos

## 👤 Autor

**Nerfe5**  
Proyecto: Sistema de Archivos Distribuido Tolerante a Fallas  
Universidad: [Tu Universidad]  
Fecha: Noviembre 2025

## 📞 Soporte

Si tienes problemas:

1. Verifica que Python 3.8+ esté instalado
2. Verifica que tkinter esté disponible
3. Revisa los logs en `logs/sistema.log`
4. Verifica conectividad de red entre nodos
5. Asegúrate que los puertos no estén bloqueados por firewall

## 🔗 Referencias

- [Documentación de Python](https://docs.python.org/3/)
- [Tkinter Tutorial](https://docs.python.org/3/library/tkinter.html)
- [Socket Programming](https://docs.python.org/3/library/socket.html)
- [Sistemas de Archivos Distribuidos](https://es.wikipedia.org/wiki/Sistema_de_archivos_distribuido)
