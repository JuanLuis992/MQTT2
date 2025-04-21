from nicegui import ui
import requests

# --- Configuración Telegram (esto sí sigue en el backend) ---
BOT_TOKEN = '7825032716:AAHBXTpOYpN6bYU3WausHv9T1S6Kg1EsmoA'
CHAT_ID = '7536996477'
alarma_enviada = False

# --- Agregar librería MQTT.js al frontend ---
ui.add_head_html('''
<script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script>
''')

# --- Script para conectarse al broker MQTT WebSocket desde el navegador ---
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

      // Lógica para detección de alarma y enviar al backend de Python
      const piezas = parseInt(msg);
      if (!isNaN(piezas) && piezas >= 20) {
        fetch('/alarma');  // Llama a la ruta backend para enviar Telegram
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

  window.mqttClient = client;  // Exponer client globalmente
""")

# --- BACKEND: Ruta para enviar Telegram cuando el frontend detecta 20 piezas ---
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

# --- Interfaz gráfica con NiceGUI ---

ui.label('Control de LED PWM: 0').props('id=label_pwm')
ui.slider(min=0, max=255).on('change', lambda e: ui.run_javascript(
    f"mqttClient.publish('led/pwm', '{e.value}'); document.getElementById('label_pwm').innerText = 'Control de LED PWM: {e.value}';"
))

ui.label('Temperatura: 0 °C').props('id=label_temp')
ui.label('No. de piezas: 0').props('id=label_pz')

ui.button('Izquierda').on('mousedown', lambda: ui.run_javascript("mqttClient.publish('boton1', '1')")) \
                      .on('mouseup', lambda: ui.run_javascript("mqttClient.publish('boton1', '0')"))

ui.button('Derecha').on('mousedown', lambda: ui.run_javascript("mqttClient.publish('boton2', '1')")) \
                    .on('mouseup', lambda: ui.run_javascript("mqttClient.publish('boton2', '0')"))

ui.button('Paro').on('mousedown', lambda: ui.run_javascript("mqttClient.publish('boton3', '1')")) \
                 .on('mouseup', lambda: ui.run_javascript("mqttClient.publish('boton3', '0')"))

ui.label('Estado de los botones').props('id=estado_label')

# Ejecutar interfaz
ui.run()
