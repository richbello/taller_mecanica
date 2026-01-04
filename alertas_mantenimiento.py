import json
import datetime
import requests
import os

# Configuración de SendGrid
SENDGRID_API_KEY = "B1DGK5LLAESYRXPHX567JJC6"
FROM_EMAIL = "richbello@gmail.com"
TO_EMAILS = ["richbello@gmail.com", "richardbello2020@gmail.com"]  # puedes agregar más

# Ruta del archivo JSON
json_path = "C:/RICHARD/RB/2025/Taller_mecánica/ordenes_taller.json"
print(f"📂 Verificando ruta: {json_path}")

# Cargar órdenes
try:
    with open(json_path, "r", encoding="utf-8") as f:
        ordenes = json.load(f)
except Exception as e:
    print(f"⚠️ Error leyendo JSON: {e}")
    ordenes = []

# Fecha actual
hoy = datetime.datetime.now()

# Función para enviar correo por SendGrid
def enviar_alerta(codigo, servicio, fecha):
    asunto = f"Alerta: {servicio} pendiente"
    cuerpo = f"El vehículo {codigo} tiene programado el servicio de {servicio} para el {fecha}."

    data = {
        "personalizations": [
            {
                "to": [{"email": correo} for correo in TO_EMAILS],
                "subject": asunto
            }
        ],
        "from": {"email": FROM_EMAIL},
        "content": [
            {
                "type": "text/plain",
                "value": cuerpo
            }
        ]
    }

    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data
        )

        if response.status_code == 202:
            print(f"✅ Correo enviado a {', '.join(TO_EMAILS)} con asunto: {asunto}")
        else:
            print(f"⚠️ Error al enviar correo: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Error inesperado al enviar correo: {e}")

# Revisar cada orden
for orden in ordenes:
    codigo = orden.get("codigo", "N/A")
    servicio = orden.get("servicio", "N/A")
    fecha_str = orden.get("fecha", "")

    print(f"🔎 Revisando {codigo} - {servicio} - fecha {fecha_str}")

    try:
        fecha_obj = datetime.datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
        dias_restantes = (fecha_obj - hoy).days

        if dias_restantes <= 7:
            enviar_alerta(codigo, servicio, fecha_str)
        else:
            print(f"✅ {codigo} aún no requiere {servicio}.")
    except Exception as e:
        print(f"⚠️ Error procesando fecha de {codigo}: {e}")
