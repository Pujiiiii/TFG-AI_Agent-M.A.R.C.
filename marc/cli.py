from core.agent import get_agent_executor

def main():
    print("🤖 Inicialitzant el nucli de M.A.R.C. (Mòdul d'Assistència i Resposta Computacional)...")
    agent_executor = get_agent_executor()
    
    print("✅ Sistema a punt! Escriu 'sortir' per tancar.")
    print("-" * 50)
    
    while True:
        user_input = input("\n👤 Tu: ")
        
        if user_input.lower() in ['sortir', 'exit', 'quit']:
            print("🤖 M.A.R.C.: Apagant sistemes. Adéu!")
            break
            
        print("🤖 M.A.R.C.: Processant...")
        
        response = agent_executor.invoke({"input": user_input})
        
        print(f"\n🤖 M.A.R.C.: {response['output']}")

if __name__ == "__main__":
    main()