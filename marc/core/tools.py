import os
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
    is_google_calendar_connected
)
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
        resum=f"Programar reunió: '{titol}' el {data_hora_inici}",
        dades={
            "titol": titol,
            "data_inici": data_hora_inici,
            "data_fi": data_hora_fi,
            "durada": f"{durada_minuts} minuts",
            "lloc": lloc if lloc else "No especificat",
            "descripcio": descripcio if descripcio else "Cap descripció"
        },
        funcio_execucio=aplicar_esdeveniment
    )

    return f"[ACCIÓ PENDENT - ID: {accio['action_id']}] S'ha preparat la programació de l'esdeveniment '{titol}' per al {data_hora_inici}. Revisa i confirma des de la interfície."

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
        return res["message"]

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
def generar_daily_briefing() -> str:
    """
    Genera un resum executiu complet de la jornada d'avui:
    - Data i hora actuals.
    - Reunions i esdeveniments previstos a l'agenda.
    - Tasques prioritàries pendents de resoldre.
    - Correus no llegits pendents d'atenció.
    """
    ara = datetime.now()
    avui_str = ara.strftime("%Y-%m-%d")
    data_formatada = ara.strftime("%A, %d de %B de %Y")

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
    url = "http://localhost:8080/search"
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