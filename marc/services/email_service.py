import os
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from marc.core.db import db_get_emails, db_add_email

def is_email_configured() -> bool:
    user = os.getenv("EMAIL_USER") or os.getenv("SMTP_USER")
    pwd = os.getenv("EMAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")
    return bool(user and pwd)

def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    result = []
    for fragment, charset in decoded_fragments:
        if isinstance(fragment, bytes):
            try:
                result.append(fragment.decode(charset or "utf-8", errors="replace"))
            except Exception:
                result.append(fragment.decode("latin-1", errors="replace"))
        else:
            result.append(str(fragment))
    return "".join(result)

def fetch_unread_emails(limit: int = 5):
    """
    Llegeix els correus no llegits de la bústia real via IMAP si està configurat.
    En cas contrari, retorna els correus de la base de dades local.
    """
    user = os.getenv("EMAIL_USER") or os.getenv("SMTP_USER")
    password = os.getenv("EMAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")
    imap_host = os.getenv("IMAP_HOST", "imap.gmail.com")

    if user and password:
        try:
            mail = imaplib.IMAP4_SSL(imap_host, 993, timeout=10)
            mail.login(user, password)
            mail.select("INBOX")

            status, messages = mail.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                mail.logout()
                return []

            email_ids = messages[0].split()
            # Agafem els últims no llegits
            email_ids = email_ids[-limit:]

            result_emails = []
            for e_id in reversed(email_ids):
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                if res != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_mime_header(msg.get("Subject", "(Sense assumpte)"))
                        sender = decode_mime_header(msg.get("From", "Desconegut"))
                        date_str = msg.get("Date", "")

                        # Extracció de cos de text
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                ctype = part.get_content_type()
                                cdisp = str(part.get("Content-Disposition"))
                                if ctype == "text/plain" and "attachment" not in cdisp:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                                        break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

                        # Reflectim a la base de dades local per a l'historial
                        db_add_email(
                            sender=sender,
                            recipient=user,
                            subject=subject,
                            body=body[:2000],
                            folder="inbox",
                            is_read=0
                        )

                        result_emails.append({
                            "sender": sender,
                            "subject": subject,
                            "date": date_str,
                            "body": body[:500]
                        })

            mail.logout()
            if result_emails:
                try:
                    from marc.services.workflow_engine import run_workflow_cycle
                    run_workflow_cycle()
                except Exception:
                    pass
            return result_emails
        except Exception as e:
            print(f"[Email Hub IMAP] Error connectant a {imap_host}: {e}. Utilitzant bústia local.")

    # Fallback a SQLite local
    return db_get_emails(folder="inbox", limit=limit, unread_only=True)

def send_email_message(recipient: str, subject: str, body: str):
    """
    Envia el correu via SMTP real si hi ha credencials a .env, i el desa a 'sent' a SQLite.
    """
    user = os.getenv("EMAIL_USER") or os.getenv("SMTP_USER")
    password = os.getenv("EMAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    enviat_real = False
    detall = ""

    if user and password:
        try:
            msg = MIMEMultipart()
            msg["From"] = user
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)

            enviat_real = True
            detall = f" (Enviat correctament via servidor SMTP: {smtp_host})"
        except Exception as e:
            detall = f" (Avís: Error d'enviament SMTP: {e}. S'ha registrat a la bústia de sortida local)"

    # Si s'ha pogut enviar per SMTP, es marca com a 'sent' (synced=1)
    # Si no hi havia internet o ha fallat, es desa a la cua 'outbox' (synced=0) per sincronitzar en reconnectar
    folder_desti = "sent" if enviat_real else "outbox"
    synced = 1 if enviat_real else 0

    db_add_email(
        sender=user or "usuari@marc-assistant.cat",
        recipient=recipient,
        subject=subject,
        body=body,
        folder=folder_desti,
        is_read=1,
        synced_remote=synced
    )

    if not enviat_real:
        estat_text = "📦 Correu desat a la bústia de sortida (cua local Outbox). Es tramitarà automàticament en restablir-se la connexió."
    else:
        estat_text = f"✉️ Correu enviat correctament a {recipient}{detall}."

    return {
        "success": True,
        "is_real_smtp": enviat_real,
        "folder": folder_desti,
        "message": estat_text
    }
