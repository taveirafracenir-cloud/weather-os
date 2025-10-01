import psutil
import xml.etree.ElementTree as ET
from datetime import datetime
import time

def gerar_status_xml(arquivo="status.xml"):
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

    # Bateria (se disponível)
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

    # Criar XML
    root = ET.Element("server_monitor")
    ET.SubElement(ET.SubElement(root, "cpu"), "usage_percent").text = str(status["cpu"])
    
    mem = ET.SubElement(root, "memory")
    ET.SubElement(mem, "usage_percent").text = str(status["memory_percent"])
    ET.SubElement(mem, "total_gb").text = str(status["memory_total"])
    ET.SubElement(mem, "available_gb").text = str(status["memory_available"])
    
    disk = ET.SubElement(root, "disk")
    ET.SubElement(disk, "usage_percent").text = str(status["disk_percent"])
    ET.SubElement(disk, "total_gb").text = str(status["disk_total"])
    ET.SubElement(disk, "free_gb").text = str(status["disk_free"])
    
    net = ET.SubElement(root, "network")
    ET.SubElement(net, "sent_mb").text = str(status["network_sent"])
    ET.SubElement(net, "received_mb").text = str(status["network_recv"])
    
    bat = ET.SubElement(root, "battery")
    ET.SubElement(bat, "percent").text = str(status["battery_percent"])
    ET.SubElement(bat, "plugged").text = str(status["battery_plugged"])
    
    ET.SubElement(root, "timestamp").text = datetime.now().isoformat()
    
    tree = ET.ElementTree(root)
    tree.write(arquivo, encoding="utf-8", xml_declaration=True)

# Loop principal para atualizar XML a cada 5 segundos
try:
    while True:
        gerar_status_xml("status.xml")
        print("Arquivo status.xml atualizado!")
        time.sleep(5)
except KeyboardInterrupt:
    print("Monitoramento encerrado pelo usuário.")
