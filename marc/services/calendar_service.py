import os
from datetime import datetime, timedelta, timezone
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

def get_calendar_label(summary: str, is_primary: bool) -> str:
    """Assigna una etiqueta llegible al calendari segons el seu títol o origen."""
    if is_primary:
        return "[Personal]"
    s_lower = summary.lower()
    if "udg.edu" in s_lower or "horariseps" in s_lower:
        return "[UdG]"
    if "formula 1" in s_lower or "f1" in s_lower:
        return "[F1]"
    if "wec" in s_lower:
        return "[FIA WEC]"
    if "gt world" in s_lower:
        return "[GT World]"
    if "mustang" in s_lower:
        return "[Mustang]"
    if "dtm" in s_lower:
        return "[DTM]"
    if "festiu" in s_lower or "festivo" in s_lower or "holiday" in s_lower:
        return "[Festiu]"
    clean = summary.split("/")[-1].split(".ics")[0]
    return f"[{clean[:12]}]"

def _format_event_time(raw_val: str) -> tuple:
    """
    Retorna (clean_str, sort_key).
    clean_str ex: '2026-10-21 13:30' o '2026-10-25 (Tot el dia)'
    sort_key ex: '2026-10-21 13:30'
    """
    if not raw_val:
        return "", ""
    if "T" in raw_val:
        try:
            dt = datetime.fromisoformat(raw_val.replace("Z", "+00:00"))
            dt_local = dt.astimezone()
            formatted = dt_local.strftime("%Y-%m-%d %H:%M")
            return formatted, formatted
        except Exception:
            clean = raw_val.replace("T", " ")[:16]
            return clean, clean
    else:
        clean = f"{raw_val} (Tot el dia)"
        sort_key = f"{raw_val} 00:00"
        return clean, sort_key

import time

_CALENDAR_CACHE = {
    "data": None,
    "timestamp": 0,
    "date_prefix": None
}

def invalidate_calendar_cache():
    global _CALENDAR_CACHE
    _CALENDAR_CACHE["timestamp"] = 0
    _CALENDAR_CACHE["data"] = None

def fetch_calendar_events(date_prefix: str = None, force_refresh: bool = False):
    """
    Obté els esdeveniments del calendari (tant el personal com els subscrits: UdG, F1, etc.).
    Si Google Calendar està connectat, consulta tots els calendaris de l'usuari i els combina ordenadament.
    Inclou memòria cau d'alta velocitat (TTL 180s) per evitar bloquejar el servidor a cada refresc.
    També inclou els esdeveniments locals de SQLite pendents de sincronització.
    """
    global _CALENDAR_CACHE
    now_ts = time.time()

    # Si tenim cau vàlid i no s'ha forçat un refresc, retornem a l'instant (0ms)
    if not force_refresh and _CALENDAR_CACHE["data"] is not None and (now_ts - _CALENDAR_CACHE["timestamp"] < 180):
        if _CALENDAR_CACHE["date_prefix"] == date_prefix:
            return _CALENDAR_CACHE["data"]

    g_service = get_google_calendar_service()
    if g_service:
        try:
            cal_list = g_service.calendarList().list().execute().get('items', [])
            all_events = []
            seen_events = set()

            if date_prefix:
                try:
                    dt_day = datetime.strptime(date_prefix.strip(), "%Y-%m-%d")
                    t_min = (dt_day - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
                    t_max = (dt_day + timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z")
                except ValueError:
                    t_min = datetime.now(timezone.utc).isoformat()
                    t_max = None
            else:
                t_min = datetime.now(timezone.utc).isoformat()
                t_max = None

            # Detectem si ja tenim el calendari complet de F1 per evitar duplicats
            has_f1_practise = any('formula 1 w/ practise' in (c.get('summary') or '').lower() for c in cal_list)

            for cal in cal_list:
                cid = cal.get('id', '')
                summary = cal.get('summary', '')
                is_primary = cal.get('primary', False)
                s_lower = summary.lower()

                # Excloem completament el calendari de Festius / Holidays de l'agenda
                if (
                    "festiu" in s_lower
                    or "festivo" in s_lower
                    or "holiday" in s_lower
                    or "holiday" in cid.lower()
                    or "#holiday" in cid.lower()
                ):
                    continue

                # Ometem calendari de F1 bàsic redundant si tenim el complet amb entrenaments
                if has_f1_practise and s_lower == 'formula 1' and not is_primary:
                    continue

                tag = get_calendar_label(summary, is_primary)
                if tag == "[Festiu]":
                    continue

                try:
                    query_kwargs = {
                        "calendarId": cid,
                        "timeMin": t_min,
                        "singleEvents": True,
                        "orderBy": "startTime",
                        "maxResults": 15 if not date_prefix else 30
                    }
                    if t_max:
                        query_kwargs["timeMax"] = t_max

                    events_result = g_service.events().list(**query_kwargs).execute()
                    items = events_result.get('items', [])

                    for item in items:
                        title_raw = item.get('summary', '(Sense títol)')
                        start_raw = item['start'].get('dateTime', item['start'].get('date'))
                        end_raw = item.get('end', {}).get('dateTime', item.get('end', {}).get('date', ''))

                        clean_start, sort_start = _format_event_time(start_raw)
                        clean_end, _ = _format_event_time(end_raw)

                        if date_prefix and not clean_start.startswith(date_prefix):
                            continue

                        # Deduplicació per títol i hora d'inici
                        dedup_key = (title_raw.lower().strip(), clean_start)
                        if dedup_key in seen_events:
                            continue
                        if tag == "[F1]" and ("f1_session", clean_start) in seen_events:
                            continue

                        seen_events.add(dedup_key)
                        if tag == "[F1]":
                            seen_events.add(("f1_session", clean_start))

                        display_title = f"{tag} {title_raw}" if tag != "[Personal]" else title_raw

                        all_events.append({
                            "id": item.get('id'),
                            "calendar_id": cid,
                            "tag": tag,
                            "title": display_title,
                            "description": item.get('description', ''),
                            "start_time": clean_start,
                            "end_time": clean_end,
                            "sort_key": sort_start,
                            "location": item.get('location', '')
                        })
                except Exception as cal_err:
                    print(f"[Google Calendar] Error llegint calendari '{summary}': {cal_err}")

            # Afegim també els esdeveniments locals de SQLite no sincronitzats
            local_events = db_get_events(date_prefix=date_prefix)
            for lev in local_events:
                lev_start = lev.get("start_time", "")
                lev_title = lev.get("title", "")
                if (lev_title.lower().strip(), lev_start) not in seen_events:
                    all_events.append({
                        "id": lev.get("id"),
                        "calendar_id": "local",
                        "tag": "[Local]",
                        "title": lev_title,
                        "description": lev.get("description", ""),
                        "start_time": lev_start,
                        "end_time": lev.get("end_time", ""),
                        "sort_key": lev_start,
                        "location": lev.get("location", "Agenda Local")
                    })

            all_events.sort(key=lambda x: x.get("sort_key", ""))

            # Desem a memòria cau
            _CALENDAR_CACHE["data"] = all_events
            _CALENDAR_CACHE["timestamp"] = time.time()
            _CALENDAR_CACHE["date_prefix"] = date_prefix

            return all_events

        except Exception as e:
            print(f"[Google Calendar API] Error consultant calendaris: {e}. Utilitzant magatzem local.")

    # Fallback / Mode local SQLite
    return db_get_events(date_prefix=date_prefix)

def add_calendar_event(title: str, start_time: str, end_time: str = None, location: str = "", description: str = ""):
    """Afegeix l'esdeveniment a Google Calendar (al calendari principal) si està actiu i a SQLite."""
    invalidate_calendar_cache()
    g_service = get_google_calendar_service()
    google_event_id = None
    if g_service:
        try:
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

def delete_calendar_event(event_id, calendar_id: str = "primary"):
    """Elimina l'esdeveniment tant de Google Calendar com de SQLite."""
    invalidate_calendar_cache()
    g_service = get_google_calendar_service()
    if g_service and isinstance(event_id, str) and not event_id.isdigit():
        try:
            g_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"[Google Calendar API] Error eliminant esdeveniment a Google ({calendar_id}): {e}")

    try:
        numeric_id = int(event_id)
        return db_delete_event(numeric_id)
    except (ValueError, TypeError):
        return False
