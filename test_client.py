#!/usr/bin/env python3
from src.network import NetworkManager, NetworkMessage
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

print('='*60)
print('  Cliente SADTF - Nodo 2 (WSL)')
print('='*60)

# Crear cliente
client = NetworkManager(
    node_id=2,
    host="172.19.127.188",
    port=5002
)

print('\n🔍 Probando conexión al servidor Ubuntu...')
print('   IP: 192.168.0.151')
print('   Puerto: 5001\n')

# Test 1: Ping
print('1️⃣ Test de PING...')
if client.ping_node("192.168.0.151", 5001):
    print('   ✅ PING exitoso - El servidor responde!\n')
    
    # Test 2: Obtener estado
    print('2️⃣ Solicitando estado del servidor...')
    message = NetworkMessage(NetworkMessage.GET_STATUS, {}, 2)
    response = client.send_message_to_node("192.168.0.151", 5001, message)
    
    if response:
        print(f'   ✅ Estado recibido: {response.data}')
        print(f'   📊 Servidor: Nodo {response.data.get("node_id")}')
        print(f'   📊 Status: {response.data.get("status")}\n')
        
        print('✅ ¡Todas las pruebas pasaron correctamente!')
        print('🎉 La comunicación entre nodos funciona perfectamente\n')
    else:
        print('   ❌ No se recibió respuesta del servidor\n')
else:
    print('   ❌ PING falló - No se puede conectar al servidor\n')
    print('🔍 Diagnóstico:')
    print('   Verifica:')
    print('   1. Que el servidor esté corriendo (python3 test_server.py)')
    print('   2. Que el firewall permita la conexión')
    print('   3. Que las IPs en config.json sean correctas')
    print('   4. Que el puerto 5001 esté abierto en el servidor\n')
    print('💡 Comandos útiles:')
    print('   # En el servidor Ubuntu:')
    print('   sudo ufw allow from 172.19.127.188 to any port 5001')
    print('   sudo ss -tulpn | grep 5001')
    print('')
