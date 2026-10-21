import os
from datetime import datetime, timedelta
from marc.core.db import db_get_events, db_add_event, db_delete_event

SCOPES = ['https://www.googleapis.com/auth/calendar']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

def get_google_calendar_service():
    """Retorna el client de Google Calendar API si credentials.json o token.json existeixen."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
            except Exception:
                creds = None
        elif os.path.exists(CREDENTIALS_FILE):
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"[Google Calendar] Error durant el flux OAuth: {e}")
                creds = None

    if creds:
        try:
            from googleapiclient.discovery import build
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            print(f"[Google Calendar] Error inicialitzant servei: {e}")
            return None
    return None

def is_google_calendar_connected() -> bool:
    return os.path.exists(TOKEN_FILE) or os.path.exists(CREDENTIALS_FILE)

def fetch_calendar_events(date_prefix: str = None):
    """
    Obté els esdeveniments del calendari.
    Si Google Calendar està connectat, obté els esdeveniments de Google Calendar i els reflecteix a local.
    En cas contrari, retorna els esdeveniments de la base de dades SQLite local.
    """
    g_service = get_google_calendar_service()
    if g_service:
        try:
            now_iso = datetime.utcnow().isoformat() + 'Z'
            events_result = g_service.events().list(
                calendarId='primary', 
                timeMin=now_iso,
                maxResults=20, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            items = events_result.get('items', [])
            
            # Sincronitzem amb la base de dades local si cal
            events_list = []
            for item in items:
                start = item['start'].get('dateTime', item['start'].get('date'))
                end = item['end'].get('dateTime', item['end'].get('date'))
                # Neteja de format ISO a AAAA-MM-DD HH:MM
                clean_start = start.replace("T", " ")[:16]
                clean_end = end.replace("T", " ")[:16] if end else ""
                events_list.append({
                    "id": item.get('id'),
                    "title": item.get('summary', '(Sense títol)'),
                    "description": item.get('description', ''),
                    "start_time": clean_start,
                    "end_time": clean_end,
                    "location": item.get('location', 'Google Calendar')
                })
            return events_list
        except Exception as e:
            print(f"[Google Calendar API] Error consultant esdeveniments: {e}. Utilitzant magatzem local.")

    # Fallback / Mode local SQLite
    return db_get_events(date_prefix=date_prefix)

def add_calendar_event(title: str, start_time: str, end_time: str = None, location: str = "", description: str = ""):
    """Afegeix l'esdeveniment a Google Calendar si està actiu i a SQLite."""
    g_service = get_google_calendar_service()
    google_event_id = None
    if g_service:
        try:
            # Format per a Google API: '2026-10-22T10:00:00Z'
            dt_inici = datetime.strptime(start_time.strip(), "%Y-%m-%d %H:%M")
            if end_time and " " in end_time:
                dt_fi = datetime.strptime(end_time.strip(), "%Y-%m-%d %H:%M")
            else:
                dt_fi = dt_inici + timedelta(hours=1)

            event_body = {
                'summary': title,
                'location': location,
                'description': description,
                'start': {'dateTime': dt_inici.isoformat(), 'timeZone': 'Europe/Madrid'},
                'end': {'dateTime': dt_fi.isoformat(), 'timeZone': 'Europe/Madrid'},
            }
            g_event = g_service.events().insert(calendarId='primary', body=event_body).execute()
            google_event_id = g_event.get('id')
        except Exception as e:
            print(f"[Google Calendar API] Error afegint esdeveniment a Google: {e}")

    # Guardem sempre a SQLite local (amb estat de sincronització)
    synced = 1 if google_event_id else 0
    local_id = db_add_event(
        title=title, 
        start_time=start_time, 
        end_time=end_time, 
        location=location, 
        description=description,
        synced_remote=synced,
        remote_id=google_event_id
    )
    return {
        "local_id": local_id,
        "google_id": google_event_id,
        "is_google_synced": bool(google_event_id)
    }

def delete_calendar_event(event_id):
    """Elimina l'esdeveniment tant de Google Calendar (si és alfanumèric) com de SQLite."""
    g_service = get_google_calendar_service()
    if g_service and isinstance(event_id, str) and not event_id.isdigit():
        try:
            g_service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"[Google Calendar API] Error eliminant esdeveniment a Google: {e}")

    try:
        numeric_id = int(event_id)
        return db_delete_event(numeric_id)
    except (ValueError, TypeError):
        return False
