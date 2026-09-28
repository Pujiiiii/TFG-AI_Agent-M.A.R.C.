# TFG-AI_Agent-M.A.R.C. (Mòdul d'Assistència i Resposta Computacional)
A personal AI agent to help on the daily basis.

Pasos per a engegar-lo:

1- Obrir Docker desktop 

2- executar: docker compose up -d

3- executar: uvicorn marc.main:app --reload --reload-dir marc --host 0.0.0.0 --port 8000