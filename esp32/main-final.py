# main.py - Aplicacao MQTT no microcontrolador 
# Execute este arquivo pelo Thonny (Run > Run current script) 
  
import network 
from umqtt.simple import MQTTClient 
from machine import Pin, PWM
import time 
import json 
import random
import dht
from hcsr04 import HCSR04


# ==== CONFIGURACOES - ALTERE AQUI ==== 
SSID = "Visitantes"    # <-- Wi-Fi: nome da rede 
SENHA = ""             # <-- Wi-Fi: senha 
BROKER = "broker.mqttdashboard.com" 
PORTA = 1883 
CLIENT_ID = "micro-pucpr-40112784"       # Use seu RA para evitar conflito 
TOPICO_PUBLICAR = "pucpr/micro/dados"    # Micro publica aqui 
TOPICO_ASSINAR  = "pucpr/pc/comandos"    # Micro recebe daqui 

# LED integrado
led = Pin(5, Pin.OUT) 
led_estado = False

# DHT 11
sensor_dht = dht.DHT11(Pin(15))

# HC SR04
sensor_ultra = HCSR04(trigger_pin=22, echo_pin=23, echo_timeout_us=10000000)

# BUZZER
buzzer = PWM(Pin(14, Pin.OUT))

# ---- Conexao Wi-Fi ---- 
def conectar_wifi(): 
    wlan = network.WLAN(network.STA_IF) 
    wlan.active(True) 
    if not wlan.isconnected(): 
        print("Conectando ao Wi-Fi...") 
        wlan.connect(SSID, SENHA) 
        tentativas = 0 
        while not wlan.isconnected() and tentativas < 20: 
            time.sleep(1) 
            tentativas += 1 
            print(f"  Tentativa {tentativas}/20...") 
    if wlan.isconnected(): 
        print(f"Wi-Fi conectado! IP: {wlan.ifconfig()[0]}") 
        return True 
    else: 
        print("ERRO: Nao foi possivel conectar ao Wi-Fi") 
        return False 

# ---- Callback de mensagens recebidas ---- 
def callback_mensagem(topico, mensagem): 
    global led_estado 
    topico = topico.decode("utf-8") 
    payload = mensagem.decode("utf-8") 
    print(f"[MICRO] Recebido em '{topico}': {payload}") 
     
    try: 
        dados = json.loads(payload) 
        comando = dados.get("comando", "") 
         
        if comando == "led_on": 
            led.value(1) 
            led_estado = True 
            print("[MICRO] LED ligado!") 
            publicar_estado() 
             
        elif comando == "led_off": 
            led.value(0) 
            led_estado = False 
            print("[MICRO] LED desligado!") 
            publicar_estado()
            
        elif comando == "status": 
            publicar_dados_sensor() 
             
        else: 
            print(f"[MICRO] Comando desconhecido: {comando}") 
             
    except Exception as e: 
        print(f"[MICRO] Erro ao processar: {e}") 
  
# ---- Funcoes de publicacao ---- 
def publicar_estado(): 
    estado = "ligado" if led_estado else "desligado" 
    msg = json.dumps({"led": estado}) 
    client.publish(TOPICO_PUBLICAR, msg, qos=1) 
    print(f"[MICRO] Publicado: {msg}") 

def buzz(freq, tempo):
    buzzer.freq(freq)
    buzzer.duty(50)
    time.sleep(tempo)
    buzzer.duty(0)

def publicar_dados_sensor():
    sensor_dht.measure()
    dados = { 
        "temperatura": str(sensor_dht.temperature()),
        "umidade": str(sensor_dht.humidity()),
        "led": "ligado" if led_estado else "desligado",
        "distancia": str(sensor_ultra.distance_cm())
    } 
    msg = json.dumps(dados)
    buzz(300, 5)
    client.publish(TOPICO_PUBLICAR, msg, qos=1) 
    print(f"[MICRO] Dados publicados: {msg}")
    
# ---- Conexao e loop principal ---- 
if not conectar_wifi(): 
    print("Abortando: sem Wi-Fi.") 
    raise SystemExit 
  
print("[MICRO] Conectando ao broker MQTT...") 
client = MQTTClient(CLIENT_ID, BROKER, port=PORTA) 
client.set_callback(callback_mensagem) 
client.connect() 
print(f"[MICRO] Conectado a {BROKER}") 
  
client.subscribe(TOPICO_ASSINAR, qos=1) 
print(f"[MICRO] Inscrito em: {TOPICO_ASSINAR}") 
print("[MICRO] Aguardando comandos...\n") 
  
contador = 0 
try: 
    while True:
        try:
            client.check_msg()
        except Exception as e: 
            print(f"[MICRO] Erro ao processar: {e}")
            client.disconnect()
            client.connect() 
        
        try:
            publicar_dados_sensor()
            
        except Exception as e: 
            print(f"[MICRO] Erro ao processar: {e}")
            client.disconnect()
            client.connect() 
         
        time.sleep(3) 
  
except KeyboardInterrupt: 
    print("\n[MICRO] Interrompido pelo usuario.") 
    client.disconnect() 
    print("[MICRO] Desconectado do broker.") 
