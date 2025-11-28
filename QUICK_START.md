# 🚀 GUÍA RÁPIDA - SADTF

## 📌 Tabla de Contenido

1. [Comandos Básicos](#comandos-básicos)
2. [Modos de Ejecución](#modos-de-ejecución)
3. [Ejemplo Paso a Paso](#ejemplo-paso-a-paso)
4. [Solución de Problemas](#solución-de-problemas)
5. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 📝 Comandos Básicos

### 🎯 Coordinador (Nodo Principal)

El coordinador es el "cerebro" del sistema. Solo debe haber **uno**.

#### Con GUI (pantalla/monitor disponible):
```bash
cd ~/distributed-fs
python3 main.py --coordinador --gui
```

#### Sin GUI (servidor headless):
```bash
cd ~/distributed-fs
python3 main.py --coordinador --headless
```

**¿Cuándo usar cada uno?**
- **`--gui`**: Cuando el coordinador está en una PC con monitor y quieres ver/usar la interfaz
- **`--headless`**: Cuando el coordinador está en un servidor sin monitor (ej: servidor Ubuntu, Raspberry Pi)

---

### 💻 Nodo Trabajador

Los nodos trabajadores almacenan bloques de archivos.

#### Con GUI (siempre recomendado para nodos):
```bash
cd ~/distributed-fs
python3 main.py --nodo --id 2 --gui
```

**Importante:** Cambia `--id 2` por el ID correcto de cada nodo según tu `config.json`

**Ejemplo con 3 nodos:**
```bash
# Nodo 2:
python3 main.py --nodo --id 2 --gui

# Nodo 3:
python3 main.py --nodo --id 3 --gui

# Nodo 4:
python3 main.py --nodo --id 4 --gui
```

---

## 🔄 Modos de Ejecución

### 📊 Comparación de Modos

| Modo | Comando | ¿Cuándo usar? | GUI | Almacena bloques |
|------|---------|---------------|-----|------------------|
| **Coordinador con GUI** | `--coordinador --gui` | PC/laptop con monitor | ✅ Sí | ✅ Sí |
| **Coordinador headless** | `--coordinador --headless` | Servidor sin monitor | ❌ No | ✅ Sí |
| **Nodo con GUI** | `--nodo --id N --gui` | Cualquier PC/laptop | ✅ Sí | ✅ Sí |
| **Nodo headless** | `--nodo --id N --headless` | Servidor dedicado | ❌ No | ✅ Sí |

---

### 🎯 Escenarios Comunes

#### Escenario 1: Todas las PCs tienen monitor
```bash
# PC 1 (coordinador):
python3 main.py --coordinador --gui

# PC 2, 3, 4... (nodos):
python3 main.py --nodo --id 2 --gui
python3 main.py --nodo --id 3 --gui
```

#### Escenario 2: Servidor Ubuntu sin monitor + PCs con monitor
```bash
# Servidor Ubuntu (coordinador sin GUI):
python3 main.py --coordinador --headless

# Laptop/PC (nodos con GUI):
python3 main.py --nodo --id 2 --gui
python3 main.py --nodo --id 3 --gui
```

#### Escenario 3: Raspberry Pi + computadoras
```bash
# Raspberry Pi (coordinador, siempre encendido):
python3 main.py --coordinador --headless

# Otras PCs cuando estén encendidas:
python3 main.py --nodo --id 2 --gui
```

---

## 📄 Ejemplo Paso a Paso

### Configuración de 2 computadoras

Vamos a configurar un sistema con:
- **Computadora 1** (192.168.1.100): Coordinador
- **Computadora 2** (192.168.1.101): Nodo trabajador

---

#### 👉 Paso 1: Clonar en ambas computadoras

```bash
# En ambas computadoras:
cd ~
git clone https://github.com/Nerfe5/distributed-fs-sadtf.git distributed-fs
cd distributed-fs
```

---

#### 👉 Paso 2: Obtener IPs

```bash
# En cada computadora, ejecuta:
hostname -I
```

Anota las IPs:
- Computadora 1: `192.168.1.100`
- Computadora 2: `192.168.1.101`

---

#### 👉 Paso 3: Editar config.json

En **ambas computadoras**, edita `config/config.json`:

```bash
nano config/config.json
```

Pega esto (con tus IPs reales):

```json
{
  "nodos": [
    {
      "id": 1,
      "nombre": "coordinador",
      "ip": "192.168.1.100",
      "puerto": 6001,
      "capacidad_mb": 70,
      "es_coordinador": true
    },
    {
      "id": 2,
      "nombre": "nodo-trabajador",
      "ip": "192.168.1.101",
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

Guarda con `Ctrl+O`, luego `Ctrl+X`

---

#### 👉 Paso 4: Iniciar coordinador

**En Computadora 1:**

```bash
cd ~/distributed-fs
python3 main.py --coordinador --gui
```

Deberías ver:
```
🚀 Iniciando SADTF como COORDINADOR...
✅ Coordinador iniciado en 192.168.1.100:6001
📊 Capacidad: 70 MB
🖥️  Abriendo interfaz gráfica...
```

Y se abre una ventana.

---

#### 👉 Paso 5: Iniciar nodo trabajador

**En Computadora 2:**

```bash
cd ~/distributed-fs
python3 main.py --nodo --id 2 --gui
```

Deberías ver:
```
🚀 Iniciando SADTF como NODO trabajador (ID: 2)...
✅ Nodo iniciado en 192.168.1.101:6002
🔗 Conectado al coordinador 192.168.1.100:6001
🖥️  Abriendo interfaz gráfica...
```

Y se abre una ventana.

---

#### 👉 Paso 6: Subir un archivo

1. En **cualquiera de las dos ventanas**, haz clic en **"Cargar"**
2. Selecciona un archivo (ej: `documento.pdf`)
3. Espera unos segundos
4. ✅ El archivo aparecerá en la lista de **ambas ventanas**

---

#### 👉 Paso 7: Ver dónde están los bloques

1. Selecciona el archivo en la lista
2. Haz clic en **"Atributos"**
3. Verás algo como:
   ```
   Archivo: documento.pdf
   Tamaño: 2.5 MB
   Bloques: 3
   
   Bloque 1 → Nodo 2 (primario), Nodo 1 (réplica)
   Bloque 2 → Nodo 1 (primario), Nodo 2 (réplica)
   Bloque 3 → Nodo 2 (primario), Nodo 1 (réplica)
   ```

---

#### 👉 Paso 8: Descargar el archivo

1. Selecciona el archivo
2. Haz clic en **"Descargar"**
3. Elige dónde guardarlo
4. ✅ El archivo se reconstruye correctamente

---

### 🎉 ¡Listo!

Tienes un sistema de archivos distribuido funcionando con:
- **140 MB** de almacenamiento total (70 + 70)
- **Tolerancia a fallas**: Si apagas una PC, los archivos siguen disponibles
- **Interfaz simple**: Solo 4 botones

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
# Si el servidor tiene GUI:
python3 main.py --coordinador

# Si es servidor sin GUI (headless):
python3 main.py --coordinador --headless
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

## ⚠️ Solución de Problemas

### Problema 1: "No se puede conectar al coordinador"

**Síntoma:**
```
❌ Error: No se pudo conectar al coordinador en 192.168.1.100:6001
```

**Soluciones:**

1. **Verifica que el coordinador esté corriendo:**
   ```bash
   # En la máquina coordinadora, busca el proceso:
   ps aux | grep "main.py --coordinador"
   ```

2. **Verifica la IP en config.json:**
   ```bash
   # Verifica que la IP del coordinador sea correcta:
   grep -A 5 '"es_coordinador": true' config/config.json
   ```

3. **Verifica conectividad de red:**
   ```bash
   # Desde el nodo, haz ping al coordinador:
   ping 192.168.1.100
   ```

4. **Revisa firewall:**
   ```bash
   # En Ubuntu, permite el puerto:
   sudo ufw allow 6001/tcp
   sudo ufw allow 6002/tcp
   ```

---

### Problema 2: "Tkinter no funciona" o "No module named 'tkinter'"

**Síntoma:**
```
ModuleNotFoundError: No module named 'tkinter'
```

**Soluciones:**

1. **Instalar tkinter:**
   ```bash
   # Ubuntu/Debian:
   sudo apt-get update
   sudo apt-get install python3-tk
   
   # Fedora/RHEL:
   sudo dnf install python3-tkinter
   ```

2. **Si estás en WSL:**
   - Windows 11: WSLg viene integrado, solo instala `python3-tk`
   - Windows 10: Necesitas VcXsrv o Xming

3. **Alternativamente, usa modo headless:**
   ```bash
   python3 main.py --coordinador --headless
   ```

---

### Problema 3: "Puerto ya en uso"

**Síntoma:**
```
OSError: [Errno 98] Address already in use
```

**Solución:**

1. **Encuentra qué proceso usa el puerto:**
   ```bash
   sudo lsof -i :6001
   ```

2. **Mata el proceso anterior:**
   ```bash
   # Si ves un proceso de Python antiguo:
   kill -9 <PID>
   ```

3. **O cambia el puerto en config.json**

---

### Problema 4: "Los archivos no aparecen en otros nodos"

**Síntoma:**  
Subiste un archivo en el nodo 1, pero no aparece en el nodo 2.

**Soluciones:**

1. **Verifica que todos los nodos estén conectados:**
   - Revisa los logs en ambos nodos
   - Deberías ver mensajes como: `🔗 Nodo 2 conectado`

2. **Refresca la GUI:**
   - Cierra y vuelve a abrir la ventana del nodo
   - O reinicia el nodo

3. **Verifica config.json:**
   - Asegúrate que el `config.json` sea idéntico en todos los nodos

---

### Problema 5: Ver logs del sistema

```bash
# Ver logs en tiempo real:
tail -f logs/system.log

# Ver últimas 50 líneas:
tail -n 50 logs/system.log

# Buscar errores:
grep -i error logs/system.log
```

---

## ❓ Preguntas Frecuentes (FAQ)

### ¿Cuántos nodos puedo tener?

**Respuesta:** Tantos como quieras. No hay límite técnico. Solo agrega más entradas en `config.json`.

**Ejemplo:** Con 10 nodos de 70 MB cada uno = **700 MB** de almacenamiento distribuido.

---

### ¿Qué pasa si se apaga un nodo?

**Respuesta:** Nada malo. El sistema sigue funcionando gracias a las **réplicas**.

- Cada bloque tiene una réplica en otro nodo
- Si el nodo primario está apagado, se usa la réplica
- Tus archivos siguen disponibles

---

### ¿Qué pasa si se apaga el coordinador?

**Respuesta:** El sistema deja de funcionar temporalmente. El coordinador es necesario para:
- Distribuir nuevos archivos
- Coordinar descargas
- Mantener la tabla de bloques

**Solución:** Reinicia el coordinador. Todos los datos están seguros en los nodos.

**Nota:** En versiones futuras habrá failover automático del coordinador.

---

### ¿Puedo usar esto en producción?

**Respuesta:** No es recomendable. SADTF es un proyecto **educativo** para aprender sobre sistemas distribuidos.

Para producción, usa sistemas maduros como:
- **Ceph**
- **GlusterFS**
- **HDFS (Hadoop)**
- **MinIO**

---

### ¿Cómo elimino un archivo?

**Respuesta:** Actualmente no hay botón de eliminar en la GUI. Puedes:

1. Conectarte a la base de datos SQLite
2. Marcar el archivo como eliminado
3. O simplemente dejar que los bloques ocupen espacio

**Nota:** Agregar botón de eliminar está en el roadmap.

---

### ¿Puedo cambiar el tamaño de bloque?

**Respuesta:** Sí, en `config.json`:

```json
"almacenamiento": {
  "tamaño_bloque_mb": 2,  ← Cambiar a 2 MB
  ...
}
```

**Nota:** Debes cambiar esto **antes** de subir archivos. No es compatible con archivos existentes.

---

### ¿Funciona en Windows?

**Respuesta:** ¡Sí! Funciona en Windows nativo y WSL.

**Opción 1: Windows Nativo (Recomendado si no tienes WSL)**

1. Instala Python desde [python.org](https://www.python.org/downloads/)
2. Marca "Add Python to PATH" durante instalación
3. Verifica:
   ```powershell
   python --version
   python -c "import tkinter; print('OK')"
   ```
4. Clona y ejecuta:
   ```powershell
   git clone https://github.com/Nerfe5/distributed-fs-sadtf.git
   cd distributed-fs-sadtf
   python main.py --coordinador --gui
   ```

**Opción 2: WSL (si ya lo tienes instalado)**
```bash
# En PowerShell como administrador:
wsl --install

# Luego dentro de WSL:
sudo apt-get update
sudo apt-get install python3 python3-tk git
```

**💡 Diferencias:**
- Windows nativo: usa `python` (no `python3`)
- WSL: usa `python3`

---

### ¿Cómo verifico que todo funciona?

```bash
cd ~/distributed-fs

# Verificar Python:
python3 --version

# Verificar tkinter:
python3 -c "import tkinter; print('✅ OK')"

# Ver estructura:
ls -la

# Ver configuración:
cat config/config.json

# Ver ayuda:
python3 main.py --help
```

---

## 📚 Recursos Adicionales

- **README.md**: Documentación completa con arquitectura y casos de uso
- **config/config.json**: Configuración del sistema
- **docs/**: Documentación técnica adicional
- **src/**: Código fuente bien comentado

---

## 👤 Autor y Versión

**Autor:** Nerfe5  
**Repositorio:** [github.com/Nerfe5/distributed-fs-sadtf](https://github.com/Nerfe5/distributed-fs-sadtf)  
**Versión:** 1.0.0  
**Fecha:** Noviembre 2025  
**Licencia:** Proyecto Educativo

---

## 🎉 ¡Listo para Usar!

Ahora tienes toda la información necesaria para:
- Instalar el sistema
- Configurar múltiples nodos
- Usar la interfaz gráfica
- Resolver problemas comunes

**¿Siguiente paso?** ¡Clona el repositorio y empieza a usarlo!

---

## 🆕 Novedades (v1.0.1+)

### 📊 Visualización de Particiones

La tabla de bloques ahora muestra la posición exacta:
```
Bloque 0: Nodo 1 [pos:0] (primario) → Nodo 2 [pos:0] (réplica)
Bloque 5: Nodo 2 [pos:5] (primario) → Nodo 1 [pos:5] (réplica)
```

Esto te ayuda a entender cómo se distribuyen los bloques en el `espacioCompartido/` de cada nodo.

### ⚠️ Validación de Capacidad

Ahora el sistema valida ANTES de intentar subir:
- ✅ Si el archivo cabe → Se sube normalmente
- ❌ Si el archivo NO cabe → Mensaje detallado con estadísticas:
  - Tamaño del archivo y bloques necesarios
  - Capacidad total, usada y libre
  - Sugerencias: eliminar archivos o agregar nodos

Esto evita subidas fallidas y te da información clara sobre el estado del sistema.
