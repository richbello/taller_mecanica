import requests

SENDGRID_API_KEY = "B1DGK5LLAESYRXPHX567JJC6"
FROM_EMAIL = "richbello@gmail.com"
TO_EMAIL = "richbello@gmail.com"  # puedes cambiarlo por otro destinatario

# Crear el cuerpo del correo
data = {
    "personalizations": [
        {
            "to": [{"email": TO_EMAIL}],
            "subject": "Alerta de prueba con SendGrid API"
        }
    ],
    "from": {"email": FROM_EMAIL},
    "content": [
        {
            "type": "text/plain",
            "value": "Este es un correo de prueba enviado desde Python usando la API HTTP de SendGrid."
        }
    ]
}

# Enviar la solicitud POST a la API de SendGrid
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
        print("✅ Correo enviado exitosamente con SendGrid API")
    else:
        print(f"⚠️ Error al enviar correo: {response.status_code} - {response.text}")

except Exception as e:
    print(f"⚠️ Error inesperado: {e}")

