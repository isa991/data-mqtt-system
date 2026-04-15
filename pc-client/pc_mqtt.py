# pc_mqtt.py

# Aplicacao MQTT no PC - Envia comandos e recebe dados do microcontrolador
import paho.mqtt.client as mqtt
import time
import json

# ---- Configuracoes ----
BROKER = "broker.mqttdashboard.com"
PORTA = 1883
TOPICO_PUBLICAR = "pucpr/pc/comandos" # PC publica aqui
TOPICO_ASSINAR = "pucpr/micro/dados" # PC recebe daqui
CLIENT_ID = "pc-pucpr-001"

# ---- Callbacks ----
def on_connect(client, userdata, flags, rc, properties):
# Chamada quando a conexao com o broker e estabelecida.
    if rc == 0:
        print("[PC] Conectado ao broker MQTT!")
        client.subscribe(TOPICO_ASSINAR, qos=1)
        print(f"[PC] Inscrito no topico: {TOPICO_ASSINAR}")
    else:
        print(f"[PC] Falha na conexao, codigo: {rc}")

def on_message(client, userdata, msg):
# Chamada quando uma mensagem e recebida.
    payload = msg.payload.decode("utf-8")
    print(f"[PC] Mensagem recebida em '{msg.topic}': {payload}")
    # Tenta interpretar como JSON
    try:
        dados = json.loads(payload)
        if "temperatura" in dados:
            print(f" -> Temperatura: {dados['temperatura']} C")
        
        if "umidade" in dados:
            print(f" -> Umidade: {dados['umidade']} %")

        if "led" in dados:
            print(f" -> Estado do LED: {dados['led']}")
    except json.JSONDecodeError:
        print(f" -> Dado em texto puro: {payload}")

def on_disconnect(client, userdata, flags, rc, properties):
# Chamada quando a conexao e perdida.
    print(f"[PC] Desconectado do broker (rc={rc})")

# ---- Programa principal ----
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    print(f"[PC] Conectando a {BROKER}:{PORTA}...")
    client.connect(BROKER, PORTA, 60)
    client.loop_start()
    print("\n--- COMANDOS DISPONIVEIS ---")
    print(" led_on -> Liga o LED")
    print(" led_off -> Desliga o LED")
    print(" status -> Solicita dados do sensor")
    print(" sair -> Encerra o programa")
    print(" (ou digite qualquer texto para enviar)\n")
    try:
        while True:
            comando = input("[PC] Digite um comando: ").strip()
            if comando.lower() == "sair":
                break
            if comando:
                mensagem = json.dumps({"comando": comando})
                # Publicar mensagem com QoS 1
                client.publish(TOPICO_PUBLICAR, mensagem, qos=1)
                print(f"[PC] Publicado em '{TOPICO_PUBLICAR}': {mensagem}")
    except KeyboardInterrupt:
        print("\n[PC] Interrompido pelo usuario.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[PC] Encerrado.")

if __name__ == "__main__":
    main()
