import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from core.tools import llistar_arxius

load_dotenv()

def get_agent_executor():
    llm = ChatGroq(
        model="openai/gpt-oss-120b", 
        temperature=0.3
    )
    
    tools = [llistar_arxius]
    
    # Actualitzem la identitat al prompt del sistema
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Ets en M.A.R.C. (Mòdul d'Assistència i Resposta Computacional), un assistent personal eficient i directe. Tens eines per veure els arxius de l'usuari."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor