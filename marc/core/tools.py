import os
import json
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from marc.core.actions import registrar_accio
from marc.core.db import (
    db_add_task,
    db_get_tasks,
    db_toggle_task,
    db_delete_task,
    db_add_notification,
    db_get_notifications,
    get_db_connection
)
from marc.services.calendar_service import (
    fetch_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    is_google_calendar_connected,
    detect_calendar_conflicts,
    suggest_free_slots
)
from marc.services.weather_service import get_girona_weather
from marc.services.document_service import analyze_document_with_ai, list_stored_documents
from marc.services.email_service import (
    fetch_unread_emails,
    send_email_message,
    is_email_configured
)
from marc.services.spotify_service import (
    play_music,
    control_playback,
    is_spotify_api_configured
)

# ==============================================================================
# 1. GESTIÓ DE TASQUES I PLANIFICACIÓ DE FEINA
# ==============================================================================

@tool
def llistar_tasques(estat: str = "totes") -> str:
    """
    Llista les tasques de feina pendents o completades.
    Paràmetres:
      - estat: 'pendent', 'completada' o 'totes' (per defecte 'totes').
    """
    filtre = None if estat == "totes" else estat
    tasques = db_get_tasks(status=filtre)
    if not tasques:
        return f"No hi ha tasques registrades amb l'estat '{estat}'."

    linies = ["### 📋 Llistat de Tasques:"]
    for t in tasques:
        icona_estat = "✅" if t["status"] == "completada" else "⏳"
        prio = t["priority"].upper()
        data_lim = f" (Data límit: {t['due_date']})" if t["due_date"] else ""
        desc = f" - *{t['description']}*" if t["description"] else ""
        linies.append(f"- **[ID: {t['id']}]** {icona_estat} [{prio}] **{t['title']}**{data_lim}{desc}")

    return "\n".join(linies)

@tool
def afegir_tasca(titol: str, prioritat: str = "mitjana", data_limit: str = "", descripcio: str = ""):
    """
    Afegeix una nova tasca a la llista de feina.
    Paràmetres:
      - titol: Títol o acció de la tasca (obligatori).
      - prioritat: 'alta', 'mitjana' o 'baixa' (per defecte 'mitjana').
      - data_limit: Data límit en format AAAA-MM-DD (opcional).
      - descripcio: Detalls addicionals sobre la tasca (opcional).
    """
    task_id = db_add_task(title=titol, priority=prioritat, due_date=data_limit, description=descripcio)
    return f"✅ Tasca afegida correctament [ID: {task_id}]: '{titol}' (Prioritat: {prioritat.upper()})."

@tool
def canviar_estat_tasca(tasca_id: int) -> str:
    """
    Canvia l'estat d'una tasca entre 'pendent' i 'completada'.
    Paràmetres:
      - tasca_id: L'identificador numèric de la tasca.
    """
    nou_estat = db_toggle_task(tasca_id)
    if nou_estat is None:
        return f"⚠️ No s'ha trobat cap tasca amb l'identificador ID: {tasca_id}."
    simbol = "✅" if nou_estat == "completada" else "⏳"
    return f"{simbol} La tasca [ID: {tasca_id}] ara està marcada com a **{nou_estat.upper()}**."

@tool
def eliminar_tasca(tasca_id: int) -> str:
    """
    Elimina una tasca definitivament.
    Paràmetres:
      - tasca_id: L'identificador numèric de la tasca.
    """
    if db_delete_task(tasca_id):
        return f"🗑️ S'ha eliminat la tasca [ID: {tasca_id}] correctament."
    return f"⚠️ No s'ha trobat cap tasca amb ID: {tasca_id}."


# ==============================================================================
# 2. GESTIÓ D'AGENDA I GOOGLE CALENDAR
# ==============================================================================

@tool
def consultar_agenda(data: str = "") -> str:
    """
    Consulta els esdeveniments, reunions i cites del calendari (Google Calendar i local).
    Paràmetres:
      - data: Data a consultar en format 'AAAA-MM-DD' (si es deixa buit, mostra les cites properes).
    """
    dia_consulta = data.strip() if data.strip() else None
    esdeveniments = fetch_calendar_events(date_prefix=dia_consulta)

    font_text = "Google Calendar" if is_google_calendar_connected() else "Calendari Local"

    if not esdeveniments:
        dia_txt = f"per al dia **{dia_consulta}**" if dia_consulta else "pròximes"
        return f"📅 No hi ha cap esdeveniment programat {dia_txt} ({font_text})."

    titol_txt = f"Agenda per al dia {dia_consulta}" if dia_consulta else "Pròximes cites a l'agenda"
    linies = [f"### 📅 {titol_txt} ({font_text}):"]
    for ev in esdeveniments:
        hora_fi = f" fins a {ev['end_time'].split(' ')[1]}" if ev.get("end_time") and " " in ev["end_time"] else ""
        data_hora = ev['start_time']
        lloc = f" 📍 *{ev['location']}*" if ev.get("location") else ""
        desc = f" ({ev['description']})" if ev.get("description") else ""
        linies.append(f"- **[ID: {ev['id']}]** 🕒 **{data_hora}{hora_fi}** — **{ev['title']}**{lloc}{desc}")

    return "\n".join(linies)

@tool
def programar_esdeveniment(titol: str, data_hora_inici: str, durada_minuts: int = 60, lloc: str = "", descripcio: str = "") -> str:
    """
    Proposa afegir una nova reunió o esdeveniment a l'agenda (Google Calendar i local).
    Aquesta acció SEMPRE requereix la confirmació de l'usuari (Human-in-the-Loop) abans d'afegir-se.
    Paràmetres:
      - titol: Títol o motiu de la reunió.
      - data_hora_inici: Data i hora d'inici en format 'AAAA-MM-DD HH:MM'.
      - durada_minuts: Durada en minuts (per defecte 60).
      - lloc: Lloc físic o enllaç de reunió (opcional).
      - descripcio: Detalls o ordre del dia (opcional).
    """
    try:
        dt_inici = datetime.strptime(data_hora_inici.strip(), "%Y-%m-%d %H:%M")
        dt_fi = dt_inici + timedelta(minutes=durada_minuts)
        data_hora_fi = dt_fi.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        data_hora_fi = f"{data_hora_inici} (+{durada_minuts} min)"

    # Detecció proactiva de conflictes d'agenda
    conflictes = detect_calendar_conflicts(data_hora_inici, data_hora_fi)
    avis_solapament = ""
    if conflictes:
        detalls_conflicte = ", ".join([f"'{c['title']}' ({c['start_time']})" for c in conflictes])
        slots_lliures = suggest_free_slots(data_hora_inici[:10], duration_minutes=durada_minuts)
        suggeriments_str = ""
        if slots_lliures:
            suggeriments_str = " | Franges lliures recomanades per avui: " + ", ".join([s["label"] for s in slots_lliures[:3]])
        avis_solapament = f"\n⚠️ **ATENCIÓ DE CONFLICTE D'AGENDA:** Coincideix amb {detalls_conflicte}.{suggeriments_str}"

    def aplicar_esdeveniment(dades):
        res = add_calendar_event(
            title=dades["titol"],
            start_time=dades["data_inici"],
            end_time=dades["data_fi"],
            location=dades.get("lloc", ""),
            description=dades.get("descripcio", "")
        )
        sincro = " [Sincronitzat amb Google Calendar]" if res.get("is_google_synced") else " [Desat a l'agenda local]"
        return f"📅 Reunió programada correctament: '{dades['titol']}' el {dades['data_inici']}{sincro}."

    accio = registrar_accio(
        tipus="calendar",
        resum=f"Programar reunió: '{titol}' el {data_hora_inici}" + (" (amb conflicte detectat)" if conflictes else ""),
        dades={
            "titol": titol,
            "data_inici": data_hora_inici,
            "data_fi": data_hora_fi,
            "durada": f"{durada_minuts} minuts",
            "lloc": lloc if lloc else "No especificat",
            "descripcio": descripcio if descripcio else "Cap descripció",
            "conflicts": [c["title"] for c in conflictes]
        },
        funcio_execucio=aplicar_esdeveniment
    )

    return f"[ACCIÓ PENDENT - ID: {accio['action_id']}] S'ha preparat la programació de l'esdeveniment '{titol}' per al {data_hora_inici}.{avis_solapament}\nRevisa i confirma des de la interfície."

@tool
def suggerir_forats_lliures(data: str = None, durada_minuts: int = 60) -> str:
    """
    Troba i suggereix franges horàries lliures a l'agenda (Google Calendar i local) per a una data específica.
    Ideal per negociar o planificar reunions sense solapaments amb classes de la UdG, F1 o cites personals.
    Paràmetres:
      - data: Data a consultar en format 'AAAA-MM-DD' (si no s'indica, s'utilitza avui).
      - durada_minuts: Durada desitjada de la reunió o bloc de treball (per defecte 60 minuts).
    """
    if not data:
        data = datetime.now().strftime("%Y-%m-%d")
    slots = suggest_free_slots(target_date=data, duration_minutes=durada_minuts)
    if not slots:
        return f"📅 No s'han trobat franges lliures de {durada_minuts} minuts per al dia {data} (dins l'horari de 09:00 a 20:00). La jornada està plena."
    
    linies = [f"### 🕒 Franges lliures disponibles per al dia {data} ({durada_minuts} min):"]
    for s in slots:
        linies.append(f"- Franja lliure: **{s['label']}** (`{s['start']}` fins a `{s['end']}`)")
    return "\n".join(linies)

@tool
def cancel_lar_esdeveniment(esdeveniment_id: str) -> str:
    """
    Proposa cancel·lar o eliminar una reunió existent del calendari (Google Calendar i local).
    Requereix confirmació de l'usuari (Human-in-the-Loop).
    Paràmetres:
      - esdeveniment_id: Identificador de l'esdeveniment a cancel·lar.
    """
    def aplicar_cancel_lacio(dades):
        if delete_calendar_event(dades["esdeveniment_id"]):
            return f"🗑️ L'esdeveniment [ID: {dades['esdeveniment_id']}] ha estat cancel·lat i eliminat de l'agenda."
        return f"⚠️ No s'ha trobat cap esdeveniment amb ID: {dades['esdeveniment_id']}."

    accio = registrar_accio(
        tipus="calendar_delete",
        resum=f"Cancel·lar esdeveniment de l'agenda [ID: {esdeveniment_id}]",
        dades={"esdeveniment_id": esdeveniment_id},
        funcio_execucio=aplicar_cancel_lacio
    )

    return f"[ACCIÓ PENDENT - ID: {accio['action_id']}] S'ha sol·licitat cancel·lar l'esdeveniment ID: {esdeveniment_id}. Esperant confirmació."


# ==============================================================================
# 3. GESTIÓ DE CORREUS ELECTRÒNICS (IMAP / SMTP / LOCAL)
# ==============================================================================

@tool
def consultar_correus_recents(limit: int = 5) -> str:
    """
    Consulta els correus recents o no llegits de la bústia (connexió real IMAP si està configurat).
    Paràmetres:
      - limit: Nombre màxim de correus a consultar (per defecte 5).
    """
    correus = fetch_unread_emails(limit=limit)
    estat_compte = "Bústia IMAP en viu" if is_email_configured() else "Bústia Local"

    if not correus:
        return f"📬 No hi ha cap correu nou o no llegit ({estat_compte}). Tot al dia!"

    linies = [f"### 📬 Correus recents ({estat_compte}):"]
    for c in correus:
        cid = c.get("id", "-")
        remitent = c.get("sender", "Desconegut")
        assumpte = c.get("subject", "(Sense assumpte)")
        data = c.get("received_at", c.get("date", ""))[:16]
        linies.append(f"- **[ID: {cid}]** ✉️ **De:** {remitent} | **Assumpte:** '{assumpte}' ({data})")

    return "\n".join(linies)

@tool
def preparar_i_enviar_correu(destinatari: str, assumpte: str, cos_missatge: str) -> str:
    """
    Redacta un correu electrònic i en proposa l'enviament (enviament real via SMTP si està configurat).
    Aquesta acció SEMPRE requereix supervisió humana (Human-in-the-Loop) abans de ser tramitada.
    Paràmetres:
      - destinatari: Adreça de correu de destinació.
      - assumpte: Títol o assumpte del correu.
      - cos_missatge: Contingut complet del missatge.
    """
    def aplicar_enviament(dades):
        res = send_email_message(
            recipient=dades["destinatari"],
            subject=dades["assumpte"],
            body=dades["cos"]
        )
        
        # Detecció intel·ligent si el correu espera resposta o proposa una reunió/cita
        text_combinat = f"{dades['assumpte']} {dades['cos']}".lower()
        paraules_clau_flux = ["?", "reunió", "reunio", "quedem", "quedar", "et va bé", "et va be", "confirmar", "proposta", "trobada", "disponibilitat", "tutor", "hora", "demà", "dilluns", "dimarts", "dimecres", "dijous", "divendres", "oli", "cotxe"]
        crea_flux = any(kw in text_combinat for kw in paraules_clau_flux)
        
        wf_msg = ""
        if crea_flux:
            from marc.core.db import db_create_workflow, db_add_workflow_log
            clean_sub = dades["assumpte"].replace("Re:", "").replace("Fwd:", "").strip()
            wf_id = db_create_workflow(
                title=f"Esperant resposta: {dades['assumpte']}",
                workflow_type="meeting_negotiation",
                trigger_type="email_reply",
                trigger_condition={"sender": dades["destinatari"], "subject_contains": clean_sub[:25]},
                action_type="schedule_event",
                action_config={"event_title": dades["assumpte"], "duration_minutes": 60, "location": "Per acordar"},
                context_data={"destinatari": dades["destinatari"], "cos_proposta": dades["cos"]}
            )
            db_add_workflow_log(wf_id, "workflow_created", f"Flux #{wf_id} creat automàticament en enviar correu a {dades['destinatari']}")
            wf_msg = f" 🤖 S'ha activat el flux asíncron #{wf_id} per monitorar la resposta a la pestanya 'FLUXOS'."

        return res["message"] + wf_msg

    accio = registrar_accio(
        tipus="email",
        resum=f"Enviar correu a {destinatari}: '{assumpte}'",
        dades={
            "destinatari": destinatari,
            "assumpte": assumpte,
            "cos": cos_missatge
        },
        funcio_execucio=aplicar_enviament
    )

    return f"[ACCIÓ PENDENT - ID: {accio['action_id']}] S'ha preparat el correu per a '{destinatari}'. Revisa el contingut i aprova l'enviament des del modal."

@tool
def analitzar_correus_udg() -> str:
    """
    Analitza de manera autònoma els correus rebuts de la Universitat de Girona (UdG, EPS, Moodle o professors).
    Detecta terminis de lliurament de treballs/pràctiques, dates d'examen, tutories o convocatòries oficials.
    Crea automàticament les tasques pertinents a la llista de feina (to-dos) i programa els recordatoris de termini a l'agenda (Google Calendar i local).
    """
    from marc.services.udg_email_service import process_all_pending_udg_emails
    res = process_all_pending_udg_emails()
    return res["message"]


# ==============================================================================
# 4. SPOTIFY (MÚSICA I REPRODUCCIÓ)
# ==============================================================================

@tool
def reproduir_musica_spotify(cerca: str, tipus: str = "track") -> str:
    """
    Cerca i posa en marxa música a Spotify (cançó, artista, àlbum o playlist).
    Funciona directament obrint l'aplicació d'escriptori Spotify a Windows o via Spotify Web API.
    Paràmetres:
      - cerca: Nom de la cançó, artista o àlbum (ex: 'Bohemian Rhapsody', 'Coldplay', 'Lofi beats').
      - tipus: 'track' (cançó), 'artist' (artista), 'album' (àlbum) o 'playlist'.
    """
    res = play_music(query=cerca, music_type=tipus)
    return res["message"]

@tool
def controlar_reproduccio_spotify(comanda: str) -> str:
    """
    Controla la reproducció de música a Spotify.
    Paràmetres:
      - comanda: 'pausa', 'reprendre', 'següent' o 'anterior'.
    """
    res = control_playback(command=comanda)
    return res["message"]


# ==============================================================================
# 5. MISSATGERIA I NOTIFICACIONS (TELEGRAM / ALERTES)
# ==============================================================================

@tool
def enviar_notificacio_o_missatge(destinatari: str, missatge: str, canal: str = "telegram") -> str:
    """
    Proposa enviar un missatge o notificació immediata a un destinatari o canal (ex: Telegram, SMS).
    Aquesta acció SEMPRE requereix aprovació de l'usuari (Human-in-the-Loop).
    Paràmetres:
      - destinatari: Nom de la persona, identificador de xat o número.
      - missatge: Text del missatge a enviar.
      - canal: 'telegram', 'sms' o 'notificacio' (per defecte 'telegram').
    """
    def aplicar_missatge(dades):
        detall_env = ""
        if dades["canal"].lower() == "telegram":
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID") or dades["destinatari"]
            if bot_token and chat_id:
                try:
                    tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    res = requests.post(tg_url, json={"chat_id": chat_id, "text": dades["missatge"]}, timeout=10)
                    if res.status_code == 200:
                        detall_env = " (Missatge entregat al Bot de Telegram)"
                    else:
                        detall_env = f" (Error resposta Telegram: {res.status_code})"
                except Exception as e:
                    detall_env = f" (Error connexió Telegram: {e})"
            else:
                detall_env = " (Canal Telegram simulat en local; configura TELEGRAM_BOT_TOKEN per a enviament real)"

        db_add_notification(recipient=dades["destinatari"], channel=dades["canal"], message=dades["missatge"])
        return f"💬 Notificació enviada a **{dades['destinatari']}** via {dades['canal'].upper()}{detall_env}."

    accio = registrar_accio(
        tipus="message",
        resum=f"Enviar missatge a {destinatari} via {canal.upper()}",
        dades={
            "destinatari": destinatari,
            "canal": canal,
            "missatge": missatge
        },
        funcio_execucio=aplicar_missatge
    )

    return f"[ACCIÓ PENDENT - ID: {accio['action_id']}] S'ha preparat el missatge per a '{destinatari}' via {canal.upper()}. Esperant aprovació."


# ==============================================================================
# 6. BRIEFING EXECUTIU DIARI (DAILY BRIEFING)
# ==============================================================================

@tool
def consultar_temps_girona(data: str = None) -> str:
    """
    Consulta la meteorologia en viu i la previsió per a Girona (Campus Montilivi / EPS) via Open-Meteo.
    Informa sobre temperatura, pluja, sensació tèrmica i recomanacions (paraigua, etc.).
    Paràmetres:
      - data: Data en format 'AAAA-MM-DD' (per defecte avui).
    """
    w = get_girona_weather(data)
    if not w.get("success"):
        return f"🌦️ {w.get('summary')}"
    return (
        f"### 🌦️ Temps a Girona ({w['location']}):\n"
        f"- **Estat actual:** {w['condition']}\n"
        f"- **Temperatura:** {w['temperature']}°C (Sensació: {w['apparent_temperature']}°C)\n"
        f"- **Previsió avui:** Mínima {w['temp_min']}°C / Màxima {w['temp_max']}°C\n"
        f"- **Probabilitat de pluja:** {w['rain_probability']}%\n"
        f"- **Recomanació:** {w['recommendation']}"
    )

@tool
def activar_mode_focus(minuts: int = 50, tema: str = "Treball profund / Estudi", posar_musica: bool = True) -> str:
    """
    Activa una sessió de concentració i estudi profund (Focus Pomodoro):
    - Bloqueja l'espai de temps a l'agenda com a [Focus].
    - Inicia música instrumental/Lo-Fi a Spotify per afavorir la concentració.
    - Notifica l'inici i prepara el cronòmetre de la sessió.
    Paràmetres:
      - minuts: Durada de la sessió en minuts (per defecte 50).
      - tema: Tema o assignatura de la sessió (ex: 'SGBD - Pràctica 2', 'Memòria TFG').
      - posar_musica: Si és True, activa música relaxant/lo-fi a Spotify.
    """
    ara = datetime.now()
    fi = ara + timedelta(minutes=minuts)
    ara_str = ara.strftime("%Y-%m-%d %H:%M")
    fi_str = fi.strftime("%Y-%m-%d %H:%M")

    # 1. Registrar a l'agenda
    add_calendar_event(
        title=f"🎯 [Focus] {tema}",
        start_time=ara_str,
        end_time=fi_str,
        location="Zona d'estudi / Concentració",
        description=f"Sessió de treball profund de {minuts} minuts gestionada per M.A.R.C."
    )

    # 2. Spotify
    musica_info = ""
    if posar_musica:
        try:
            m_res = play_music(query="lofi hip hop study", music_type="playlist")
            musica_info = f" i s'ha engegat Spotify ({m_res.get('message', 'Lo-Fi Study')})"
        except Exception:
            musica_info = " (Spotify no disponible)"

    # 3. Notificació interna
    db_add_notification(
        recipient="Marc",
        channel="focus",
        message=f"🎯 Sessió de focus de {minuts} minuts activada: '{tema}' (fins a les {fi.strftime('%H:%M')})"
    )

    return (
        f"🎯 **Mode Focus Activat!**\n"
        f"- **Objectiu:** {tema}\n"
        f"- **Durada:** {minuts} minuts (de {ara.strftime('%H:%M')} a {fi.strftime('%H:%M')})\n"
        f"- **Agenda:** Franja bloquejada al calendari com a `🎯 [Focus] {tema}`{musica_info}.\n"
        f"- **Consell:** Minimitza finestres, posa el mòbil en silenci i a per totes!"
    )

@tool
def analitzar_document_o_practica(nom_fitxer_o_ruta: str) -> str:
    """
    Analitza un document acadèmic o professional (enunciat de pràctica en PDF, guia docent o memòria TFG).
    Extreu objectius, terminis de lliurament, entregables exigits, criteris d'avaluació i tasques recomanades.
    Paràmetres:
      - nom_fitxer_o_ruta: Nom del fitxer desat a marc/data/documents o ruta absoluta al PDF/document.
    """
    res = analyze_document_with_ai(nom_fitxer_o_ruta)
    if not res.get("success"):
        docs = list_stored_documents()
        docs_str = ", ".join([d["filename"] for d in docs]) if docs else "Cap document a marc/data/documents"
        return f"⚠️ No s'ha pogut analitzar el document: {res.get('error')}. Documents disponibles: {docs_str}"

    a = res.get("analysis", {})
    titol = a.get("title", res.get("filename"))
    resum = a.get("summary", "")
    
    lliurables = "\n".join([f"  • {item}" for item in a.get("deliverables", [])]) or "  • Cap detallat"
    terminis = "\n".join([f"  • **{d.get('concept')}:** {d.get('date')} {d.get('time') or ''}" for d in a.get("deadlines", [])]) or "  • Sense terminis explícits"
    criteris = "\n".join([f"  • {c}" for c in a.get("evaluation_criteria", [])]) or "  • Criteris generals"
    tasques = "\n".join([f"  • [{t.get('priority', 'alta').upper()}] {t.get('title')} (Data límit: {t.get('due_date') or 'Sense data'})" for t in a.get("recommended_tasks", [])]) or "  • Cap tasca suggerida"

    return (
        f"### 📄 Anàlisi Intel·ligent del Document: **{titol}**\n\n"
        f"**📋 Resum executiu:**\n{resum}\n\n"
        f"**📦 Lliurables exigits:**\n{lliurables}\n\n"
        f"**⏰ Terminis i Dates Clau:**\n{terminis}\n\n"
        f"**🎯 Criteris d'Avaluació:**\n{criteris}\n\n"
        f"**✅ Tasques Recomanades per a To-Do:**\n{tasques}\n\n"
        f"---\n"
        f"*Pots demanar-me que creï automàticament aquestes tasques al teu To-Do o que programi els terminis a la teva agenda.*"
    )

@tool
def generar_daily_briefing() -> str:
    """
    Genera un resum executiu complet de la jornada d'avui:
    - Data, hora actual i condicions meteorològiques a Girona / EPS.
    - Reunions i esdeveniments previstos a l'agenda.
    - Tasques prioritàries pendents de resoldre.
    - Correus no llegits pendents d'atenció.
    """
    ara = datetime.now()
    avui_str = ara.strftime("%Y-%m-%d")
    data_formatada = ara.strftime("%A, %d de %B de %Y")

    # 0. Temps a Girona
    w = get_girona_weather(avui_str)
    part_temps = f"  • {w.get('summary', 'Temps no disponible')}"

    # 1. Reunions d'avui
    esdeveniments = fetch_calendar_events(date_prefix=avui_str)
    part_agenda = []
    if esdeveniments:
        for ev in esdeveniments:
            hora = ev["start_time"].split(" ")[1] if " " in ev["start_time"] else ev["start_time"]
            part_agenda.append(f"  • **{hora}**: {ev['title']} ({ev.get('location') or 'Sense lloc'})")
    else:
        part_agenda.append("  • *No hi ha reunions programades per avui. Tens la jornada lliure.*")

    # 2. Tasques pendents
    tasques = db_get_tasks(status="pendent")
    part_tasques = []
    if tasques:
        for t in tasques[:4]:
            part_tasques.append(f"  • [{t['priority'].upper()}] **{t['title']}**")
        if len(tasques) > 4:
            part_tasques.append(f"  • *...i {len(tasques) - 4} tasques més.*")
    else:
        part_tasques.append("  • *Cap tasca pendent. Tot al dia!*")

    # 3. Correus no llegits
    correus = fetch_unread_emails(limit=5)
    part_correus = []
    if correus:
        for c in correus[:3]:
            remitent = c.get("sender", "Desconegut")
            assumpte = c.get("subject", "(Sense assumpte)")
            part_correus.append(f"  • De **{remitent}**: *{assumpte}*")
        if len(correus) > 3:
            part_correus.append(f"  • *...i {len(correus) - 3} correus no llegits més.*")
    else:
        part_correus.append("  • *La bústia d'entrada està al dia. Sense correus pendents.*")

    briefing = (
        f"## ☀️ Daily Executive Briefing // {data_formatada}\n\n"
        f"### 🌦️ Temps a Girona (EPS - Montilivi):\n{part_temps}\n\n"
        f"### 📅 Agenda d'Avui:\n" + "\n".join(part_agenda) + "\n\n"
        f"### 🎯 Tasques Prioritàries:\n" + "\n".join(part_tasques) + "\n\n"
        f"### 📬 Bústia d'Entrada:\n" + "\n".join(part_correus) + "\n\n"
        f"---\n"
        f"*Consell executiu de M.A.R.C.: Revisa la teva agenda i comença per la tasca de màxima prioritat.*"
    )
    return briefing


# ==============================================================================
# 7. EINES DE CERCA I LECTURA WEB (SEARXNG & BEAUTIFULSOUP)
# ==============================================================================

@tool
def buscar_informacio_internet(consulta: str) -> str:
    """
    Busca informació actualitzada a internet utilitzant el motor privat SearxNG.
    Útil per consultar notícies, el temps, informació sobre empreses, persones o conceptes.
    """
    url = "http://127.0.0.1:8080/search"
    params = {
        "q": consulta,
        "format": "json"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return "No s'han trobat resultats a la xarxa per a aquesta cerca."
            
            resum_resultats = []
            for r in results[:3]:
                titol = r.get("title", "")
                content = r.get("content", "")
                resum_resultats.append(f"- **{titol}**: {content}")
                
            return "\n".join(resum_resultats)
        else:
            return f"Error en el servidor de cerca local: codi {response.status_code}"
    except Exception as e:
        return f"No s'ha pogut connectar amb el motor SearXNG local: {e}"

@tool
def visitar_pagina_web(url: str) -> str:
    """
    Visita una pàgina web concreta (URL completa) i n'extreu el text net.
    Útil per llegir articles, informació d'enllaços o resums de webs.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MARC-ExecutiveAssistant/2.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Error en accedir a la URL: Codi de resposta {res.status_code}"
        
        soup = BeautifulSoup(res.text, "html.parser")
        for s in soup(["script", "style", "nav", "footer"]):
            s.decompose()
            
        text = soup.get_text(separator="\n", strip=True)
        return text[:3500] if len(text) > 3500 else text
    except Exception as e:
        return f"Error en llegir la pàgina {url}: {e}"

# ==============================================================================
# 8. SINCRONITZACIÓ OFFLINE-FIRST (CUA LOCAL I SERVIDORS REMOTS)
# ==============================================================================

@tool
def sincronitzar_dades_remotes() -> str:
    """
    Sincronitza totes les cites locals pendents amb Google Calendar i envia els correus de la cua 'outbox' un cop restablerta la connexió a internet.
    Útil quan s'ha estat treballant sense connexió i es volen bolcar tots els canvis acumulats als servidors remots.
    """
    from marc.services.sync_manager import run_full_synchronization
    res = run_full_synchronization()
    return res["message"]

# ==============================================================================
# 9. FLUXOS DE TREBALL ASÍNCRONS I AUTOMATITZACIONS (STATE MACHINE ENGINE)
# ==============================================================================

@tool
def crear_flux_asincron(
    titol: str,
    tipus_flux: str,
    trigger_tipus: str,
    condicio_trigger_json: str,
    accio_tipus: str,
    configuracio_accio_json: str,
    context_dades_json: str = "{}"
) -> str:
    """
    Registra un nou flux de treball asíncron que s'executarà en segon pla quan es compleixi un disparador (trigger).
    Permet gestionar tasques que requereixen esperar hores o dies (p.ex. rebre resposta d'un correu de reunió, esperar a una data o revisió).
    
    Paràmetres:
    - titol: Nom descriptiu del flux (ex: "Negociació de reunió amb tutor").
    - tipus_flux: Categoria del flux (ex: "meeting_negotiation", "task_followup", "conditional_reminder", "custom").
    - trigger_tipus: Disparador esperat: "email_reply" (espera correu), "datetime" (espera arribar a data/hora límit).
    - condicio_trigger_json: Objecte JSON amb els filtres del disparador.
      Exemples:
      - Per a email_reply: {"sender": "prof@udg.edu", "subject_contains": "Reunió"}
      - Per a datetime: {"target_datetime": "2026-10-25 10:00"}
    - accio_tipus: Acció a dur a terme quan el trigger es dispari:
      "schedule_event" (programa cita a l'agenda), "create_task" (crea tasca), "notify" (envia avís).
    - configuracio_accio_json: Dades de l'acció a executar en format JSON.
      Exemple: {"event_title": "Reunió TFG", "duration_minutes": 60, "location": "Despatx Tutor"}
    - context_dades_json: Variables i context addicional en JSON (ex: {"proposed_datetime": "2026-10-27 10:00"}).
    """
    from marc.core.db import db_create_workflow
    try:
        cond = json.loads(condicio_trigger_json) if isinstance(condicio_trigger_json, str) else condicio_trigger_json
        act_cfg = json.loads(configuracio_accio_json) if isinstance(configuracio_accio_json, str) else configuracio_accio_json
        ctx = json.loads(context_dades_json) if isinstance(context_dades_json, str) else context_dades_json
    except Exception as e:
        return f"Error en el format JSON dels paràmetres: {e}"

    wf_id = db_create_workflow(
        title=titol,
        workflow_type=tipus_flux,
        trigger_type=trigger_tipus,
        trigger_condition=cond,
        action_type=accio_tipus,
        action_config=act_cfg,
        context_data=ctx
    )
    return f"Flux de treball asíncron #{wf_id} '{titol}' creat i activat. Estat: pendent de trigger '{trigger_tipus}'."

@tool
def consultar_fluxos_actius(filtre: str = "tots") -> str:
    """
    Consulta tots els fluxos de treball asíncrons actius o recents i el seu estat actual.
    Útil per comprovar quines automatitzacions o respostes està esperant l'agent.
    Paràmetres:
    - filtre: Opcional. "tots", "pending" o "completed". Per defecte "tots".
    """
    from marc.core.db import db_get_workflows
    status_filter = filtre.strip().lower() if filtre and filtre.strip().lower() in ("pending", "completed", "cancelled") else None
    wfs = db_get_workflows(status=status_filter)
    if not wfs:
        return "No hi ha cap flux de treball asíncron registrat."
    
    linies = ["FLUXOS DE TREBALL ASÍNCRONS (AUTOMATITZACIONS):"]
    for w in wfs:
        estat_icon = "⏳" if w["status"] == "pending" else ("✅" if w["status"] == "completed" else "⚠️")
        linies.append(f"- #{w['id']} {estat_icon} [{w['status'].upper()}] '{w['title']}' | Tipus: {w['workflow_type']} | Trigger: {w['trigger_type']}")
        if w.get("result_summary"):
            linies.append(f"  Resultat: {w['result_summary']}")
    return "\n".join(linies)

@tool
def cancel_lar_flux_asincron(flux_id: int) -> str:
    """
    Cancel·la un flux de treball asíncron actiu perquè deixi d'esperar disparadors.
    """
    from marc.core.db import db_update_workflow, db_add_workflow_log
    db_update_workflow(flux_id, status="cancelled", result_summary="Cancel·lat manualment per l'usuari.")
    db_add_workflow_log(flux_id, "cancelled", "Cancel·lat per comanda de l'agent/usuari.")
    return f"Flux #{flux_id} cancel·lat correctament."

@tool
def eliminar_flux_asincron(flux_id: int) -> str:
    """
    Elimina definitivament un flux de treball de la base de dades (especialment si ja està acabat o cancel·lat).
    Paràmetres:
    - flux_id: Identificador numèric del flux a eliminar.
    """
    from marc.core.db import db_delete_workflow
    if db_delete_workflow(flux_id):
        return f"🗑️ El flux #{flux_id} ha estat eliminat definitivament de la base de dades."
    return f"⚠️ No s'ha trobat cap flux amb ID #{flux_id}."


@tool
def executar_cicle_fluxos(motiu: str = "verificacio_manual") -> str:
    """
    Força una revisió immediata de tots els fluxos asíncrons pendents (correus rebuts i terminis).
    Paràmetres:
    - motiu: Motiu de l'execució (per defecte 'verificacio_manual').
    """
    from marc.services.workflow_engine import run_workflow_cycle
    res = run_workflow_cycle()
    return res["message"]