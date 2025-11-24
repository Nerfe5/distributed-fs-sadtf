# 🚀 Guía de Implementación SADTF

## 📋 Introducción

Esta guía te llevará paso a paso para implementar el Sistema de Archivos Distribuido Tolerante a Fallas (SADTF) en tu red local, laboratorio u oficina.

**Tiempo estimado:** 30-45 minutos  
**Nivel de dificultad:** Básico  
**Conocimientos requeridos:** Comandos básicos de Linux/terminal

---

## 🎯 Objetivo

Al finalizar esta guía, tendrás:
- Un coordinador funcionando
- 2 o más nodos trabajadores conectados
- Capacidad de subir y descargar archivos distribuidos
- Sistema con tolerancia a fallas

---

## 📝 Checklist de Preparación

Antes de comenzar, asegúrate de tener:

- [ ] 2 o más computadoras en la misma red local
- [ ] Python 3.8+ instalado en todas ellas
- [ ] Acceso SSH o físico a cada computadora
- [ ] Las IPs de todas las computadoras anotadas
- [ ] Permisos de administrador (para instalar paquetes)

---

## 🔧 Parte 1: Preparación de Computadoras

### Paso 1.1: Identificar tus computadoras

Decide cuál será el rol de cada computadora:

| Computadora | Rol | Tiene monitor | IP (ejemplo) |
|-------------|-----|---------------|--------------|
| PC 1 | Coordinador | ❌ No (servidor) | 192.168.1.100 |
| PC 2 | Nodo trabajador | ✅ Sí | 192.168.1.101 |
| PC 3 | Nodo trabajador | ✅ Sí | 192.168.1.102 |

**Recomendación:** Usa un servidor o PC siempre encendido como coordinador.

---

### Paso 1.2: Obtener las IPs

En **cada computadora**, ejecuta:

```bash
hostname -I
```

O más específico:

```bash
ip addr show | grep "inet " | grep -v "127.0.0.1"
```

Anota las IPs en una tabla:

```
PC 1 (coordinador):  192.168.1.100
PC 2 (nodo):         192.168.1.101
PC 3 (nodo):         192.168.1.102
```

---

### Paso 1.3: Verificar Python y tkinter

En **cada computadora**:

```bash
# Ver versión de Python
python3 --version
# Debe ser 3.8 o superior

# Verificar tkinter
python3 -c "import tkinter; print('✅ Tkinter OK')"
```

Si tkinter falla, instálalo:

```bash
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install python3-tk

# Fedora/RHEL:
sudo dnf install python3-tkinter
```

---

## 📥 Parte 2: Instalación del Sistema

### Paso 2.1: Clonar el repositorio en todas las computadoras

**IMPORTANTE:** Repite esto en **cada computadora** (coordinador y nodos).

```bash
# 1. Ir a home
cd ~

# 2. Clonar repositorio
git clone https://github.com/Nerfe5/distributed-fs-sadtf.git distributed-fs

# 3. Entrar al directorio
cd distributed-fs

# 4. Verificar que todo esté bien
ls -la
# Deberías ver: main.py, src/, config/, README.md, etc.
```

---

### Paso 2.2: Configurar config.json

**IMPORTANTE:** El archivo `config.json` debe ser **idéntico** en todas las computadoras.

#### Opción A: Editar manualmente en cada PC

En **cada computadora**:

```bash
cd ~/distributed-fs
nano config/config.json
```

Pega este contenido (ajusta las IPs a tus valores reales):

```json
{
  "nodos": [
    {
      "id": 1,
      "nombre": "coordinador-principal",
      "ip": "192.168.1.100",
      "puerto": 6001,
      "capacidad_mb": 70,
      "es_coordinador": true
    },
    {
      "id": 2,
      "nombre": "nodo-trabajador-1",
      "ip": "192.168.1.101",
      "puerto": 6002,
      "capacidad_mb": 70,
      "es_coordinador": false
    },
    {
      "id": 3,
      "nombre": "nodo-trabajador-2",
      "ip": "192.168.1.102",
      "puerto": 6003,
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

Guarda con `Ctrl+O`, luego `Ctrl+X`.

#### Opción B: Copiar desde el coordinador (más rápido)

1. **En el coordinador**, edita `config.json`
2. **Cópialo a los demás nodos:**

```bash
# Desde el coordinador:
scp config/config.json usuario@192.168.1.101:~/distributed-fs/config/
scp config/config.json usuario@192.168.1.102:~/distributed-fs/config/
```

---

### Paso 2.3: Verificar conectividad

Desde **cada nodo trabajador**, verifica que puedas alcanzar al coordinador:

```bash
ping -c 3 192.168.1.100
```

Si falla, revisa:
- Que ambas máquinas estén en la misma red
- Que no haya firewall bloqueando

---

### Paso 2.4: Configurar firewall (si es necesario)

Si usas firewall, permite los puertos:

```bash
# En Ubuntu con ufw:
sudo ufw allow 6001/tcp
sudo ufw allow 6002/tcp
sudo ufw allow 6003/tcp

# En Fedora/RHEL con firewalld:
sudo firewall-cmd --permanent --add-port=6001/tcp
sudo firewall-cmd --permanent --add-port=6002/tcp
sudo firewall-cmd --permanent --add-port=6003/tcp
sudo firewall-cmd --reload
```

---

## ▶️ Parte 3: Iniciar el Sistema

### Paso 3.1: Iniciar el coordinador

**En la PC coordinadora:**

#### Si tiene monitor/GUI:
```bash
cd ~/distributed-fs
python3 main.py --coordinador --gui
```

#### Si NO tiene monitor (servidor headless):
```bash
cd ~/distributed-fs
python3 main.py --coordinador --headless
```

**Salida esperada:**
```
🚀 Iniciando SADTF como COORDINADOR...
✅ Coordinador iniciado en 192.168.1.100:6001
📊 Capacidad: 70 MB
🖥️  Abriendo interfaz gráfica... (si usaste --gui)
```

**⚠️ IMPORTANTE:** El coordinador debe estar corriendo antes de iniciar los nodos.

---

### Paso 3.2: Iniciar los nodos trabajadores

**En cada nodo trabajador:**

```bash
cd ~/distributed-fs
python3 main.py --nodo --id 2 --gui
```

**Nota:** Cambia `--id 2` por el ID correcto:
- Nodo 2: `--id 2`
- Nodo 3: `--id 3`
- etc.

**Salida esperada:**
```
🚀 Iniciando SADTF como NODO trabajador (ID: 2)...
✅ Nodo iniciado en 192.168.1.101:6002
🔗 Conectado al coordinador 192.168.1.100:6001
🖥️  Abriendo interfaz gráfica...
```

Se abrirá una ventana con la interfaz gráfica.

---

### Paso 3.3: Verificar que todos están conectados

En la terminal del **coordinador**, deberías ver mensajes como:

```
🔗 Nodo 2 conectado desde 192.168.1.101:6002
🔗 Nodo 3 conectado desde 192.168.1.102:6003
```

---

## ✅ Parte 4: Prueba del Sistema

### Prueba 1: Subir un archivo

1. En **cualquier nodo con GUI**, haz clic en **"Cargar"**
2. Selecciona un archivo pequeño (ej: 2-5 MB)
3. Espera a que termine la subida
4. ✅ El archivo debe aparecer en **todas** las ventanas GUI

---

### Prueba 2: Ver distribución de bloques

1. Selecciona el archivo subido
2. Haz clic en **"Atributos"**
3. Verás algo como:

```
Archivo: documento.pdf
Tamaño: 3.2 MB
Bloques: 4

Bloque 1 → Nodo 2 (primario), Nodo 1 (réplica)
Bloque 2 → Nodo 3 (primario), Nodo 2 (réplica)
Bloque 3 → Nodo 2 (primario), Nodo 3 (réplica)
Bloque 4 → Nodo 1 (primario), Nodo 2 (réplica)
```

Esto confirma que:
- Los bloques están distribuidos entre los nodos
- Cada bloque tiene su réplica

---

### Prueba 3: Tolerancia a fallas

1. **Apaga uno de los nodos trabajadores** (Ctrl+C en su terminal)
2. En otro nodo, intenta **descargar el archivo**
3. ✅ Debe descargarse correctamente usando las réplicas

---

### Prueba 4: Descargar un archivo

1. Selecciona el archivo en la lista
2. Haz clic en **"Descargar"**
3. Elige dónde guardarlo
4. ✅ El archivo debe guardarse correctamente

Verifica que sea idéntico al original:

```bash
# Compara checksums:
sha256sum archivo_original.pdf
sha256sum archivo_descargado.pdf
# Deben ser iguales
```

---

## 🔧 Parte 5: Operación Continua

### Para usar el sistema diariamente

1. **Inicia el coordinador primero** (en el servidor):
   ```bash
   cd ~/distributed-fs
   python3 main.py --coordinador --headless
   ```

2. **Inicia los nodos** cuando los necesites:
   ```bash
   cd ~/distributed-fs
   python3 main.py --nodo --id N --gui
   ```

3. **Usa la GUI** para subir/descargar archivos

---

### Para mantener el coordinador corriendo permanentemente

Usa `systemd` o `screen`:

#### Opción A: Con screen (simple)
```bash
# Instalar screen si no lo tienes:
sudo apt-get install screen

# Crear sesión:
screen -S sadtf-coordinador

# Dentro de screen:
cd ~/distributed-fs
python3 main.py --coordinador --headless

# Detach con: Ctrl+A, luego D

# Reattach después:
screen -r sadtf-coordinador
```

#### Opción B: Con systemd (avanzado)
```bash
# Crear archivo de servicio:
sudo nano /etc/systemd/system/sadtf-coordinador.service
```

Contenido:
```ini
[Unit]
Description=SADTF Coordinador
After=network.target

[Service]
Type=simple
User=tuusuario
WorkingDirectory=/home/tuusuario/distributed-fs
ExecStart=/usr/bin/python3 main.py --coordinador --headless
Restart=always

[Install]
WantedBy=multi-user.target
```

Habilitar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sadtf-coordinador
sudo systemctl start sadtf-coordinador
```

---

## ➕ Parte 6: Agregar Más Nodos (Opcional)

Para agregar un nuevo nodo:

1. **En TODAS las computadoras existentes**, edita `config.json`:
   ```json
   {
     "nodos": [
       ... nodos existentes ...
       {
         "id": 4,
         "nombre": "nuevo-nodo",
         "ip": "192.168.1.103",
         "puerto": 6004,
         "capacidad_mb": 70,
         "es_coordinador": false
       }
     ]
   }
   ```

2. **En el nuevo nodo**, clona el repositorio e inicia:
   ```bash
   cd ~/distributed-fs
   python3 main.py --nodo --id 4 --gui
   ```

3. ✅ El nuevo nodo se conectará automáticamente

---

## 📊 Parte 7: Monitoreo y Logs

### Ver logs del sistema

```bash
# En cualquier nodo:
cd ~/distributed-fs

# Ver logs en tiempo real:
tail -f logs/system.log

# Buscar errores:
grep -i error logs/system.log

# Ver últimas 50 líneas:
tail -n 50 logs/system.log
```

### Verificar espacio usado

```bash
# Ver bloques almacenados:
du -sh espacioCompartido/

# Contar archivos de bloques:
ls -1 espacioCompartido/ | wc -l
```

---

## ⚠️ Solución de Problemas Comunes

### Problema: "No se puede conectar al coordinador"

**Causa:** Coordinador no está corriendo o firewall bloqueando.

**Solución:**
```bash
# 1. Verificar que el coordinador esté corriendo:
ps aux | grep "main.py --coordinador"

# 2. Verificar conectividad:
ping 192.168.1.100

# 3. Verificar puerto:
telnet 192.168.1.100 6001
```

---

### Problema: "Tkinter no funciona"

**Causa:** python3-tk no instalado.

**Solución:**
```bash
sudo apt-get install python3-tk
```

---

### Problema: "Puerto ya en uso"

**Causa:** Proceso anterior no terminó correctamente.

**Solución:**
```bash
# Encontrar proceso:
sudo lsof -i :6001

# Matar proceso:
kill -9 <PID>
```

---

## 🎉 ¡Implementación Completa!

Has implementado exitosamente SADTF con:
- ✅ Coordinador funcionando
- ✅ Múltiples nodos conectados
- ✅ Sistema de replicación activo
- ✅ Tolerancia a fallas verificada

### Próximos pasos recomendados:

1. **Documenta tu configuración:** Guarda las IPs y puertos en un lugar seguro
2. **Haz backups:** Especialmente de `config.json` y `metadata/`
3. **Monitorea el sistema:** Revisa los logs periódicamente
4. **Expande gradualmente:** Agrega más nodos según necesites

---

## 📚 Recursos Adicionales

- **README.md**: Documentación general del proyecto
- **QUICK_START.md**: Guía rápida de comandos
- **docs/CONFIGURACION_NODOS.md**: Detalles técnicos de configuración

---

**Autor:** Nerfe5  
**Versión de esta guía:** 1.0  
**Última actualización:** Noviembre 2025
