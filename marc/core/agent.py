import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory as ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from marc.core.tools import (
    llistar_arxius,
    llegir_arxiu, 
    crear_carpeta, 
    esborrar_arxiu, 
    buscar_informacio_internet,
    buscar_text_en_projecte,
    buscar_arxiu_per_nom,
    editar_arxiu_amb_diff,
    visitar_pagina_web,
    descarregar_recurs_internet,
    executar_script_o_comanda,
    gestio_git
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
        llistar_arxius,
        llegir_arxiu, 
        crear_carpeta, 
        esborrar_arxiu, 
        buscar_informacio_internet,
        buscar_text_en_projecte,
        buscar_arxiu_per_nom,
        editar_arxiu_amb_diff,
        visitar_pagina_web,
        descarregar_recurs_internet,
        executar_script_o_comanda,
        gestio_git
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "Ets en M.A.R.C. (Mòdul d'Assistència i Resposta Computacional), un enginyer de programari i assistent personal autònom. "
         "Només pots fer servir les eines definides. "
         "SEMPRE has de respondre a l'usuari amb un missatge en llenguatge natural explicant el resultat, fins i tot si una eina ha donat un error o no ha trobat dades. "
         "Mai finalitzis la resposta en blanc."),
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