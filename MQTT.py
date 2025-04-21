from nicegui import ui
import requests

# --- Configuración Telegram ---
BOT_TOKEN = '7825032716:AAHBXTpOYpN6bYU3WausHv9T1S6Kg1EsmoA'
CHAT_ID = '7536996477'
alarma_enviada = False

# --- Interfaz gráfica con NiceGUI ---
label_temp = ui.label('Temperatura: 0 °C').props('id=label_temp')
label_pz = ui.label('No. de piezas: 0').props('id=label_pz')
estado_label = ui.label('Estado de los botones').props('id=estado_label')
label_pwm = ui.label('Control de LED PWM: 0').props('id=label_pwm')

slider = ui.slider(min=0, max=255).on('change', lambda e: ui.run_javascript(
    f"mqttClient.publish('led/pwm', '{e.value}'); document.getElementById('label_pwm').innerText = 'Control de LED PWM: {e.value}';"
))

ui.button('Izquierda').on('mousedown', lambda: ui.run_javascript("mqttClient.publish('boton1', '1')")) \
                      .on('mouseup', lambda: ui.run_javascript("mqttClient.publish('boton1', '0')"))

ui.button('Derecha').on('mousedown', lambda: ui.run_javascript("mqttClient.publish('boton2', '1')")) \
                    .on('mouseup', lambda: ui.run_javascript("mqttClient.publish('boton2', '0')"))

ui.button('Paro').on('mousedown', lambda: ui.run_javascript("mqttClient.publish('boton3', '1')")) \
                 .on('mouseup', lambda: ui.run_javascript("mqttClient.publish('boton3', '0')"))

# --- Agregar librería MQTT.js al frontend ---
ui.add_head_html('''
<script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script>
''')

# --- Ejecutar JavaScript solo después de que UI esté listo ---
@ui.page('/')
def index():
    ui.run_javascript("""
        const client = mqtt.connect('ws://server-production-952c.up.railway.app');

        client.on('connect', () => {
            console.log('✅ Conectado al broker MQTT por WebSocket');
            client.subscribe('sensor/temp');
            client.subscribe('sensor/industrial');
            client.subscribe('boton1');
            client.subscribe('boton2');
            client.subscribe('boton3');
            client.subscribe('led/pwm');
        });

        client.on('message', (topic, message) => {
            const msg = message.toString();
            console.log(`📩 ${topic}: ${msg}`);

            if (topic === 'sensor/temp') {
                document.getElementById('label_temp').innerText = `Temperatura: ${msg} °C`;
            }
            if (topic === 'sensor/industrial') {
                document.getElementById('label_pz').innerText = `No. de piezas: ${msg}`;

                const piezas = parseInt(msg);
                if (!isNaN(piezas) && piezas >= 20) {
                    fetch('/alarma');
                }
            }
            if (topic === 'boton1') {
                document.getElementById('estado_label').innerText = `Estado Botón 1: ${msg}`;
            }
            if (topic === 'boton2') {
                document.getElementById('estado_label').innerText = `Estado Botón 2: ${msg}`;
            }
            if (topic === 'boton3') {
                document.getElementById('estado_label').innerText = `Estado Botón 3: ${msg}`;
            }
        });

        window.mqttClient = client;
    """)

# --- BACKEND: Ruta para enviar Telegram ---
@ui.page('/alarma')
def enviar_alarma():
    global alarma_enviada
    if not alarma_enviada:
        mensaje = "🚨 Alarma: Se han contado 20 piezas."
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {'chat_id': CHAT_ID, 'text': mensaje}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Mensaje enviado a Telegram.")
            alarma_enviada = True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
    return 'OK'

# Ejecutar la interfaz
ui.run(host="0.0.0.0", port=80)

