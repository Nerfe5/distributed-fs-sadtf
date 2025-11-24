# 🗂️ SADTF - Sistema de Archivos Distribuido Tolerante a Fallas

> **Sistema de archivos distribuido simple y funcional para compartir almacenamiento entre múltiples computadoras**

[![Versión](https://img.shields.io/badge/versión-1.0.0-blue.svg)](https://github.com/Nerfe5/distributed-fs-sadtf)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Licencia](https://img.shields.io/badge/licencia-Educativo-orange.svg)](LICENSE)

## 📋 ¿Qué es SADTF?

SADTF es un sistema que te permite **convertir varias computadoras en un solo sistema de almacenamiento compartido**. Imagina que tienes 3 computadoras con 70 MB de espacio libre cada una: SADTF las une para darte 210 MB de almacenamiento distribuido.

### 🎯 ¿Para qué sirve?

- **Compartir archivos grandes** entre varias computadoras sin servidor central costoso
- **Tolerancia a fallas**: Si una computadora se apaga, tus archivos siguen disponibles
- **Aprovechar espacio no usado** en computadoras de laboratorio, oficina o hogar
- **Aprender** sobre sistemas distribuidos de manera práctica

### ✨ Características

✅ **Fácil de usar**: Interfaz gráfica simple con 4 botones  
✅ **Distribución automática**: Divide archivos en bloques de 1 MB  
✅ **Réplicas automáticas**: Cada bloque se guarda en 2 lugares diferentes  
✅ **Modo GUI o headless**: Con o sin interfaz gráfica  
✅ **Sin dependencias**: Solo Python 3.8+ y tkinter  
✅ **100% Python**: Código limpio y educativo

## 🚀 Inicio Rápido (5 minutos)

### 1️⃣ Clonar el repositorio

```bash
cd ~
git clone https://github.com/Nerfe5/distributed-fs-sadtf.git distributed-fs
cd distributed-fs
```

### 2️⃣ Configurar tus nodos

Edita `config/config.json` y cambia las IPs a las de tus computadoras:

```json
{
  "nodos": [
    {
      "id": 1,
      "nombre": "mi-servidor",
      "ip": "192.168.1.100",     ← Cambia esto
      "puerto": 6001,
      "capacidad_mb": 70,
      "es_coordinador": true      ← Solo un nodo debe ser coordinador
    },
    {
      "id": 2,
      "nombre": "mi-laptop",
      "ip": "192.168.1.101",     ← Cambia esto
      "puerto": 6002,
      "capacidad_mb": 70,
      "es_coordinador": false
    }
  ]
}
```

**¿Cómo saber mi IP?** Ejecuta en cada computadora:
```bash
hostname -I
```

### 3️⃣ Iniciar el sistema

**En el coordinador (primera computadora):**
```bash
python3 main.py --coordinador --gui
```

**En los nodos trabajadores (otras computadoras):**
```bash
python3 main.py --nodo --id 2 --gui
```

### 4️⃣ ¡Usar!

Se abre una ventana con botones:
- **Cargar**: Subir archivos
- **Descargar**: Bajar archivos
- **Atributos**: Ver detalles
- **Tabla**: Ver todos los bloques

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────┐
│         INTERFAZ GRÁFICA (SADTF)            │
│  [Cargar] [Atributos] [Tabla] [Descargar]  │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│      COORDINADOR (Nodo 1)                   │
│  - Tabla de bloques global                  │
│  - Distribución de archivos                 │
│  - También puede almacenar bloques          │
└─────────────────────────────────────────────┘
                    ↕
┌──────────┬──────────┬──────────┬───────────┐
│  Nodo 1  │  Nodo 2  │  Nodo 3  │  Nodo 4   │
│ (Ubuntu) │  (WSL)   │ (Linux)  │ (Windows) │
│  70 MB   │  70 MB   │ 100 MB   │  80 MB    │
└──────────┴──────────┴──────────┴───────────┘

💡 El coordinador también puede almacenar bloques como cualquier otro nodo
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

## 📖 Guía Detallada de Instalación

### Requisitos

- **Python 3.8 o superior** (ya instalado en Ubuntu/WSL modernos)
- **Tkinter** para la interfaz gráfica
- **Varias computadoras en la misma red** (o puedes probar con una sola)

### ✅ Paso 1: Verificar Python

```bash
# Ver versión de Python
python3 --version
# Debe mostrar: Python 3.8.x o superior

# Verificar tkinter
python3 -c "import tkinter; print('✅ Tkinter funciona')"

# Si tkinter NO funciona, instálalo:
sudo apt-get update
sudo apt-get install python3-tk
```

### 📥 Paso 2: Instalar en cada computadora

Repite estos pasos en **todas las computadoras** que quieras usar:

```bash
# 1. Ir a tu carpeta home
cd ~

# 2. Clonar el repositorio
git clone https://github.com/Nerfe5/distributed-fs-sadtf.git distributed-fs

# 3. Entrar al proyecto
cd distributed-fs

# 4. Verificar estructura
ls -la
# Debes ver: main.py, src/, config/, etc.
```

### ⚙️ Paso 3: Configurar IPs y nodos

#### 3.1 Obtener las IPs de tus computadoras

En **cada computadora**, ejecuta:

```bash
hostname -I
```

Anota las IPs. Por ejemplo:
- Computadora 1 (servidor): `192.168.1.100`
- Computadora 2 (laptop): `192.168.1.101`
- Computadora 3 (WSL): `172.19.127.188`

#### 3.2 Editar config.json

En **todas las computadoras**, edita el archivo `config/config.json`:

```bash
nano config/config.json
```

Cambia las IPs a las que anotaste:

```json
{
  "nodos": [
    {
      "id": 1,
      "nombre": "servidor-principal",
      "ip": "192.168.1.100",         ← TU IP REAL AQUÍ
      "puerto": 6001,
      "capacidad_mb": 70,
      "es_coordinador": true          ← SOLO UNO debe ser true
    },
    {
      "id": 2,
      "nombre": "laptop-trabajo",
      "ip": "192.168.1.101",         ← TU IP REAL AQUÍ
      "puerto": 6002,
      "capacidad_mb": 70,
      "es_coordinador": false
    }
  ],
  "almacenamiento": {
    "tamaño_bloque_mb": 1,
    "tamaño_espacio_compartido_mb": 70,
    "factor_replicacion": 1
  },
  "red": {
    "timeout_segundos": 30,
    "heartbeat_intervalo_segundos": 10
  }
}
```

**⚠️ IMPORTANTE:**
- **Todos los nodos deben tener el mismo `config.json`**
- Solo **un nodo** debe tener `"es_coordinador": true`
- Los puertos son `6001`, `6002`, `6003`, etc. (uno por nodo)

#### 3.3 Copiar config.json a todas las computadoras

```bash
# Desde la computadora donde editaste config.json, cópialo a las demás:
scp config/config.json usuario@192.168.1.101:~/distributed-fs/config/
```

O simplemente copia y pega el contenido manualmente.

## ▶️ Ejecutar el Sistema

### 🎯 Opción 1: Con interfaz gráfica (GUI)

Esta es la forma más común de usar el sistema.

#### En el COORDINADOR (computadora principal):

```bash
cd ~/distributed-fs
python3 main.py --coordinador --gui
```

Verás:
```
🚀 Iniciando SADTF como COORDINADOR...
✅ Coordinador iniciado en 192.168.1.100:6001
📊 Capacidad: 70 MB
🖥️  Abriendo interfaz gráfica...
```

#### En los NODOS TRABAJADORES (otras computadoras):

```bash
# En la segunda computadora:
cd ~/distributed-fs
python3 main.py --nodo --id 2 --gui

# En la tercera computadora:
cd ~/distributed-fs
python3 main.py --nodo --id 3 --gui
```

Verás:
```
🚀 Iniciando SADTF como NODO trabajador (ID: 2)...
✅ Nodo iniciado en 192.168.1.101:6002
🔗 Conectado al coordinador 192.168.1.100:6001
🖥️  Abriendo interfaz gráfica...
```

---

### 🖥️ Opción 2: Modo headless (sin interfaz gráfica)

Úsalo cuando el coordinador esté en un servidor sin pantalla o GUI:

```bash
cd ~/distributed-fs
python3 main.py --coordinador --headless
```

Esto inicia el coordinador en modo servidor puro. Los nodos trabajadores siguen usando `--gui` para interactuar con el sistema.

**Ejemplo de configuración típica:**
- **Servidor Ubuntu** (sin monitor): `python3 main.py --coordinador --headless`
- **Laptop Windows/WSL** (con monitor): `python3 main.py --nodo --id 2 --gui`
- **PC de escritorio** (con monitor): `python3 main.py --nodo --id 3 --gui`

---

### 🎨 Interfaz Gráfica

Cuando uses `--gui`, verás una ventana así:

```
╔══════════════════════════════════════════╗
║         SADTF - Nodo 2 (Activo)          ║
╠══════════════════════════════════════════╣
║  Archivos en el sistema:                 ║
║                                          ║
║  📄 documento.pdf      01/11/25  2.5 MB  ║
║  🎬 video.mp4         15/11/25  15.0 MB  ║
║  📊 datos.csv         20/11/25  850 KB   ║
║                                          ║
╠══════════════════════════════════════════╣
║ [Cargar] [Atributos] [Tabla] [Descargar]║
╚══════════════════════════════════════════╝
```

**Botones:**
- 📤 **Cargar**: Subir un archivo al sistema distribuido
- 📋 **Atributos**: Ver detalles y ubicación de bloques de un archivo
- 📊 **Tabla**: Ver todos los bloques del sistema (paginado)
- 📥 **Descargar**: Recuperar un archivo seleccionado

## 🔧 Cómo Usar el Sistema

### 📤 1. Subir un archivo

**Pasos:**
1. En cualquier nodo con GUI, haz clic en **"Cargar"**
2. Selecciona un archivo de tu computadora
3. Espera a que termine la subida
4. ✅ El archivo aparecerá en la lista

**Lo que hace el sistema internamente:**
```
1. Divide el archivo en bloques de 1 MB
   ejemplo.mp4 (5 MB) → 5 bloques

2. Distribuye los bloques entre nodos disponibles
   bloque_1 → Nodo 2
   bloque_2 → Nodo 1 (coordinador)
   bloque_3 → Nodo 2
   bloque_4 → Nodo 1
   bloque_5 → Nodo 2

3. Crea una réplica de cada bloque en otro nodo
   bloque_1 → Nodo 2 (primario) + Nodo 1 (réplica)
   bloque_2 → Nodo 1 (primario) + Nodo 2 (réplica)
   ...

4. Actualiza la tabla de metadatos
```

---

### 📥 2. Descargar un archivo

**Pasos:**
1. Selecciona un archivo de la lista
2. Haz clic en **"Descargar"**
3. Elige dónde guardarlo
4. ✅ El archivo se reconstruye y guarda

**Lo que hace el sistema:**
- Recupera todos los bloques (del nodo primario o réplica si falla)
- Une los bloques en orden
- Verifica integridad con hash SHA256
- Guarda el archivo completo

**Tolerancia a fallas:**
Si un nodo está apagado, el sistema automáticamente usa las réplicas de otros nodos. ¡Tu archivo siempre está disponible!

---

### 📋 3. Ver atributos de un archivo

**Pasos:**
1. Selecciona un archivo
2. Haz clic en **"Atributos"**
3. Verás una ventana con:
   - Nombre del archivo
   - Tamaño total
   - Fecha de subida
   - Hash SHA256
   - **Lista de bloques con su ubicación:**
     ```
     Bloque 1: Nodo 2 (primario) → Nodo 1 (réplica)
     Bloque 2: Nodo 1 (primario) → Nodo 2 (réplica)
     Bloque 3: Nodo 2 (primario) → Nodo 1 (réplica)
     ```

---

### 📊 4. Ver tabla completa de bloques

**Pasos:**
1. Haz clic en **"Tabla"**
2. Verás todos los bloques del sistema con:
   - Nombre del archivo
   - Número de bloque
   - Tamaño
   - Nodo donde está almacenado
   - Estado (activo/eliminado)

La tabla está **paginada** (10 bloques por página) para facilitar la navegación.

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

## ➕ Agregar Más Nodos al Sistema

¿Quieres expandir tu sistema con más computadoras? Es muy fácil:

### Paso 1: Edita config.json en TODAS las computadoras

Agrega el nuevo nodo a la lista:

```json
{
  "nodos": [
    {
      "id": 1,
      "ip": "192.168.1.100",
      "puerto": 6001,
      "capacidad_mb": 70,
      "es_coordinador": true
    },
    {
      "id": 2,
      "ip": "192.168.1.101",
      "puerto": 6002,
      "capacidad_mb": 70,
      "es_coordinador": false
    },
    {
      "id": 3,                      ← NUEVO NODO
      "nombre": "pc-oficina",
      "ip": "192.168.1.102",       ← IP del nuevo nodo
      "puerto": 6003,                ← Puerto único
      "capacidad_mb": 100,
      "es_coordinador": false
    }
  ]
}
```

### Paso 2: Inicia el nuevo nodo

En la nueva computadora:

```bash
cd ~/distributed-fs
python3 main.py --nodo --id 3 --gui
```

### Paso 3: ¡Listo!

El nuevo nodo se conectará automáticamente al coordinador y empezará a:
- Recibir bloques de archivos nuevos
- Servir bloques que tenga almacenados
- Participar en la replicación

**💡 Beneficio:** Ahora tienes **240 MB** de almacenamiento distribuido (70 + 70 + 100)

---

## 📊 Casos de Uso Reales

### 1. 🎓 Laboratorio Universitario

**Escenario:**  
Universidad con 20 PCs en laboratorio, cada una con 50 MB libres

**Implementación:**
- 1 PC como coordinador (puede ser headless)
- 19 PCs como nodos trabajadores
- Total: **1,000 MB (1 GB)** de almacenamiento compartido

**Uso:**
Estudiantes comparten datasets, proyectos de programación, papers y videos educativos

**Comandos:**
```bash
# En PC coordinador:
python3 main.py --coordinador --headless

# En cada PC del laboratorio:
python3 main.py --nodo --id N --gui
```

---

### 2. 🏢 Oficina Pequeña

**Escenario:**  
Oficina con 5 computadoras sin servidor dedicado

**Implementación:**
- Computadora del gerente = coordinador con GUI
- 4 computadoras de empleados = nodos con GUI
- Total: **350 MB** compartidos

**Uso:**
Guardar diseños, presentaciones, documentos compartidos, backups

**Ventaja:**  
No necesitan comprar servidor ni NAS. Usan recursos existentes.

---

### 3. 🔬 Laboratorio de Investigación

**Escenario:**  
Lab con 3 workstations potentes para simulaciones

**Implementación:**
- Workstation 1: coordinador (200 MB)
- Workstation 2-3: nodos (200 MB c/u)
- Total: **600 MB** con tolerancia a fallas

**Uso:**
Almacenar resultados de experimentos, datos de sensores, modelos de ML

**Ventaja:**  
Si una workstation falla o reinicia, los datos siguen disponibles gracias a las réplicas.

---

### 4. 🏠 Red Casera

**Escenario:**  
Casa con laptop, PC de escritorio y Raspberry Pi

**Implementación:**
- Raspberry Pi: coordinador headless (siempre encendido)
- Laptop + PC: nodos con GUI (cuando están encendidos)

**Uso:**  
Compartir fotos, videos familiares, documentos entre dispositivos

**Comandos:**
```bash
# En Raspberry Pi:
python3 main.py --coordinador --headless

# En laptop/PC:
python3 main.py --nodo --id 2 --gui
```

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
