import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

from marc.core.tools import (
    llistar_tasques,
    afegir_tasca,
    canviar_estat_tasca,
    eliminar_tasca,
    consultar_agenda,
    programar_esdeveniment,
    cancel_lar_esdeveniment,
    consultar_correus_recents,
    preparar_i_enviar_correu,
    analitzar_correus_udg,
    reproduir_musica_spotify,
    controlar_reproduccio_spotify,
    enviar_notificacio_o_missatge,
    generar_daily_briefing,
    buscar_informacio_internet,
    visitar_pagina_web,
    sincronitzar_dades_remotes,
    crear_flux_asincron,
    consultar_fluxos_actius,
    cancel_lar_flux_asincron,
    executar_cicle_fluxos
)

load_dotenv()

SYSTEM_PROMPT = (
    "Ets en M.A.R.C. (Mòdul d'Assistència i Resposta Computacional), el secretari executiu i assistent personal autònom de l'usuari. "
    "La teva feina és gestionar la seva jornada, coordinar la seva feina, comunicacions i multimèdia: "
    "- Gestionar tasques i to-dos (afegir, completar, prioritzar). "
    "- Consultar l'agenda i programar o cancel·lar reunions i esdeveniments (sincronitzat amb Google Calendar i local). Tens visibilitat tant dels teus esdeveniments personals com de tots els calendaris subscrits o importats (per exemple: horaris de classe de la universitat UdG, sessions i curses de Formula 1, festius, etc.). "
    "- Revisar correus de la bústia (IMAP en viu o local), redactar respostes i enviar correus via SMTP. "
    "- Analitzar autònomament els correus rebuts de la universitat (UdG / EPS / Moodle / professors): detectar terminis de plaç d'entrega de treballs, pràctiques o dates d'examen, i crear automàticament tasques a To-Do i recordatoris a l'agenda. "
    "- Gestionar fluxos de treball asíncrons i màquines d'estats amb triggers (State Machine Engine): si l'usuari et demana una comanda que requereix diversos passos en el temps (com per exemple demanar una reunió a algú i esperar resposta per correu per crear la cita a l'agenda, o esperar un termini temporal), has d'enviar el correu corresponent i crear immediatament un flux asíncron amb `crear_flux_asincron`. Així el sistema monitorarà en segon pla les respostes i executarà la següent acció quan arribi el trigger sense haver d'esperar manualment. "
    "- Controlar la música a Spotify (cercar i posar cançons, àlbums, artistes, pausar, reprendre o passar de pista). "
    "- Enviar notificacions o missatges (Telegram / canals alertes). "
    "- Proporcionar el 'daily briefing' diari quan l'usuari ho demani o saludi pel matí. "
    "- Fer cerques a internet sobre conceptes, notícies o preparació de reunions. "
    "\n"
    "PROTOCOL IMPORTANT DE SEGURETAT (Human-in-the-Loop): "
    "Qualsevol acció que impliqui enviar correus, programar o cancel·lar reunions o enviar missatges requereix confirmació prèvia. "
    "Quan executis una eina de proposta (com preparar correu, programar reunió o enviar missatge), explica a l'usuari "
    "els detalls de la proposta i que ha de confirmar-la des del panell de la interfície. "
    "Comunica't sempre en català, amb un to executiu, amable, clar, estructurat i eficient."
)

ALL_TOOLS = [
    llistar_tasques,
    afegir_tasca,
    canviar_estat_tasca,
    eliminar_tasca,
    consultar_agenda,
    programar_esdeveniment,
    cancel_lar_esdeveniment,
    consultar_correus_recents,
    preparar_i_enviar_correu,
    analitzar_correus_udg,
    reproduir_musica_spotify,
    controlar_reproduccio_spotify,
    enviar_notificacio_o_missatge,
    generar_daily_briefing,
    buscar_informacio_internet,
    visitar_pagina_web,
    sincronitzar_dades_remotes,
    crear_flux_asincron,
    consultar_fluxos_actius,
    cancel_lar_flux_asincron,
    executar_cicle_fluxos
]

def extract_text_from_content(content) -> str:
    """Extreu el text net de qualsevol format de resposta de LLM (string, llista de blocs o diccionari)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                parts.append(p.get("text", ""))
            elif isinstance(p, dict) and "text" in p:
                parts.append(p["text"])
            elif isinstance(p, str):
                parts.append(p)
        return "".join(parts)
    return str(content)

def get_llm():
    """Inicialitza el model principal (Google Gemini si hi ha clau, fallback a Groq)."""
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        return ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=google_key,
            temperature=0.2
        )
    else:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.2
        )

class MarcAgentRunner:
    def __init__(self):
        self.llm = get_llm()
        self.memory = MemorySaver()
        self.agent = create_agent(
            self.llm,
            tools=ALL_TOOLS,
            checkpointer=self.memory,
            system_prompt=SYSTEM_PROMPT
        )
        self.initialized_threads = set()

    def invoke(self, input_data: dict, config: dict = None) -> dict:
        session_id = "default"
        if config and "configurable" in config:
            session_id = config["configurable"].get("session_id") or config["configurable"].get("thread_id") or "default"

        user_input = input_data.get("input", "")
        thread_cfg = {"configurable": {"thread_id": session_id}}

        messages_to_send = []
        # Si el fil encara no s'ha inicialitzat en memòria, carreguem l'historial previ des de SQLite
        if session_id not in self.initialized_threads:
            self.initialized_threads.add(session_id)
            try:
                from marc.core.db import db_get_session_messages
                msgs = db_get_session_messages(session_id)
                # Si main.py ja ha inserit l'últim missatge de l'usuari a la BD, no el dupliquem
                prev_msgs = msgs[:-1] if msgs and msgs[-1]["sender"].lower() == "user" and msgs[-1]["message"] == user_input else msgs
                for m in prev_msgs:
                    if m["sender"].lower() == "user":
                        messages_to_send.append(HumanMessage(content=m["message"]))
                    else:
                        messages_to_send.append(AIMessage(content=m["message"]))
            except Exception as e:
                print(f"[Agent Memory Load Warning]: {e}")

        messages_to_send.append(HumanMessage(content=user_input))

        res = self.agent.invoke({"messages": messages_to_send}, config=thread_cfg)
        last_msg = res["messages"][-1]
        output_text = extract_text_from_content(last_msg.content)
        return {"output": output_text}

# Instància global connectada amb el gestor de sessions
agent_amb_historial = MarcAgentRunner()
store = {}