# M.A.R.C. (Mòdul d'Assistència i Resposta Computacional)
> **Treball de Final de Grau (TFG)**  
> Assistent Personal Intel·ligent i Secretari Executiu Autònom amb Supervisió Humana (*Human-in-the-Loop*).

---

## 🌟 Visió General
**M.A.R.C.** és un agent d'intel·ligència artificial dissenyat per actuar com a secretari executiu i assistent personal autònom. Ajuda l'usuari a organitzar la seva jornada, coordinar comunicacions, planificar la feina i buscar informació amb seguretat i privadesa.

### ✨ Funcionalitats Principals
* 📋 **Gestió de Tasques i To-Dos**: Llistat interactiu de tasques, priorització (Alta, Mitjana, Baixa) i marcatge com a completades tant des del xat com des del panell lateral HUD.
* 📅 **Agenda i Calendari**: Consulta de reunions i cites d'avui o d'altres dies, detecció de conflictes i programació supervisada de nous esdeveniments.
* 📬 **Email Hub (Correu Electrònic)**: Lectura de correus nous o pendents, redacció automàtica de respostes i enviament amb confirmació prèvia (suport per a SMTP real o bústia local integrada).
* 💬 **Missatgeria i Notificacions**: Enviament d'avisos i alertes al mòbil mitjançant **Telegram Bot API** o canal de sistema.
* ☀️ **Daily Briefing**: Resum executiu d'inici de jornada amb reunions del dia, tasques prioritàries pendents i novetats a la bústia.
* 🛡️ **Seguretat Human-in-the-Loop (HITL)**: Tota acció crítica (enviar un correu, programar/cancel·lar una reunió, enviar un missatge) es presenta primer en un modal interactiu perquè l'usuari l'aprovi o la rebutgi abans d'executar-se.
* 🔍 **Cerca Web Privada**: Integració amb motor de cerca privat **SearXNG** (Docker) per a consultes en temps real i navegació neta de pàgines web.

---

## 🛠️ Arquitectura Tècnica
* **Backend**: FastAPI + Python 3.12+
* **Orquestració d'Agents**: LangChain (`create_tool_calling_agent`, `AgentExecutor`, `RunnableWithMessageHistory`)
* **LLM Engine**: Groq API (models oberts d'alta velocitat)
* **Persistència de Dades**: Base de dades local **SQLite** (`data/marc.db`)
* **Frontend**: HUD / Cyberpunk Dark Terminal (HTML5, Vanilla CSS3, JavaScript modern amb Marked.js i Highlight.js)
* **Cerca**: SearXNG sobre contenidor Docker local (port 8080)

---

## 🚀 Com Engegar el Projecte

### 1. Requisits Previs
* Python 3.10 o superior
* Docker Desktop (opcional, per al motor SearXNG)

### 2. Instal·lació de Dependències
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuració d'Entorn (`.env`)
Crea o edita el fitxer `.env` a l'arrel del repositori:
```env
GROQ_API_KEY=el_teu_groq_api_key

# (Opcional) Per a lectura i enviament de correus reals (Gmail / Outlook):
# EMAIL_USER=el_teu_correu@gmail.com
# EMAIL_PASSWORD=la_teva_contrasenya_d_aplicacio
# IMAP_HOST=imap.gmail.com
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587

# (Opcional) Per a Spotify Web API (si no es posa, funciona amb l'app nativa d'escriptori):
# SPOTIFY_CLIENT_ID=el_teu_spotify_client_id
# SPOTIFY_CLIENT_SECRET=el_teu_spotify_client_secret
# SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

# (Opcional) Per a enviament de notificacions a Telegram:
# TELEGRAM_BOT_TOKEN=el_teu_token_de_bot
# TELEGRAM_CHAT_ID=el_teu_chat_id

# (Opcional) Per a Google Calendar:
# Descarrega el fitxer 'credentials.json' (OAuth Client ID) de Google Cloud Console
# i col·loca'l a l'arrel del projecte. S'obrirà automàticament el navegador per autoritzar.
```

### 4. Engegar SearXNG (Opcional per a cerques web)
```bash
docker compose up -d
```

### 5. Engegar el Servidor M.A.R.C.
Pots engegar directament amb el script amb auto-commit al tancar:
```bash
python run.py
```
O bé directament amb uvicorn:
```bash
uvicorn marc.main:app --reload --reload-dir marc --host 0.0.0.0 --port 8000
```

Obre el teu navegador a [http://localhost:8000](http://localhost:8000) per accedir a la consola HUD de M.A.R.C.