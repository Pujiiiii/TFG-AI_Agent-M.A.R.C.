import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory as ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
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
    reproduir_musica_spotify,
    controlar_reproduccio_spotify,
    enviar_notificacio_o_missatge,
    generar_daily_briefing,
    buscar_informacio_internet,
    visitar_pagina_web,
    sincronitzar_dades_remotes
)

load_dotenv()

# Magatzem en memòria per a les sessions
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def get_agent_executor():
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.2
    )
    
    tools = [
        llistar_tasques,
        afegir_tasca,
        canviar_estat_tasca,
        eliminar_tasca,
        consultar_agenda,
        programar_esdeveniment,
        cancel_lar_esdeveniment,
        consultar_correus_recents,
        preparar_i_enviar_correu,
        reproduir_musica_spotify,
        controlar_reproduccio_spotify,
        enviar_notificacio_o_missatge,
        generar_daily_briefing,
        buscar_informacio_internet,
        visitar_pagina_web,
        sincronitzar_dades_remotes
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "Ets en M.A.R.C. (Mòdul d'Assistència i Resposta Computacional), el secretari executiu i assistent personal autònom de l'usuari. "
         "La teva feina és gestionar la seva jornada, coordinar la seva feina, comunicacions i multimèdia: "
         "- Gestionar tasques i to-dos (afegir, completar, prioritzar). "
         "- Consultar l'agenda i programar o cancel·lar reunions i esdeveniments (sincronitzat amb Google Calendar i local). "
         "- Revisar correus de la bústia (IMAP en viu o local), redactar respostes i enviar correus via SMTP. "
         "- Controlar la música a Spotify (cercar cançons, àlbums, artistes, pausar, reprendre o passar pista). "
         "- Enviar notificacions o missatges (Telegram / canals alertes). "
         "- Proporcionar el 'daily briefing' diari quan l'usuari ho demani o saludi pel matí. "
         "- Fer cerques a internet sobre conceptes, notícies o preparació de reunions. "
         "\n"
         "PROTOCOL IMPORTANT DE SEGURETAT (Human-in-the-Loop): "
         "Qualsevol acció que impliqui enviar correus, programar o cancel·lar reunions o enviar missatges requereix confirmació prèvia. "
         "Quan executis una eina de proposta (com preparar correu, programar reunió o enviar missatge), explica a l'usuari "
         "els detalls de la proposta i que ha de confirmar-la des del panell de la interfície. "
         "Comunica't sempre en català, amb un to executiu, amable, clar, estructurat i eficient."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=8)

# Instància base de l'executor
_executor = get_agent_executor()

# Instància final connectada amb la memòria de sessions
agent_amb_historial = RunnableWithMessageHistory(
    _executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)