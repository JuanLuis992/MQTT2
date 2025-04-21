import paho.mqtt.client as mqtt

# Configuración MQTT
broker = 'server-production-952c.up.railway.app'
port = 80  # Asegúrate de que esté configurado para WebSocket en Railway

# Callback al conectar
def on_connect(client, userdata, flags, rc):
    print(f'Conectado con código {rc}')
    client.subscribe("test/topic")  # Cambia el tópico para probar

# Callback al recibir mensaje
def on_message(client, userdata, msg):
    print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")

# Cliente MQTT
client = mqtt.Client(transport="websockets")
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port, 60)

client.loop_start()
