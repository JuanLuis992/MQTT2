import paho.mqtt.client as mqtt
from nicegui import ui
import requests


# Configuración MQTT - usando HiveMQ público
broker = 'server-production-952c.up.railway.app'
port = 8080

# Configuración Telegram
BOT_TOKEN = '7825032716:AAHBXTpOYpN6bYU3WausHv9T1S6Kg1EsmoA'
CHAT_ID = '7536996477'
alarma_enviada = False

# Función para enviar mensajes a Telegram
def enviar_telegram(mensaje):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': mensaje}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ Mensaje enviado a Telegram correctamente.")
    else:
        print(f"❌ Error al enviar mensaje. Código HTTP: {response.status_code}")
        print(response.text)

# Callback al conectar
def on_connect(client, userdata, flags, rc):
    print(f'Conectado con código {rc}')
    client.subscribe("boton1")
    client.subscribe("boton2")
    client.subscribe("boton3")
    client.subscribe("led/pwm")
    client.subscribe("sensor/temp")
    client.subscribe("sensor/industrial")

# Callback al recibir mensaje
def on_message(client, userdata, msg):
    global alarma_enviada
    valor = msg.payload.decode()
    print(f"Mensaje recibido en {msg.topic}: {valor}")

    if msg.topic == "boton1":
        estado_label.set_text(f"Estado Botón 1: {valor}")
    elif msg.topic == "boton2":
        estado_label.set_text(f"Estado Botón 2: {valor}")
    elif msg.topic == "boton3":
        estado_label.set_text(f"Estado Botón 3: {valor}")
    elif msg.topic == "sensor/temp":
        label_temp.set_text(f"Temperatura: {valor} °C")
    elif msg.topic == "sensor/industrial":
        label_pz.set_text(f'No. de piezas: {valor}')
        try:
            piezas = int(valor)
            if piezas >= 20 and not alarma_enviada:
                enviar_telegram("🚨 Alarma: Se han contado 20 piezas.")
                alarma_enviada = True
            elif piezas < 20:
                alarma_enviada = False
        except ValueError:
            print("Valor recibido no es un número válido.")

# Cliente MQTT
client = mqtt.Client(transport="websockets")
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port, 60)
client.loop_start()

# Función para publicar el valor del slider
def publish_slider_value(value):
    client.publish("led/pwm", str(value))
    label_value.text = f'Valor del PWM: {value}'

# Acciones de botones
def boton1_presionado():
    client.publish("boton1", "1")
    estado_label.set_text('Botón 1 Presionado')

def boton1_soltado():
    client.publish("boton1", "0")
    estado_label.set_text('Botón 1 Soltado')

def boton2_presionado():
    client.publish("boton2", "1")
    estado_label.set_text('Botón 2 Presionado')

def boton2_soltado():
    client.publish("boton2", "0")
    estado_label.set_text('Botón 2 Soltado')

def boton3_presionado():
    client.publish("boton3", "1")
    estado_label.set_text('Botón 3 Presionado')

def boton3_soltado():
    client.publish("boton3", "0")
    estado_label.set_text('Botón 3 Soltado')

# Interfaz NiceGUI
label_value = ui.label('Control de LED PWM: 0')
slider = ui.slider(min=0, max=255, value=0, on_change=lambda e: publish_slider_value(e.value))

label_temp = ui.label('Temperatura: 0 °C')
label_pz = ui.label('No. de Piezas: 0')

boton1 = ui.button('Izquierda')
boton1.on('mousedown', boton1_presionado)
boton1.on('mouseup', boton1_soltado)

boton2 = ui.button('Derecha')
boton2.on('mousedown', boton2_presionado)
boton2.on('mouseup', boton2_soltado)

boton3 = ui.button('Paro')
boton3.on('mousedown', boton3_presionado)
boton3.on('mouseup', boton3_soltado)

estado_label = ui.label('Estado de los botones')

ui.run()
