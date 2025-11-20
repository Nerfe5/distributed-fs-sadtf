# 🖥️ Configuración de Nodos - SADTF

## Información de tu Red

### 📍 IPs Configuradas:

- **Servidor Ubuntu (Nodo 1 - Coordinador):** `192.168.0.151:5001`
- **WSL (Nodo 2):** `172.19.127.188:5002`

---

## 🔧 Configuración del Servidor Ubuntu (Nodo 1)

### 1. Verificar Conectividad SSH

Desde tu WSL, verifica que puedas conectarte:

```bash
ssh alejandro@192.168.0.151
```

### 2. Clonar/Copiar el Proyecto

**Opción A: Si el servidor tiene acceso a GitHub:**

```bash
# En el servidor Ubuntu
cd ~
git clone git@github.com:Nerfe5/distributed-fs-sadtf.git distributed-fs
cd distributed-fs
git checkout feature/network-module
```

**Opción B: Copiar desde WSL via SCP:**

```bash
# Desde tu WSL
cd /home/alejandro
scp -r distributed-fs alejandro@192.168.0.151:~/
```

### 3. Verificar Python y Dependencias

```bash
# En el servidor Ubuntu
python3 --version  # Debe ser 3.8+
python3 -c "import socket, json, threading; print('Dependencias OK')"
```

### 4. Verificar Puertos Disponibles

El sistema usa los siguientes puertos:

- **5001**: Nodo 1 (Servidor Ubuntu)
- **5002**: Nodo 2 (WSL)

Verifica que no estén en uso:

```bash
# En el servidor Ubuntu
sudo netstat -tulpn | grep 5001
# O si no tienes netstat:
sudo ss -tulpn | grep 5001
```

**Si el puerto está ocupado**, puedes:
- Cambiar el puerto en `config/config.json`
- O detener el servicio que lo usa

### 5. Configurar Firewall (IMPORTANTE)

Como tu servidor tiene otros servicios corriendo, necesitamos abrir el puerto 5001 **solo para tu WSL**:

```bash
# En el servidor Ubuntu
# Permitir puerto 5001 desde tu WSL
sudo ufw allow from 172.19.127.188 to any port 5001
sudo ufw allow from 172.19.127.188 to any port 5000

# Verificar reglas
sudo ufw status numbered
```

**Nota:** Esto es más seguro que abrir el puerto para todo el mundo.

---

## 🖥️ Configuración de WSL (Nodo 2)

### 1. Verificar que el Proyecto Esté Actualizado

```bash
# En WSL
cd ~/distributed-fs
git status
git checkout feature/network-module
git pull origin feature/network-module
```

### 2. Verificar Conectividad con el Servidor

```bash
# Probar conexión SSH
ssh alejandro@192.168.0.151

# Probar ping
ping -c 3 192.168.0.151

# Probar conexión al puerto 5001
nc -zv 192.168.0.151 5001
# O si no tienes nc:
telnet 192.168.0.151 5001
```

---

## 🧪 Prueba de Comunicación Entre Nodos

### Prueba 1: Comunicación Local (en WSL)

```bash
cd ~/distributed-fs
python3 src/network.py
```

Deberías ver:
```
✅ Nodo 1 escuchando en localhost:9001
✅ Ping exitoso - El servidor responde
✅ ¡Todas las pruebas pasaron correctamente!
```

### Prueba 2: Servidor Ubuntu Escuchando

**En el servidor Ubuntu:**

```python
# Crear archivo test_server.py
cat > ~/distributed-fs/test_server.py << 'EOF'
from src.network import NetworkManager
import time

# Iniciar servidor en el puerto 5001
server = NetworkManager(
    node_id=1,
    host="0.0.0.0",  # Escuchar en todas las interfaces
    port=5001
)

print("Iniciando servidor en 0.0.0.0:5001...")
if server.start_server():
    print("Servidor listo. Presiona Ctrl+C para detener.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        server.stop_server()
else:
    print("Error al iniciar servidor")
EOF

# Ejecutar
python3 test_server.py
```

### Prueba 3: Cliente desde WSL

**En tu WSL (mientras el servidor Ubuntu está corriendo):**

```python
# Crear archivo test_client.py
cat > ~/distributed-fs/test_client.py << 'EOF'
from src.network import NetworkManager, NetworkMessage

# Crear cliente
client = NetworkManager(
    node_id=2,
    host="172.19.127.188",
    port=5002
)

print("Haciendo ping al servidor Ubuntu...")
if client.ping_node("192.168.0.151", 5001):
    print("✅ Servidor Ubuntu responde!")
    
    # Enviar mensaje de estado
    message = NetworkMessage(NetworkMessage.GET_STATUS, {}, 2)
    response = client.send_message_to_node("192.168.0.151", 5001, message)
    
    if response:
        print(f"✅ Estado del servidor: {response.data}")
    else:
        print("❌ No se recibió respuesta")
else:
    print("❌ No se puede conectar al servidor")
    print("Verifica:")
    print("  1. Que el servidor esté corriendo")
    print("  2. Que el firewall permita la conexión")
    print("  3. Que las IPs en config.json sean correctas")
EOF

# Ejecutar
python3 test_client.py
```

---

## 🔍 Troubleshooting

### Problema: "Connection refused"

**Causas posibles:**
1. El servidor no está corriendo
2. Firewall bloqueando el puerto
3. IP incorrecta

**Solución:**
```bash
# En el servidor Ubuntu
# 1. Verificar si algo escucha en 5001
sudo netstat -tulpn | grep 5001

# 2. Verificar firewall
sudo ufw status | grep 5001

# 3. Permitir temporalmente todo (solo para pruebas)
sudo ufw allow 5001
```

### Problema: "Timeout"

**Causas posibles:**
1. Red lenta
2. Servidor sobrecargado
3. Timeout muy corto

**Solución:**
Aumentar timeout en `config/config.json`:
```json
"red": {
  "timeout_segundos": 10
}
```

### Problema: "Port already in use"

**Solución:**
```bash
# Ver qué proceso usa el puerto
sudo lsof -i :5001

# Matar el proceso (si es seguro)
sudo kill -9 PID

# O cambiar el puerto en config.json
```

---

## 📊 Monitoreo de Red

### Ver Conexiones Activas

```bash
# En el servidor Ubuntu
watch -n 1 'sudo ss -tulpn | grep 500'
```

### Ver Logs del Sistema

```bash
# Ver logs en tiempo real
tail -f ~/distributed-fs/logs/sistema.log
```

### Verificar Uso de Recursos

```bash
# CPU y memoria
htop

# Red
iftop  # Requiere sudo
```

---

## 🔒 Seguridad

### Recomendaciones:

1. **NO abrir los puertos 5000-5002 al público**
   - Solo permitir conexiones desde IPs conocidas (tu WSL, otros nodos)

2. **Usar IPs privadas cuando sea posible**
   - Tu configuración actual es correcta (192.168.x.x es red privada)

3. **Monitorear conexiones sospechosas**
   ```bash
   sudo tail -f /var/log/auth.log | grep "Failed"
   ```

4. **Backup regular del directorio metadata/**
   ```bash
   # Crear backup diario
   tar -czf ~/backups/metadata-$(date +%Y%m%d).tar.gz ~/distributed-fs/metadata/
   ```

---

## 📝 Checklist de Configuración

Antes de usar el sistema en producción, verifica:

### En el Servidor Ubuntu:
- [ ] Python 3.8+ instalado
- [ ] Proyecto clonado/copiado
- [ ] Puerto 5001 disponible
- [ ] Firewall configurado (ufw allow from WSL_IP)
- [ ] SSH funcionando

### En WSL:
- [ ] Python 3.8+ instalado
- [ ] Proyecto actualizado
- [ ] Puede hacer ping al servidor
- [ ] Puerto 5002 disponible
- [ ] IPs en config.json correctas

### Ambos Nodos:
- [ ] Conexión de red estable
- [ ] Carpetas creadas (espacioCompartido, metadata, logs)
- [ ] Permisos de lectura/escritura en las carpetas

---

## 🚀 Próximos Pasos

Una vez que la comunicación funcione:

1. **Desarrollar el coordinador** (coordinator.py)
2. **Desarrollar el nodo** (node.py)
3. **Probar transferencia de bloques**
4. **Desarrollar la GUI**

---

**Última actualización:** Noviembre 2025  
**Autor:** Nerfe5  
**Proyecto:** SADTF - Sistema de Archivos Distribuido Tolerante a Fallas
