import paho.mqtt.client as mqtt
from nicegui import ui
import requests
from collections import deque
from datetime import datetime
import socket
import threading

# Configuración MQTT con Railway
broker = "switchyard.proxy.rlwy.net"  # broker MQTT en Railway
port = 57529  # El puerto proporcionado por Railway

HOST = '0.0.0.0'
PORT = 5000

# Telegram
BOT_TOKEN = "7825032716:AAHBXTpOYpN6bYU3WausHv9T1S6Kg1EsmoA"
CHAT_ID = "7536996477"
alarma_enviada = False

# Variables para la gráfica
temp_data = deque(maxlen=50)  # Últimos 50 datos
time_data = deque(maxlen=50)

# Función para enviar mensajes a Telegram
def enviar_telegram(mensaje):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': mensaje}
    response = requests.post(url, data=data)
    print("Telegram OK" if response.status_code == 200 else f"Error Telegram {response.status_code}")

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
        try:
            temp = float(valor)
            now = datetime.now().strftime('%H:%M:%S')
            temp_data.append(temp)
            time_data.append(now)
            with line_plot:
                line_plot.options['xAxis']['data'] = list(time_data)
                line_plot.options['series'][0]['data'] = list(temp_data)
                line_plot.update()
        except ValueError:
            print("Temperatura no válida")
    elif msg.topic == "sensor/industrial":
        label_pz.set_text(f'No. de piezas: {valor}')
        try:
            piezas = int(valor)
            if piezas >= 20 and not alarma_enviada:
                enviar_telegram("Alarma: Se han contado 20 piezas.")
                alarma_enviada = True
            elif piezas < 20:
                alarma_enviada = False
        except ValueError:
            print("Valor no válido")

# Cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# -------- Servidor TCP para recibir datos del ESP32 --------
def tcp_handler():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Servidor TCP escuchando en {HOST}:{PORT}")
        conn, addr = s.accept()
        with conn:
            print(f"Conectado desde {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    mensaje = data.decode().strip()
                    print(f"TCP recibido: {mensaje}")
                    if "=" in mensaje:
                        topic, valor = mensaje.split("=")
                        topic = topic.strip()
                        valor = valor.strip()
                        client.publish(topic, valor)
                except Exception as e:
                    print(f"Error al procesar mensaje TCP: {e}")

# Lanzar el hilo TCP
tcp_thread = threading.Thread(target=tcp_handler, daemon=True)
tcp_thread.start()

# Conectar al broker MQTT
client.connect(broker, port, 60)
client.loop_start()

# Función para publicar el valor del slider
def publish_slider_value(value):
    client.publish("led/pwm", str(value))
    label_value.text = f'Valor del PWM: {value}'

# Botones
def boton1_presionado(): client.publish("boton1", "1"); estado_label.set_text('Botón 1 Presionado')
def boton1_soltado(): client.publish("boton1", "0"); estado_label.set_text('Botón 1 Soltado')
def boton2_presionado(): client.publish("boton2", "1"); estado_label.set_text('Botón 2 Presionado')
def boton2_soltado(): client.publish("boton2", "0"); estado_label.set_text('Botón 2 Soltado')
def boton3_presionado(): client.publish("boton3", "1"); estado_label.set_text('Botón 3 Presionado')
def boton3_soltado(): client.publish("boton3", "0"); estado_label.set_text('Botón 3 Soltado')

# UI NiceGUI
label_value = ui.label('Control de LED PWM: 0')
slider = ui.slider(min=0, max=255, value=0, on_change=lambda e: publish_slider_value(e.value))

label_temp = ui.label('Temperatura: 0 °C')
label_pz = ui.label('No. de Piezas: 0')

boton1 = ui.button('Izquierda'); boton1.on('mousedown', boton1_presionado); boton1.on('mouseup', boton1_soltado)
boton2 = ui.button('Derecha'); boton2.on('mousedown', boton2_presionado); boton2.on('mouseup', boton2_soltado)
boton3 = ui.button('Paro'); boton3.on('mousedown', boton3_presionado); boton3.on('mouseup', boton3_soltado)

estado_label = ui.label('Estado de los botones')

# Gráfica de temperatura
ui.label('Gráfica de Temperatura en Tiempo Real')
with ui.echart({
    'xAxis': {'type': 'category', 'data': []},
    'yAxis': {'type': 'value'},
    'series': [{'type': 'line', 'data': []}]
}) as line_plot:
    pass

ui.run(port=5000)
