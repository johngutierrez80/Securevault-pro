import httpx

from ..core.config import settings

MAILJET_API_URL = "https://api.mailjet.com/v3.1/send"


async def send_secret_email(to_email: str, site: str, secret_value: str, sender_email: str) -> bool:
    """Envía un secreto descifrado por email al destinatario indicado usando Mailjet."""
    if not settings.mailjet_api_key or not settings.mailjet_secret_key:
        print(f"[EMAIL] MAILJET_API_KEY no configurada. Secreto '{site}' no enviado a {to_email}.", flush=True)
        return False

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; border-top: 4px solid #4a9eff;">
                <h2 style="color: #333; margin-bottom: 4px;">SecureVault Pro</h2>
                <p style="color: #888; font-size: 13px; margin-top: 0;">Compartición segura de secreto</p>

                <p style="color: #555; font-size: 15px; line-height: 1.6;">
                    El usuario <strong>{sender_email}</strong> te ha compartido el siguiente secreto:
                </p>

                <div style="margin: 20px 0; padding: 4px 0;">
                    <p style="margin: 0 0 6px; font-size: 12px; color: #999; text-transform: uppercase; letter-spacing: 1px;">Nombre del secreto</p>
                    <p style="margin: 0; font-size: 16px; font-weight: bold; color: #333;">{site}</p>
                </div>

                <div style="margin: 20px 0; padding: 16px; background-color: #f0f4ff; border-radius: 6px; border-left: 4px solid #4a9eff;">
                    <p style="margin: 0 0 6px; font-size: 12px; color: #999; text-transform: uppercase; letter-spacing: 1px;">Valor</p>
                    <p style="margin: 0; font-family: monospace; font-size: 15px; color: #1a1a2e; word-break: break-all;">{secret_value}</p>
                </div>

                <p style="color: #e74c3c; font-size: 12px; margin-top: 24px; border-top: 1px solid #eee; padding-top: 16px;">
                    ⚠️ Este mensaje contiene información sensible. No lo reenvíes ni lo almacenes en texto plano.
                    Elimínalo después de usarlo.
                </p>
            </div>
        </body>
    </html>
    """
    text_content = (
        f"SecureVault Pro — Secreto compartido por {sender_email}\n\n"
        f"Nombre: {site}\n"
        f"Valor: {secret_value}\n\n"
        f"ADVERTENCIA: Esta información es sensible. Elimina este correo después de usarlo."
    )

    payload = {
        "Messages": [
            {
                "From": {
                    "Email": settings.mailjet_sender_email,
                    "Name": settings.mailjet_sender_name,
                },
                "To": [{"Email": to_email}],
                "Subject": f"[SecureVault Pro] Secreto compartido: {site}",
                "HTMLPart": html_content,
                "TextPart": text_content,
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                MAILJET_API_URL,
                json=payload,
                auth=(settings.mailjet_api_key, settings.mailjet_secret_key),
            )
        if response.status_code in (200, 201):
            data = response.json()
            msg_id = data.get("Messages", [{}])[0].get("To", [{}])[0].get("MessageID", "N/A")
            print(f"[EMAIL] Secreto '{site}' enviado a {to_email} | id: {msg_id}", flush=True)
            return True
        else:
            print(f"[EMAIL ERROR] {to_email} | status={response.status_code} | {response.text}", flush=True)
            return False
    except Exception as e:
        print(f"[EMAIL EXCEPTION] {to_email}: {type(e).__name__}: {e}", flush=True)
        return False
