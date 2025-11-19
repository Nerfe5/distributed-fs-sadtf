# 📘 Guía de Inicio - SADTF

## ¡Bienvenido a tu proyecto de Sistema de Archivos Distribuido!

Esta guía te explica de forma sencilla qué hemos construido hasta ahora y cómo funciona cada parte.

---

## 🎯 ¿Qué hemos logrado hasta ahora?

### ✅ Fase 1 Completada: Fundamentos del Sistema

Hemos creado la base sólida del proyecto con dos componentes fundamentales que son el corazón del sistema:

1. **ConfigManager** - El cerebro de la configuración
2. **BlockManager** - El motor de división de archivos

---

## 📁 Estructura del Proyecto

```
distributed-fs/
├── src/                      ← Tu código fuente está aquí
│   ├── config_manager.py     ← Lee config.json y proporciona los parámetros
│   └── block_manager.py      ← Divide y une archivos en bloques
│
├── config/                   ← Configuración del sistema
│   └── config.json           ← Aquí ajustas todo (IPs, tamaños, etc.)
│
├── espacioCompartido/        ← Aquí se guardarán los bloques (vacío por ahora)
├── metadata/                 ← Aquí irá la tabla de bloques (vacío por ahora)
├── logs/                     ← Aquí se guardarán los logs (vacío por ahora)
├── tests/                    ← Pruebas y archivos temporales
├── docs/                     ← Documentación (este archivo)
│
├── .gitignore                ← Git ignora archivos temporales
├── README.md                 ← Documentación principal
└── requirements.txt          ← Dependencias (ninguna externa por ahora)
```

---

## 🧩 Componente 1: ConfigManager

### ¿Qué hace?

Lee el archivo `config/config.json` y te permite acceder fácilmente a cualquier configuración del sistema.

### ¿Por qué es importante?

En lugar de escribir valores como "1 MB" o "localhost" en todo el código, los leemos de UN SOLO lugar. Si quieres cambiar algo, solo editas `config.json`.

### Ejemplo de uso:

```python
from config_manager import get_config

# Obtener configuración
config = get_config()

# Usar valores de configuración
block_size = config.get_block_size_mb()  # → 1 MB
nodes = config.get_nodes()                # → Lista de nodos
coordinator = config.get_coordinator_node()  # → Nodo coordinador
```

### Cómo probarlo:

```bash
cd ~/distributed-fs
python3 src/config_manager.py
```

Esto te mostrará un resumen completo de tu configuración actual.

---

## 🧩 Componente 2: BlockManager

### ¿Qué hace?

Se encarga de TODO lo relacionado con bloques:
- Divide un archivo grande en bloques de 1 MB
- Une bloques para reconstruir el archivo original
- Calcula hashes SHA256 para verificar que no haya corrupción
- Lee y escribe bloques en disco

### ¿Por qué es importante?

Es el CORAZÓN del sistema de archivos distribuido. Sin esto, no podríamos dividir archivos grandes ni distribuirlos entre nodos.

### Ejemplo de uso:

```python
from block_manager import BlockManager

# Crear gestor de bloques
bm = BlockManager()

# Dividir un archivo
blocks = bm.split_file_to_blocks(
    "mi_video.mp4",      # Archivo a dividir
    "bloques/"           # Dónde guardar los bloques
)

# Reconstruir el archivo
success = bm.join_blocks_to_file(
    "bloques/",                    # Dónde están los bloques
    "mi_video_recuperado.mp4",     # Archivo de salida
    len(blocks)                    # Cuántos bloques unir
)

# Verificar que sean idénticos
is_same = bm.verify_file_integrity(
    "mi_video.mp4", 
    "mi_video_recuperado.mp4"
)
```

### Cómo probarlo:

```bash
cd ~/distributed-fs
python3 src/block_manager.py
```

Esto creará un archivo de prueba de ~13 MB, lo dividirá en bloques, lo reconstruirá y verificará que sea idéntico.

---

## 🔧 Configuración Actual (config.json)

### Parámetros Importantes:

#### 📦 Almacenamiento
```json
"tamaño_bloque_mb": 1           ← Cada bloque es de 1 MB
"tamaño_espacio_compartido_mb": 70  ← Cada nodo aporta 70 MB
```

**Puedes cambiar estos valores entre 50-100 MB fácilmente.**

#### 💻 Nodos Configurados

##### Nodo 1: Servidor Ubuntu (Coordinador)
```json
{
  "id": 1,
  "nombre": "servidor-ubuntu",
  "ip": "192.168.1.100",    ← CAMBIA ESTO a la IP real de tu servidor
  "puerto": 5001,
  "capacidad_mb": 70,
  "es_coordinador": true    ← Este nodo será el jefe
}
```

##### Nodo 2: WSL Local
```json
{
  "id": 2,
  "nombre": "wsl-local",
  "ip": "localhost",        ← O la IP de tu WSL
  "puerto": 5002,
  "capacidad_mb": 70,
  "es_coordinador": false
}
```

### Cómo obtener las IPs correctas:

#### En tu servidor Ubuntu:
```bash
hostname -I
# O más detallado:
ip addr show | grep inet
```

#### En WSL:
```bash
ip addr show eth0 | grep inet
```

---

## 🧪 Pruebas que Puedes Hacer Ahora

### 1. Verificar la Configuración

```bash
cd ~/distributed-fs
python3 src/config_manager.py
```

Deberías ver algo como:
```
============================================================
  SADTF v1.0.0
============================================================

📦 ALMACENAMIENTO:
   Tamaño de bloque: 1 MB
   Espacio por nodo: 70 MB
   Capacidad total: 140 MB
   Total de bloques: 140
```

### 2. Probar División de Archivos

```bash
cd ~/distributed-fs
python3 src/block_manager.py
```

Esto crea un archivo de prueba, lo divide, lo reconstruye y verifica su integridad.

### 3. Dividir Tu Propio Archivo

Crea un script simple:

```python
# mi_prueba.py
from src.block_manager import BlockManager

bm = BlockManager()

# Divide tu propio archivo
blocks = bm.split_file_to_blocks(
    "/ruta/a/tu/archivo.pdf",
    "tests/mis_bloques"
)

print(f"Archivo dividido en {len(blocks)} bloques")
```

```bash
python3 mi_prueba.py
```

---

## 📚 Conceptos Clave que Debes Entender

### 1. Bloque (Block)

Un **bloque** es un pedazo de 1 MB de un archivo más grande.

Ejemplo:
```
video.mp4 (12 MB) → Se divide en:
- bloque_000.bin (1 MB)
- bloque_001.bin (1 MB)
- bloque_002.bin (1 MB)
- ...
- bloque_011.bin (1 MB)
```

### 2. Hash SHA256

Es como una "huella digital" de los datos. Si cambias UN SOLO byte del archivo, el hash cambia completamente.

Ejemplo:
```python
Archivo original:   hash = "a3f8b2c9..."
Archivo corrupto:   hash = "f9d1e4c8..."  ← DIFERENTE!
```

Lo usamos para verificar que los bloques no se corrompan durante la transferencia.

### 3. Tabla de Bloques

Es como un "índice" que registra:
- Qué bloques existen
- A qué archivo pertenece cada bloque
- Dónde está cada bloque (en qué nodo)
- Si está libre u ocupado

Ejemplo:
```
Bloque 0 → Ocupado → video.mp4 → Nodo 1 (primario), Nodo 2 (réplica)
Bloque 1 → Ocupado → video.mp4 → Nodo 2 (primario), Nodo 3 (réplica)
Bloque 2 → Libre   → -          → -
```

**Nota:** Esto lo implementaremos en la siguiente fase.

### 4. Replicación

Cada bloque se guarda en DOS nodos diferentes:
- **Nodo primario**: Donde se guarda originalmente
- **Nodo réplica**: Copia de respaldo

Así, si el Nodo 1 falla, podemos recuperar el bloque desde el Nodo 2.

---

## 🚀 ¿Qué Sigue?

### Próximos Pasos (Orden Recomendado):

1. **Actualizar IPs en config.json**
   - Pon la IP real de tu servidor Ubuntu
   - Pon la IP correcta de tu WSL

2. **Crear módulo de red (network.py)**
   - Comunicación TCP/IP entre nodos
   - Protocolo JSON para mensajes
   - Envío/recepción de bloques

3. **Crear coordinador (coordinator.py)**
   - Mantener tabla de bloques
   - Asignar bloques a nodos
   - Detectar nodos caídos

4. **Crear nodo (node.py)**
   - Servidor que escucha peticiones
   - Almacena bloques localmente
   - Responde a solicitudes

5. **Crear interfaz gráfica (gui.py)**
   - Ventana con tkinter
   - 4 botones: Cargar, Atributos, Tabla, Descargar
   - Tabla de archivos

6. **Integrar todo**
   - Crear main.py que una todos los componentes
   - Probar con 2 nodos (tu servidor y WSL)

---

## 💡 Consejos para Ti

### Para Entender el Código:

1. **Lee los comentarios**: Cada función tiene explicación de qué hace
2. **Ejecuta los ejemplos**: Los archivos tienen código de prueba al final
3. **Experimenta**: Cambia valores y ve qué pasa
4. **No tengas miedo**: Si algo falla, Git te permite volver atrás

### Si Te Atoras:

1. **Lee los docstrings**: Cada función explica sus parámetros
2. **Revisa el README.md**: Tiene ejemplos completos
3. **Usa print()**: Imprime variables para ver qué contienen
4. **Consulta esta guía**: Vuelve aquí cuando te pierdas

### Atajos Útiles:

```bash
# Ver estado de Git
git status

# Ver cambios
git diff

# Ver historial
git log --oneline

# Volver a un commit anterior (si algo se rompe)
git checkout COMMIT_ID archivo.py
```

---

## 📖 Glosario de Términos

| Término | Significado |
|---------|-------------|
| **Nodo** | Una computadora participante en el sistema |
| **Bloque** | Pedazo de 1 MB de un archivo |
| **Coordinador** | Nodo maestro que gestiona el sistema |
| **Réplica** | Copia de respaldo de un bloque |
| **Hash** | Huella digital para verificar integridad |
| **Metadata** | Información sobre los archivos y bloques |
| **Tabla de bloques** | Índice de todos los bloques del sistema |
| **SHA256** | Algoritmo de hash (muy seguro) |
| **TCP/IP** | Protocolo de red para comunicación |
| **JSON** | Formato de datos tipo {"clave": "valor"} |

---

## 🎓 Lo Que Has Aprendido Hasta Ahora

✅ Cómo organizar un proyecto Python modular  
✅ Cómo leer configuración desde JSON  
✅ Cómo dividir archivos en bloques  
✅ Cómo reconstruir archivos desde bloques  
✅ Cómo verificar integridad con hashes  
✅ Cómo usar Git para versionar código  
✅ Patrones de diseño (Singleton con `get_config()`)  
✅ Type hints en Python (`def func() -> str`)  
✅ Dataclasses para estructurar datos  

---

## 🌟 ¡Ánimo!

Has completado la parte más fundamental del proyecto. Los bloques son la base de TODO el sistema. Lo que sigue (red, coordinador, GUI) se construye sobre estos cimientos.

Cada vez que trabajes en el proyecto:

1. Lee esta guía para recordar dónde estás
2. Revisa el README.md para instrucciones detalladas
3. Prueba cada módulo individualmente antes de integrar
4. Haz commits frecuentes con mensajes descriptivos

**¡Estás haciendo un gran trabajo! 🚀**

---

## 📞 Comandos de Referencia Rápida

```bash
# Navegar al proyecto
cd ~/distributed-fs

# Ver configuración
python3 src/config_manager.py

# Probar bloques
python3 src/block_manager.py

# Estado de Git
git status
git log --oneline

# Ver estructura
ls -la

# Ver un archivo
cat config/config.json

# Editar configuración
nano config/config.json
```

---

**Última actualización:** Noviembre 2025  
**Autor:** Nerfe5  
**Proyecto:** SADTF - Sistema de Archivos Distribuido Tolerante a Fallas
