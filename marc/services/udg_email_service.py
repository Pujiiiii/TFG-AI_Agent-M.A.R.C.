import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from marc.core.db import (
    db_get_unanalyzed_udg_emails,
    db_mark_email_analyzed,
    db_add_task,
    db_add_notification,
    db_add_email,
    get_db_connection
)
from marc.services.calendar_service import add_calendar_event
from marc.services.email_service import is_email_configured, decode_mime_header

load_dotenv()

UDG_DOMAINS = ["udg.edu", "eps.udg.edu", "alumnes.udg.edu", "moodle.udg.edu"]

def is_udg_sender_or_subject(sender: str, subject: str, body: str = "") -> bool:
    """Detecta si un correu prové de la UdG, professors, Moodle o entorns acadèmics relacionats."""
    s_low = (sender or "").lower()
    sub_low = (subject or "").lower()
    b_low = (body or "").lower()

    for dom in UDG_DOMAINS:
        if dom in s_low or dom in b_low:
            return True

    keywords = ["udg", "moodle", "campus virtual", "eps", "grau", "tfg", "universitat de girona"]
    for kw in keywords:
        if kw in s_low or kw in sub_low:
            return True

    return False

def sync_imap_udg_emails():
    """Si hi ha credencials IMAP reals, cerca correus nous no llegits de la UdG i els insereix a la base de dades."""
    if not is_email_configured():
        return 0

    import imaplib
    import email

    user = os.getenv("EMAIL_USER") or os.getenv("SMTP_USER")
    password = os.getenv("EMAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")
    imap_host = os.getenv("IMAP_HOST", "imap.gmail.com")

    nous_trobats = 0
    try:
        mail = imaplib.IMAP4_SSL(imap_host, 993, timeout=10)
        mail.login(user, password)
        mail.select("INBOX")

        status, messages = mail.search(None, "UNSEEN")
        if status == "OK" and messages[0]:
            email_ids = messages[0].split()
            for e_id in reversed(email_ids[-15:]):
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                if res != "OK":
                    continue
                for part in msg_data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        sender = decode_mime_header(msg.get("From", ""))
                        subject = decode_mime_header(msg.get("Subject", ""))
                        body = ""
                        if msg.is_multipart():
                            for p in msg.walk():
                                if p.get_content_type() == "text/plain":
                                    payload = p.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(p.get_content_charset() or "utf-8", errors="replace")
                                        break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

                        if is_udg_sender_or_subject(sender, subject, body):
                            # Comprovem si ja és a SQLite
                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute("SELECT id FROM emails WHERE sender = ? AND subject = ?", (sender.strip(), subject.strip()))
                            exists = c.fetchone()
                            conn.close()

                            if not exists:
                                db_add_email(
                                    sender=sender,
                                    recipient=user,
                                    subject=subject,
                                    body=body[:3000],
                                    folder="inbox",
                                    is_read=0,
                                    synced_remote=1
                                )
                                nous_trobats += 1
        mail.logout()
    except Exception as e:
        print(f"[UDG Email Service] Error sincronitzant IMAP: {e}")

    return nous_trobats

def extract_json_from_llm_response(text: str) -> dict:
    """Neteja i extreu l'objecte JSON de la resposta del model."""
    try:
        clean = text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        return json.loads(clean)
    except Exception:
        # Intent d'extracció per expressió regular
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return {}

def analyze_single_udg_email(em: dict, llm: ChatGroq = None) -> dict:
    """
    Analitza un correu de la UdG amb LLM, dedueix tasques, terminis de lliurament o exàmens
    i executa les accions pertinents a la base de dades i al calendari.
    """
    if llm is None:
        llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.1)

    ara_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = f"""Ets en M.A.R.C., el secretari executiu i assistent d'en Marc a la universitat (UdG - EPS).
La teva missió és analitzar aquest correu acadèmic oficial rebut i determinar quines accions cal emprendre.

DADES DEL CORREU:
- Remitent: {em.get('sender')}
- Assumpte: {em.get('subject')}
- Data d'avui de referència: {ara_str}
- Contingut del correu:
\"\"\"{em.get('body', '')}\"\"\"

INSTRUCCIONS DE DECISIÓ:
1. Determina l'assignatura o matèria (ex: 'SGBD', 'Habilitats Directives', 'Gestió de Producció', 'TFG').
2. Determina si demana un lliurament de treball/pràctica, si anuncia una data d'examen/presentació o és merament informatiu.
3. Si hi ha feina a fer o un termini, marca 'requires_action': true.
4. Extreu la data límit ('due_date') en format 'YYYY-MM-DD' (any 2026). Si diu una hora límit, posa-la a 'due_time' en format 'HH:MM' (ex: '23:59' o '14:30').
5. Defineix una prioritat: 'alta' (si és un examen, defensa o lliurament a curt termini), 'mitjana' o 'baixa'.
6. Si hi ha una data límit o data d'examen concreta, marca 'create_calendar_event': true per posar-ho a l'agenda de Google Calendar i local.

Respon EXCLUSIVAMENT amb un únic objecte JSON vàlid amb aquestes claus exactes:
{{
  "subject_name": "Nom de l'assignatura",
  "email_type": "lliurament_treball | examen | presentacio | tutoria | informatiu",
  "requires_action": true,
  "task_title": "Títol breu i clar de la tasca per a la llista de to-dos",
  "task_description": "Explicació detallada de què demana el professor i requisits",
  "due_date": "YYYY-MM-DD",
  "due_time": "HH:MM",
  "priority": "alta | mitjana | baixa",
  "create_calendar_event": true,
  "calendar_event_title": "Termini: Títol de la tasca o examen",
  "calendar_location": "Campus Virtual UdG / EPS Aula ...",
  "summary": "Resum executiu d'1 frase de l'acció presa"
}}
"""

    try:
        response = llm.invoke(prompt)
        data = extract_json_from_llm_response(response.content)
    except Exception as e:
        print(f"[UDG Analyzer Error]: {e}")
        data = {}

    if not data:
        # Fallback heurístic bàsic si el model no respon JSON vàlid
        data = {
            "subject_name": "UdG / Acadèmic",
            "email_type": "informatiu",
            "requires_action": True,
            "task_title": f"Revisar correu: {em.get('subject')[:40]}",
            "task_description": em.get('body', '')[:150],
            "due_date": "",
            "due_time": "",
            "priority": "mitjana",
            "create_calendar_event": False,
            "summary": f"Correu de {em.get('sender')} analitzat."
        }

    email_id = em["id"]
    actions_taken = []
    created_task_id = None
    created_event_id = None

    # 1. Creació automàtica de la Tasca
    if data.get("requires_action") and data.get("task_title"):
        task_title = data["task_title"].strip()
        prio = data.get("priority", "mitjana").lower()
        due_date = data.get("due_date", "").strip() or None
        desc = data.get("task_description", "").strip()
        if data.get("subject_name"):
            desc = f"[{data['subject_name']}] {desc}"

        created_task_id = db_add_task(
            title=task_title,
            priority=prio,
            due_date=due_date,
            description=desc
        )
        actions_taken.append(f"📋 Nova tasca afegida: '{task_title}' (Prioritat: {prio.upper()})")

    # 2. Creació automàtica de l'Esdeveniment / Recordatori al Calendari
    if data.get("create_calendar_event") and data.get("due_date"):
        due_d = data["due_date"].strip()
        due_t = data.get("due_time", "23:59").strip() if data.get("due_time") else "23:59"
        start_time_str = f"{due_d} {due_t}"
        event_title = data.get("calendar_event_title") or f"Termini: {data.get('task_title', 'Lliurament UdG')}"
        loc = data.get("calendar_location") or "Campus Virtual UdG"
        ev_desc = data.get("summary") or data.get("task_description", "")

        cal_res = add_calendar_event(
            title=event_title,
            start_time=start_time_str,
            location=loc,
            description=ev_desc
        )
        created_event_id = cal_res.get("local_id")
        sync_txt = " [Google Calendar]" if cal_res.get("is_google_synced") else " [Agenda Local]"
        actions_taken.append(f"📅 Recordatori de termini programat: '{event_title}' el {start_time_str}{sync_txt}")

    # 3. Notificació interna
    resum_final = data.get("summary") or f"Processat correu de {em.get('sender')} ({data.get('subject_name', 'UdG')})"
    db_add_notification(
        recipient="Marc (Assistent)",
        channel="udg_hub",
        message=f"🎓 {resum_final} | Accions: {len(actions_taken)} creades."
    )

    # 4. Marcar correu com a analitzat
    db_mark_email_analyzed(email_id, resum_final)

    return {
        "email_id": email_id,
        "sender": em.get("sender"),
        "subject": em.get("subject"),
        "analysis": data,
        "task_id": created_task_id,
        "event_id": created_event_id,
        "actions_taken": actions_taken,
        "summary": resum_final
    }

def process_all_pending_udg_emails() -> dict:
    """
    Executa l'anàlisi intel·ligent completa de tots els correus no analitzats de la UdG.
    1. Comprova si hi ha nous correus a IMAP.
    2. Obté els correus pendents de la base de dades local.
    3. Analitza cadascun amb IA i executa les tasques i cites necessàries.
    """
    # 1. Comprovació d'IMAP en viu si està disponible
    nous_imap = sync_imap_udg_emails()

    # 2. Correus pendents a la base de dades
    pendents = db_get_unanalyzed_udg_emails()

    if not pendents:
        return {
            "processed_count": 0,
            "new_imap_count": nous_imap,
            "results": [],
            "message": "🎓 No hi ha cap correu nou pendent d'analitzar de la Universitat de Girona (UdG) o Moodle. Tot al dia!"
        }

    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.1)
    results = []
    total_tasks = 0
    total_events = 0

    for em in pendents:
        res = analyze_single_udg_email(em, llm=llm)
        if res.get("task_id"):
            total_tasks += 1
        if res.get("event_id"):
            total_events += 1
        results.append(res)

    resum_linies = [
        f"🎓 **S'han analitzat amb èxit {len(results)} correus de la UdG / Moodle:**"
    ]
    for r in results:
        resum_linies.append(f"- **De:** `{r['sender']}` | **Assumpte:** '{r['subject']}'")
        for acc in r["actions_taken"]:
            resum_linies.append(f"  • {acc}")

    resum_linies.append(f"\n📊 **Total generat:** {total_tasks} tasques afegides a To-Do, {total_events} cites/terminis a l'agenda.")

    return {
        "processed_count": len(results),
        "new_imap_count": nous_imap,
        "total_tasks": total_tasks,
        "total_events": total_events,
        "results": results,
        "message": "\n".join(resum_linies)
    }
