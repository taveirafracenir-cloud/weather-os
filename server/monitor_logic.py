import psutil
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os
import requests

# --- CONFIGURAÇÕES ---
API_KEY = "SUA_CHAVE_OPENWEATHER"  # Troque pela sua chave
CIDADE = "São Paulo,BR"
URL_WEATHER = f"http://api.openweathermap.org/data/2.5/weather?q={CIDADE}&appid={API_KEY}&units=metric"

LIMITE_CPU = 80
LIMITE_MEM = 80
LIMITE_DISCO = 90
INTERVALO_ATUALIZACAO = 5       # Atualiza status.xml a cada 5s
INTERVALO_LOG = 60             # Cria log histórico a cada 60s
PASTA_LOGS = "logs_xml"        # pasta para logs históricos

# Cria pasta de logs se não existir
if not os.path.exists(PASTA_LOGS):
    os.makedirs(PASTA_LOGS)

# --- FUNÇÕES ---
def coletar_status():
    """Coleta status do servidor"""
    status = {
        "cpu": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_total": round(psutil.virtual_memory().total / (1024**3), 2),
        "memory_available": round(psutil.virtual_memory().available / (1024**3), 2),
        "disk_percent": psutil.disk_usage('/').percent,
        "disk_total": round(psutil.disk_usage('/').total / (1024**3), 2),
        "disk_free": round(psutil.disk_usage('/').free / (1024**3), 2),
        "network_sent": round(psutil.net_io_counters().bytes_sent / (1024*1024), 2),
        "network_recv": round(psutil.net_io_counters().bytes_recv / (1024*1024), 2)
    }

    try:
        bateria = psutil.sensors_battery()
        if bateria:
            status["battery_percent"] = bateria.percent
            status["battery_plugged"] = bateria.power_plugged
        else:
            status["battery_percent"] = "N/A"
            status["battery_plugged"] = "N/A"
    except:
        status["battery_percent"] = "Erro"
        status["battery_plugged"] = "Erro"

    return status

def pegar_previsao_tempo():
    """Obtém previsão do tempo da API"""
    try:
        resposta = requests.get(URL_WEATHER)
        dados = resposta.json()
        tempo = {
            "temperatura": dados['main']['temp'],
            "umidade": dados['main']['humidity'],
            "condicao": dados['weather'][0]['description'].title()
        }
        return tempo
    except:
        return {"temperatura": "Erro", "umidade": "Erro", "condicao": "Erro"}

def criar_xml(status, tempo, arquivo):
    """Cria XML com status do servidor, alertas e previsão do tempo"""
    root = ET.Element("server_monitor")
    
    # CPU
    ET.SubElement(ET.SubElement(root, "cpu"), "usage_percent").text = str(status["cpu"])
    
    # Memória
    mem = ET.SubElement(root, "memory")
    ET.SubElement(mem, "usage_percent").text = str(status["memory_percent"])
    ET.SubElement(mem, "total_gb").text = str(status["memory_total"])
    ET.SubElement(mem, "available_gb").text = str(status["memory_available"])
    
    # Disco
    disk = ET.SubElement(root, "disk")
    ET.SubElement(disk, "usage_percent").text = str(status["disk_percent"])
    ET.SubElement(disk, "total_gb").text = str(status["disk_total"])
    ET.SubElement(disk, "free_gb").text = str(status["disk_free"])
    
    # Rede
    net = ET.SubElement(root, "network")
    ET.SubElement(net, "sent_mb").text = str(status["network_sent"])
    ET.SubElement(net, "received_mb").text = str(status["network_recv"])
    
    # Bateria
    bat = ET.SubElement(root, "battery")
    ET.SubElement(bat, "percent").text = str(status["battery_percent"])
    ET.SubElement(bat, "plugged").text = str(status["battery_plugged"])
    
    # Timestamp
    ET.SubElement(root, "timestamp").text = datetime.now().isoformat()
    
    # Alertas
    alerts = ET.SubElement(root, "alerts")
    if status["cpu"] > LIMITE_CPU:
        ET.SubElement(alerts, "alert").text = f"CPU alta: {status['cpu']}%"
    if status["memory_percent"] > LIMITE_MEM:
        ET.SubElement(alerts, "alert").text = f"Memória alta: {status['memory_percent']}%"
    if status["disk_percent"] > LIMITE_DISCO:
        ET.SubElement(alerts, "alert").text = f"Disco cheio: {status['disk_percent']}%"
    
    # Previsão do tempo
    weather = ET.SubElement(root, "weather")
    ET.SubElement(weather, "temperatura").text = str(tempo["temperatura"])
    ET.SubElement(weather, "umidade").text = str(tempo["umidade"])
    ET.SubElement(weather, "condicao").text = str(tempo["condicao"])
    
    tree = ET.ElementTree(root)
    tree.write(arquivo, encoding="utf-8", xml_declaration=True)

# --- LOOP PRINCIPAL ---
ultimo_log = time.time()

try:
    while True:
        status_atual = coletar_status()
        tempo_atual = pegar_previsao_tempo()
        
        # Atualiza XML principal
        criar_xml(status_atual, tempo_atual, "status.xml")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] status.xml atualizado!")

        # Cria log histórico se passou o intervalo
        agora = time.time()
        if agora - ultimo_log >= INTERVALO_LOG:
            nome_log = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            caminho_log = os.path.join(PASTA_LOGS, nome_log)
            criar_xml(status_atual, tempo_atual, caminho_log)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Log histórico criado: {nome_log}")
            ultimo_log = agora

        time.sleep(INTERVALO_ATUALIZACAO)

except KeyboardInterrupt:
    print("Monitoramento encerrado pelo usuário.")
