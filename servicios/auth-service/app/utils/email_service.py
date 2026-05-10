import dns.resolver
import httpx
from email_validator import validate_email, EmailNotValidError

from ..core.config import settings

MAILJET_API_URL = "https://api.mailjet.com/v3.1/send"


async def _send_email(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """Envía email usando la API de Mailjet (200 emails/día gratis, sin restricción de destinatarios)."""
    if not settings.mailjet_api_key or not settings.mailjet_secret_key:
        print(f"[EMAIL] MAILJET_API_KEY no configurada. Token para {to_email} — revisar logs del servicio.", flush=True)
        return True
    payload = {
        "Messages": [
            {
                "From": {
                    "Email": settings.mailjet_sender_email,
                    "Name": settings.mailjet_sender_name,
                },
                "To": [{"Email": to_email}],
                "Subject": subject,
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
            print(f"[EMAIL] Enviado OK a {to_email} | id: {msg_id}", flush=True)
            return True
        else:
            print(f"[EMAIL ERROR] {to_email} | status={response.status_code} | {response.text}", flush=True)
            return False
    except Exception as e:
        print(f"[EMAIL EXCEPTION] {to_email}: {type(e).__name__}: {e}", flush=True)
        return False


async def validate_email_domain(email: str) -> bool:
    """Valida que el dominio del correo tenga MX records válidos"""
    try:
        # Validación básica
        valid = validate_email(email, check_deliverability=True)
        email_normalized = valid.email
        
        # Extraer dominio
        domain = email_normalized.split("@")[1]
        
        # Verificar MX records
        try:
            mx_records = dns.resolver.resolve(domain, "MX")
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            # Si no hay MX, intentar A/AAAA records como fallback
            try:
                dns.resolver.resolve(domain, "A")
                return True
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
                return False
                
    except EmailNotValidError:
        return False


async def send_reset_email(email: str, token: str, locked_out: bool = False) -> bool:
    """Envía email de recuperación de contraseña con token y enlace directo al login."""
    from urllib.parse import quote
    login_url = f"http://localhost:3000/?reset_token={quote(token)}&email={quote(email)}"

    if locked_out:
        title = "Tu cuenta ha sido bloqueada - SecureVault Pro"
        intro = (
            "Tu cuenta ha sido <strong>bloqueada temporalmente</strong> por múltiples intentos "
            "fallidos de inicio de sesión. Haz clic en el botón de abajo para restablecer tu "
            "contraseña y recuperar el acceso."
        )
        subject = "Cuenta bloqueada — Restablece tu contraseña · SecureVault Pro"
        header_color = "#dc3545"
        header_text = "Cuenta Bloqueada"
    else:
        title = "Recuperación de Contraseña - SecureVault Pro"
        intro = (
            "Recibimos una solicitud para restablecer la contraseña de tu cuenta. "
            "Haz clic en el botón de abajo para continuar, o copia el token manualmente."
        )
        subject = "Recuperar contraseña - SecureVault Pro"
        header_color = "#4a9eff"
        header_text = "Recuperar Contraseña"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <div style="background-color: {header_color}; color: white; padding: 16px 24px; border-radius: 6px 6px 0 0; margin: -30px -30px 24px -30px;">
                    <h2 style="margin: 0; font-size: 20px;">{header_text} — SecureVault Pro</h2>
                </div>
                <p style="color: #444; font-size: 15px; line-height: 1.7;">
                    {intro}
                </p>
                <div style="margin: 28px 0; text-align: center;">
                    <a href="{login_url}"
                       style="background-color: {header_color}; color: white; padding: 14px 36px;
                       text-decoration: none; border-radius: 6px; font-weight: bold;
                       font-size: 15px; display: inline-block; letter-spacing: 0.3px;">
                        Restablecer mi contraseña
                    </a>
                </div>
                <p style="color: #666; font-size: 13px; margin-top: 8px;">
                    Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                    <a href="{login_url}" style="color: #4a9eff; word-break: break-all;">{login_url}</a>
                </p>
                <div style="margin: 20px 0; padding: 12px 16px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid {header_color};">
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #888;">O ingresa este token manualmente en la pantalla de recuperación:</p>
                    <code style="word-break: break-all; font-size: 13px; color: #333;">{token}</code>
                </div>
                <p style="color: #999; font-size: 12px; margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px;">
                    Este enlace expira en <strong>30 minutos</strong>.<br>
                    Si no solicitaste este correo, ignora este mensaje. Tu contraseña no cambiará.
                </p>
            </div>
        </body>
    </html>
    """
    return await _send_email(
        to_email=email,
        subject=subject,
        html_content=html_content,
        text_content=f"Restablece tu contraseña en: {login_url}\n\nO usa el token: {token}",
    )


async def send_verification_email(email: str, token: str) -> bool:
    """Envía email de verificación con token de confirmación"""
    verification_url = f"http://localhost:3000/verify-email?token={token}&email={email}"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                <h2 style="color: #333; margin-bottom: 20px;">Verificación de Correo - SecureVault Pro</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.6;">
                    ¡Bienvenido a SecureVault Pro! Para completar tu registro,
                    por favor verifica tu correo electrónico haciendo clic en el siguiente botón:
                </p>
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{verification_url}"
                       style="background-color: #4a9eff; color: white; padding: 12px 30px;
                       text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Verificar Correo
                    </a>
                </div>
                <p style="color: #999; font-size: 12px; margin-top: 20px;">
                    Si no puedes hacer clic en el botón, copia y pega este enlace en tu navegador:<br>
                    <span style="word-break: break-all; color: #4a9eff;">{verification_url}</span>
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px;">
                    Este enlace expira en 30 minutos.<br>
                    Si no solicitaste este correo, puedes ignorar este mensaje.
                </p>
            </div>
        </body>
    </html>
    """
    return await _send_email(
        to_email=email,
        subject="Verifica tu correo electrónico - SecureVault Pro",
        html_content=html_content,
        text_content=f"Haz clic aquí para verificar tu correo: {verification_url}",
    )
