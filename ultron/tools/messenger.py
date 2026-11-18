import urllib.parse
import webbrowser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from ultron.tools.phone_controller import PhoneController

class Messenger:
    """Unified communication hub for sending messages via Phone (SMS/WhatsApp) and Desktop."""
    def __init__(self, phone_controller: PhoneController, config: Optional[dict] = None):
        self.phone = phone_controller
        self.config = config or {}

    def send_whatsapp(self, recipient_phone: str, message: str, prefer_device: str = "auto") -> Dict[str, Any]:
        """Sends WhatsApp message via connected Android device or desktop browser."""
        clean_phone = recipient_phone.replace("+", "").replace(" ", "").replace("-", "")
        encoded_msg = urllib.parse.quote(message)
        wa_web_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

        # Check if phone is connected and preferred
        phone_status = self.phone.get_phone_status()
        if phone_status.get("connected") and prefer_device != "desktop":
            res = self.phone.send_whatsapp(clean_phone, message)
            if res.get("success"):
                return {
                    "success": True,
                    "channel": "Phone WhatsApp",
                    "device": phone_status.get("model"),
                    "recipient": recipient_phone,
                    "message": f"WhatsApp staged on {phone_status.get('model')} for {recipient_phone}."
                }

        # Fallback to Desktop WhatsApp Web
        webbrowser.open(wa_web_url)
        return {
            "success": True,
            "channel": "Desktop WhatsApp Web",
            "recipient": recipient_phone,
            "message": f"WhatsApp Web opened in desktop browser for {recipient_phone}.",
            "url": wa_web_url
        }

    def send_sms(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        """Dispatches an SMS message through connected Android phone."""
        phone_status = self.phone.get_phone_status()
        if not phone_status.get("connected"):
            return {
                "success": False,
                "error": "No Android device connected to send SMS. Connect phone via USB with USB Debugging enabled."
            }

        return self.phone.send_sms(recipient_phone, message)

    def send_email(self, recipient_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Sends an email using configured SMTP credentials in config.json."""
        smtp_cfg = self.config.get("messaging", {}).get("smtp", {})
        host = smtp_cfg.get("host")
        port = smtp_cfg.get("port", 587)
        user = smtp_cfg.get("user")
        password = smtp_cfg.get("password")

        if not host or not user or not password:
            # Fallback to mailto link in browser
            mailto_url = f"mailto:{recipient_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            webbrowser.open(mailto_url)
            return {
                "success": True,
                "channel": "Desktop Mail Client",
                "message": f"Opened default desktop email composer for {recipient_email}."
            }

        try:
            msg = MIMEMultipart()
            msg["From"] = user
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)

            return {
                "success": True,
                "channel": "Direct SMTP",
                "message": f"Email successfully sent to {recipient_email}."
            }
        except Exception as e:
            return {"success": False, "error": f"SMTP transmission failed: {str(e)}"}
