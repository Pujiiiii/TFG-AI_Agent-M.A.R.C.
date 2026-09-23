import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from marc.core.tools import (
    llistar_arxius, 
    editar_arxiu, 
    llegir_arxiu, 
    crear_carpeta, 
    esborrar_arxiu, 
    buscar_informacio_internet
)

load_dotenv()

def get_agent_executor():
    llm = ChatGroq(
        model="openai/gpt-oss-120b", 
        temperature=0.3
    )
    
    tools = [
        llistar_arxius, 
        editar_arxiu, 
        llegir_arxiu, 
        crear_carpeta, 
        esborrar_arxiu, 
        buscar_informacio_internet
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Ets en M.A.R.C. (Mòdul d'Assistència i Resposta Computacional), un assistent personal autònom. Només pots fer servir les eines que tens definides i cap mes. Si fas un canvi, explica breument què has fet."),
        ("placeholder", "{chat_history}"), # Nova línia: Espai on s'injectarà la memòria
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor