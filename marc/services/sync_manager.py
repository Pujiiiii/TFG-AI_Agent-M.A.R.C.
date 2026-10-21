import socket
import os
from datetime import datetime, timedelta
from marc.core.db import (
    db_get_unsynced_events,
    db_mark_event_synced,
    db_get_pending_outbox_emails,
    db_mark_email_sent,
    db_get_sync_summary
)
from marc.services.calendar_service import get_google_calendar_service, is_google_calendar_connected
from marc.services.email_service import is_email_configured, send_email_message

def check_internet_connection(timeout: float = 1.5) -> bool:
    """Comprova si el dispositiu té accés a internet amb un ping ràpid a servidors DNS d'alta disponibilitat."""
    hosts = [("8.8.8.8", 53), ("1.1.1.1", 53)]
    for host, port in hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            return True
        except Exception:
            continue
    return False

def sync_pending_events() -> int:
    """Puja a Google Calendar les cites que s'hagin creat en mode local/fora de línia."""
    if not is_google_calendar_connected():
        return 0

    g_service = get_google_calendar_service()
    if not g_service:
        return 0

    unsynced = db_get_unsynced_events()
    count = 0

    for ev in unsynced:
        try:
            start_str = ev["start_time"].strip()
            dt_inici = datetime.strptime(start_str, "%Y-%m-%d %H:%M") if " " in start_str else datetime.fromisoformat(start_str)
            
            end_str = ev.get("end_time")
            if end_str and " " in end_str:
                dt_fi = datetime.strptime(end_str.strip(), "%Y-%m-%d %H:%M")
            else:
                dt_fi = dt_inici + timedelta(hours=1)

            event_body = {
                'summary': ev["title"],
                'location': ev.get("location") or "",
                'description': ev.get("description") or "",
                'start': {'dateTime': dt_inici.isoformat(), 'timeZone': 'Europe/Madrid'},
                'end': {'dateTime': dt_fi.isoformat(), 'timeZone': 'Europe/Madrid'},
            }
            g_ev = g_service.events().insert(calendarId='primary', body=event_body).execute()
            google_id = g_ev.get('id')
            db_mark_event_synced(ev["id"], google_id)
            count += 1
        except Exception as e:
            print(f"[Sync Manager] Error sincronitzant esdeveniment ID {ev['id']} a Google Calendar: {e}")

    return count

def sync_pending_outbox_emails() -> int:
    """Envia els correus acumulats a la bústia de sortida (outbox) que no es van poder enviar per manca d'internet."""
    if not is_email_configured():
        return 0

    pending = db_get_pending_outbox_emails()
    count = 0

    for em in pending:
        try:
            res = send_email_message(
                recipient=em["recipient"],
                subject=em["subject"],
                body=em["body"]
            )
            if res.get("is_real_smtp"):
                db_mark_email_sent(em["id"])
                count += 1
        except Exception as e:
            print(f"[Sync Manager] Error enviant correu en cua ID {em['id']}: {e}")

    return count

def run_full_synchronization() -> dict:
    """
    Executa la sincronització completa Offline-First:
    1. Comprova si hi ha connexió a internet.
    2. Sincronitza cites locals pendents amb Google Calendar.
    3. Envia els correus pendents de la cua 'outbox'.
    """
    has_internet = check_internet_connection()
    summary_before = db_get_sync_summary()

    if not has_internet:
        return {
            "online": False,
            "status": "offline",
            "synced_events": 0,
            "synced_emails": 0,
            "pending": summary_before,
            "message": "⚠️ Sense connexió a internet. El sistema roman en mode local segur (Offline-First). Totes les dades es mantenen guardades en local a l'espera de connectivitat."
        }

    # Si tenim connexió, pugem els canvis acumulats
    synced_events = sync_pending_events()
    synced_emails = sync_pending_outbox_emails()
    summary_after = db_get_sync_summary()

    detall = []
    if synced_events > 0:
        detall.append(f"{synced_events} cites sincronitzades amb Google Calendar")
    if synced_emails > 0:
        detall.append(f"{synced_emails} correus enviats de la bústia de sortida")

    if not detall:
        if summary_after["total_pending"] == 0:
            msg = "Tot al dia! Totes les dades locals estan completament sincronitzades amb els servidors remots."
        else:
            msg = f"Connexio activa. Hi ha {summary_after['total_pending']} elements locals (configura Google Calendar o Email a .env per a pujar-los)."
    else:
        msg = f"Sincronitzacio completada amb exit: {', '.join(detall)}."

    return {
        "online": True,
        "status": "online",
        "synced_events": synced_events,
        "synced_emails": synced_emails,
        "pending": summary_after,
        "message": msg
    }
