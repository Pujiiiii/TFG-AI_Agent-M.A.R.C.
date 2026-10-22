import os
import sqlite3
import json
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "marc.db")

def get_db_connection():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Taula de Tasques (To-Do / Work Planning)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        priority TEXT DEFAULT 'mitjana',
        status TEXT DEFAULT 'pendent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Taula d'Esdeveniments i Agenda (Calendar)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT,
        location TEXT,
        synced_remote INTEGER DEFAULT 0,
        remote_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Taula de Correus (Inbox, Sent, Outbox, Drafts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        folder TEXT DEFAULT 'inbox',
        is_read INTEGER DEFAULT 0,
        synced_remote INTEGER DEFAULT 0,
        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Taula de Notificacions / Missatges enviats
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT NOT NULL,
        channel TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'sent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Taula d'Historial de Converses / Sessions de Xat (Persistent i ultra-lleugera)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id)")

    # Taula de Fluxos de Treball Asíncrons (Generic Workflow & State Machine Engine)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        workflow_type TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        trigger_type TEXT NOT NULL,
        trigger_condition TEXT,
        action_type TEXT NOT NULL,
        action_config TEXT,
        context_data TEXT,
        result_summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflows(status)")

    # Taula de Logs d'Auditoria dels Fluxos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflow_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        detail TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
    )
    """)

    conn.commit()

    # Migració de seguretat per si la taula ja existia sense les columnes de sincronització
    try:
        cursor.execute("PRAGMA table_info(events)")
        cols_events = [row[1] for row in cursor.fetchall()]
        if "synced_remote" not in cols_events:
            cursor.execute("ALTER TABLE events ADD COLUMN synced_remote INTEGER DEFAULT 0")
        if "remote_id" not in cols_events:
            cursor.execute("ALTER TABLE events ADD COLUMN remote_id TEXT")

        cursor.execute("PRAGMA table_info(emails)")
        cols_emails = [row[1] for row in cursor.fetchall()]
        if "synced_remote" not in cols_emails:
            cursor.execute("ALTER TABLE emails ADD COLUMN synced_remote INTEGER DEFAULT 0")
        if "is_analyzed" not in cols_emails:
            cursor.execute("ALTER TABLE emails ADD COLUMN is_analyzed INTEGER DEFAULT 0")
        if "analysis_result" not in cols_emails:
            cursor.execute("ALTER TABLE emails ADD COLUMN analysis_result TEXT")

        conn.commit()
    except Exception as e:
        print(f"[DB Migration Warning]: {e}")

    # Si la base de dades és completament nova, inserim dades inicials demostratives
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        avui = datetime.now().strftime("%Y-%m-%d")
        dema = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        cursor.execute("""
        INSERT INTO tasks (title, description, due_date, priority, status)
        VALUES 
        ('Revisar la memòria inicial del TFG', 'Adaptar els objectius cap al secretari personal intel·ligent.', ?, 'alta', 'pendent'),
        ('Preparar la reunió de seguiment', 'Resumir les noves eines i la integració del panell HUD.', ?, 'mitjana', 'pendent'),
        ('Configurar credencials opcionals de correu i Telegram', 'Revisar l arxiu .env amb les claus d API.', ?, 'baixa', 'pendent')
        """, (avui, avui, dema))

        cursor.execute("""
        INSERT INTO events (title, description, start_time, end_time, location, synced_remote)
        VALUES 
        ('Reunió de seguiment del TFG', 'Comentar l enfocament d assistent executiu i calendari.', ? || ' 16:30', ? || ' 17:30', 'Despatx Tutor / Online', 1),
        ('Sessió de planificació setmanal', 'Revisió de tasques pendents i prioritats.', ? || ' 11:00', ? || ' 11:45', 'Sala d reunions', 1)
        """, (avui, avui, dema, dema))

        cursor.execute("""
        INSERT INTO emails (sender, recipient, subject, body, folder, is_read, synced_remote)
        VALUES 
        ('tutor.tfg@universitat.cat', 'usuari@tfg.cat', 'Revisió del nou enfocament de M.A.R.C.', 'Hola Marc, he vist la proposta de canvi cap a secretari executiu i em sembla excel·lent. Quedem avui per comentar-ho.', 'inbox', 0, 1),
        ('equip.projecte@startup.com', 'usuari@tfg.cat', 'Actualització de fites setmanals', 'Bon dia, et passem el resum de les fites pendents d aquesta setmana.', 'inbox', 0, 1)
        """)

        conn.commit()

    conn.close()

# --- FUNCIONS AUXILIARS DE TASQUES ---
def db_add_task(title: str, priority: str = "mitjana", due_date: str = None, description: str = ""):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (title, description, due_date, priority, status) VALUES (?, ?, ?, ?, 'pendent')",
        (title.strip(), description.strip(), due_date.strip() if due_date else None, priority.lower().strip())
    )
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    return task_id

def db_get_tasks(status: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM tasks WHERE status = ? ORDER BY CASE priority WHEN 'alta' THEN 1 WHEN 'mitjana' THEN 2 ELSE 3 END, id DESC", (status,))
    else:
        c.execute("SELECT * FROM tasks ORDER BY CASE status WHEN 'pendent' THEN 1 ELSE 2 END, CASE priority WHEN 'alta' THEN 1 WHEN 'mitjana' THEN 2 ELSE 3 END, id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_toggle_task(task_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    nou_estat = "completada" if row["status"] == "pendent" else "pendent"
    c.execute("UPDATE tasks SET status = ? WHERE id = ?", (nou_estat, task_id))
    conn.commit()
    conn.close()
    return nou_estat

def db_delete_task(task_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# --- FUNCIONS AUXILIARS D'AGENDA / ESDEVENIMENTS ---
def db_add_event(title: str, start_time: str, end_time: str = None, location: str = "", description: str = "", synced_remote: int = 0, remote_id: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (title, description, start_time, end_time, location, synced_remote, remote_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title.strip(), description.strip(), start_time.strip(), end_time.strip() if end_time else None, location.strip(), synced_remote, remote_id)
    )
    conn.commit()
    event_id = c.lastrowid
    conn.close()
    return event_id

def db_get_events(date_prefix: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    if date_prefix:
        c.execute("SELECT * FROM events WHERE start_time LIKE ? ORDER BY start_time ASC", (f"{date_prefix}%",))
    else:
        c.execute("SELECT * FROM events ORDER BY start_time ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_delete_event(event_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id = ?", (event_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def db_get_unsynced_events():
    """Retorna les cites creades en local que encara no s'han sincronitzat amb Google Calendar."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE synced_remote = 0 ORDER BY id ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_mark_event_synced(event_id: int, remote_id: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE events SET synced_remote = 1, remote_id = ? WHERE id = ?", (remote_id, event_id))
    conn.commit()
    conn.close()

# --- FUNCIONS AUXILIARS DE CORREU ---
def db_get_emails(folder: str = "inbox", limit: int = 10, unread_only: bool = False):
    conn = get_db_connection()
    c = conn.cursor()
    query = "SELECT * FROM emails WHERE folder = ?"
    params = [folder]
    if unread_only:
        query += " AND is_read = 0"
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    c.execute(query, tuple(params))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_add_email(sender: str, recipient: str, subject: str, body: str, folder: str = "inbox", is_read: int = 0, synced_remote: int = 0):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO emails (sender, recipient, subject, body, folder, is_read, synced_remote) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sender.strip(), recipient.strip(), subject.strip(), body.strip(), folder, is_read, synced_remote)
    )
    conn.commit()
    email_id = c.lastrowid
    conn.close()
    return email_id

def db_get_pending_outbox_emails():
    """Retorna els correus que estan a la cua de sortida pendents d'enviar quan hi hagi internet."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM emails WHERE folder = 'outbox' ORDER BY id ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_mark_email_sent(email_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE emails SET folder = 'sent', is_read = 1, synced_remote = 1 WHERE id = ?", (email_id,))
    conn.commit()
    conn.close()

def db_mark_email_read(email_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE emails SET is_read = 1 WHERE id = ?", (email_id,))
    conn.commit()
    conn.close()

# --- FUNCIONS AUXILIARS DE NOTIFICACIONS ---
def db_add_notification(recipient: str, channel: str, message: str, status: str = "sent"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO notifications (recipient, channel, message, status) VALUES (?, ?, ?, ?)",
        (recipient.strip(), channel.strip(), message.strip(), status)
    )
    conn.commit()
    notif_id = c.lastrowid
    conn.close()
    return notif_id

def db_get_notifications(limit: int = 10):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_get_sync_summary():
    """Retorna el recompte d'elements locals pendents de pujar als servidors remots."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM events WHERE synced_remote = 0")
    pending_events = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM emails WHERE folder = 'outbox'")
    pending_emails = c.fetchone()[0]
    conn.close()
    return {
        "pending_events": pending_events,
        "pending_emails": pending_emails,
        "total_pending": pending_events + pending_emails
    }

def db_get_unanalyzed_udg_emails():
    """Retorna els correus de la bústia que provenen de la UdG, Moodle o departaments i que encara no han estat analitzats."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM emails 
        WHERE folder = 'inbox' 
          AND is_analyzed = 0 
          AND (
            LOWER(sender) LIKE '%udg.edu%' 
            OR LOWER(sender) LIKE '%moodle%' 
            OR LOWER(sender) LIKE '%universitat%'
            OR LOWER(subject) LIKE '%udg%' 
            OR LOWER(subject) LIKE '%moodle%' 
            OR LOWER(subject) LIKE '%pràctica%'
            OR LOWER(subject) LIKE '%practica%'
            OR LOWER(subject) LIKE '%lliurament%'
            OR LOWER(subject) LIKE '%examen%'
            OR LOWER(body) LIKE '%udg.edu%'
            OR LOWER(body) LIKE '%campus virtual%'
          )
        ORDER BY id ASC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_mark_email_analyzed(email_id: int, result_summary: str = ""):
    """Marca un correu com a analitzat i en guarda el resum de decisions preses."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE emails SET is_analyzed = 1, analysis_result = ?, is_read = 1 WHERE id = ?",
        (result_summary.strip(), email_id)
    )
    conn.commit()
    conn.close()

def db_ensure_sample_udg_emails():
    """Assegura l'existència de correus acadèmics d'exemple de la UdG per a proves si no n'hi ha cap."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM emails WHERE sender LIKE '%udg.edu%' OR sender LIKE '%moodle%'")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO emails (sender, recipient, subject, body, folder, is_read, synced_remote, is_analyzed)
            VALUES 
            (
                'professor.sgbd@eps.udg.edu',
                'marcpujol2601@gmail.com',
                '[SGBD] Lliurament de la Pràctica 2 - Disseny de base de dades NoSQL',
                'Benvolguts alumnes de Sistemes de Gestió de Bases de Dades,\n\nUs recordem que el termini improrrogable per lliurar la Pràctica 2 (Modelat NoSQL amb MongoDB) a través de la bústia de lliuraments del Campus Virtual finalitza el proper 28 d''octubre de 2026 a les 23:59h.\n\nLa pràctica s''ha de lliurar en format ZIP amb la memòria explicativa i els scripts de càrrega. Té un pes del 20% en l''avaluació continuada.\n\nAtentament,\nEquip docent de SGBD - EPS UdG',
                'inbox',
                0,
                1,
                0
            ),
            (
                'avisos.moodle@udg.edu',
                'marcpujol2601@gmail.com',
                '[Habilitats Directives] Convocatòria Presentació de l''Estudi de Cas',
                'Hola Marc,\n\nS''ha publicat al Campus Virtual la convocatòria oficial per a la defensa de l''Estudi de Cas en equip d''Habilitats Directives i de Comunicació.\n\nLa teva sessió tindrà lloc el proper 29 d''octubre de 2026 a les 14:30h a l''aula II-02B de l''EPS.\n\nRecordeu portar la presentació en PDF abans d''iniciar la classe.\n\nSalutacions,\nCoordinació Moodle UdG',
                'inbox',
                0,
                1,
                0
            )
        """)
        conn.commit()
    conn.close()

def db_add_chat_message(session_id: str, sender: str, message: str):
    """Guarda un missatge de la conversa a la sessió indicada a SQLite."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_messages (session_id, sender, message) VALUES (?, ?, ?)",
        (session_id.strip(), sender.strip(), message.strip())
    )
    conn.commit()
    msg_id = c.lastrowid
    conn.close()
    return msg_id

def db_get_session_messages(session_id: str, limit: int = 200):
    """Retorna els missatges d'una sessió ordenats cronològicament."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, session_id, sender, message, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
        (session_id.strip(), limit)
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_get_all_sessions():
    """Retorna totes les sessions que tenen missatges registrats."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT session_id FROM chat_messages ORDER BY id DESC")
    sessions = [row["session_id"] for row in c.fetchall()]
    conn.close()
    if "sessio_per_defecte" not in sessions:
        sessions.insert(0, "sessio_per_defecte")
    return sessions

# --- FUNCIONS AUXILIARS DE FLUXOS DE TREBALL ASÍNCRONS (GENERIC WORKFLOW ENGINE) ---
def db_create_workflow(
    title: str,
    workflow_type: str,
    trigger_type: str,
    trigger_condition: dict,
    action_type: str,
    action_config: dict,
    context_data: dict = None
) -> int:
    """Crea i registra un nou flux asíncron a SQLite."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO workflows 
        (title, workflow_type, status, trigger_type, trigger_condition, action_type, action_config, context_data)
        VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            workflow_type.strip(),
            trigger_type.strip(),
            json.dumps(trigger_condition or {}, ensure_ascii=False),
            action_type.strip(),
            json.dumps(action_config or {}, ensure_ascii=False),
            json.dumps(context_data or {}, ensure_ascii=False)
        )
    )
    conn.commit()
    wf_id = c.lastrowid
    
    c.execute(
        "INSERT INTO workflow_logs (workflow_id, event_type, detail) VALUES (?, 'created', ?)",
        (wf_id, f"Flux '{title}' creat amb èxit. Esperant trigger de tipus '{trigger_type}'.")
    )
    conn.commit()
    conn.close()
    return wf_id

def db_get_workflows(status: str = None, trigger_type: str = None) -> list:
    """Retorna els fluxos de treball filtrats per estat o tipus de trigger."""
    conn = get_db_connection()
    c = conn.cursor()
    query = "SELECT * FROM workflows WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status.strip())
    if trigger_type:
        query += " AND trigger_type = ?"
        params.append(trigger_type.strip())
    query += " ORDER BY id DESC"
    
    c.execute(query, params)
    rows = []
    for r in c.fetchall():
        d = dict(r)
        for f in ["trigger_condition", "action_config", "context_data"]:
            if d.get(f):
                try:
                    d[f] = json.loads(d[f])
                except Exception:
                    d[f] = {}
            else:
                d[f] = {}
        rows.append(d)
    conn.close()
    return rows

def db_get_workflow(workflow_id: int) -> dict:
    """Retorna un flux de treball per id amb els seus camps JSON deserialitzats."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for f in ["trigger_condition", "action_config", "context_data"]:
        if d.get(f):
            try:
                d[f] = json.loads(d[f])
            except Exception:
                d[f] = {}
        else:
            d[f] = {}
    return d

def db_update_workflow(workflow_id: int, status: str = None, context_update: dict = None, result_summary: str = None):
    """Actualitza l'estat o context d'un flux existent."""
    conn = get_db_connection()
    c = conn.cursor()
    
    updates = ["updated_at = CURRENT_TIMESTAMP"]
    params = []
    
    if status:
        updates.append("status = ?")
        params.append(status)
    if result_summary is not None:
        updates.append("result_summary = ?")
        params.append(result_summary)
        
    if context_update:
        c.execute("SELECT context_data FROM workflows WHERE id = ?", (workflow_id,))
        row = c.fetchone()
        current_ctx = {}
        if row and row["context_data"]:
            try:
                current_ctx = json.loads(row["context_data"])
            except Exception:
                current_ctx = {}
        current_ctx.update(context_update)
        updates.append("context_data = ?")
        params.append(json.dumps(current_ctx, ensure_ascii=False))
        
    params.append(workflow_id)
    sql = f"UPDATE workflows SET {', '.join(updates)} WHERE id = ?"
    c.execute(sql, params)
    conn.commit()
    conn.close()

def db_add_workflow_log(workflow_id: int, event_type: str, detail: str):
    """Afegeix una entrada a l'auditoria del flux."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO workflow_logs (workflow_id, event_type, detail) VALUES (?, ?, ?)",
        (workflow_id, event_type.strip(), detail.strip())
    )
    conn.commit()
    conn.close()

def db_get_workflow_logs(workflow_id: int) -> list:
    """Retorna l'historial de logs d'un flux determinat."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, workflow_id, event_type, detail, created_at FROM workflow_logs WHERE workflow_id = ? ORDER BY id ASC",
        (workflow_id,)
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def db_get_analytics_stats() -> dict:
    """Calcula mètriques i estadístiques globals per a la memòria i defensa del TFG."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Tasques
    c.execute("SELECT status, priority, count(*) as cnt FROM tasks GROUP BY status, priority")
    task_rows = c.fetchall()
    total_tasks = 0
    completed_tasks = 0
    pending_tasks = 0
    by_priority = {"alta": 0, "mitjana": 0, "baixa": 0}
    for r in task_rows:
        cnt = r["cnt"]
        total_tasks += cnt
        st = r["status"].lower()
        if st == "completada":
            completed_tasks += cnt
        else:
            pending_tasks += cnt
        prio = r["priority"].lower()
        if prio in by_priority:
            by_priority[prio] += cnt
            
    # 2. Esdeveniments d'agenda
    c.execute("SELECT count(*) as total, sum(CASE WHEN title LIKE '%[Focus]%' THEN 1 ELSE 0 END) as focus_cnt FROM events")
    ev_row = c.fetchone()
    total_events = ev_row["total"] if ev_row else 0
    focus_events = ev_row["focus_cnt"] or 0 if ev_row else 0
    
    # 3. Correus i acadèmics UdG
    c.execute("SELECT count(*) as total, sum(CASE WHEN is_read = 1 OR sender LIKE '%udg.edu%' OR sender LIKE '%moodle%' THEN 1 ELSE 0 END) as analyzed_cnt FROM emails")
    em_row = c.fetchone()
    total_emails = em_row["total"] if em_row else 0
    analyzed_emails = em_row["analyzed_cnt"] or 0 if em_row else 0
    
    # 4. Fluxos asíncrons
    c.execute("SELECT count(*) as total, sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_wf, sum(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_wf FROM workflows")
    wf_row = c.fetchone()
    total_wf = wf_row["total"] if wf_row else 0
    completed_wf = wf_row["completed_wf"] or 0 if wf_row else 0
    pending_wf = wf_row["pending_wf"] or 0 if wf_row else 0
    
    # 5. Missatges de xat totals
    c.execute("SELECT count(*) as total_msgs, count(DISTINCT session_id) as total_sessions FROM chat_messages")
    chat_row = c.fetchone()
    total_msgs = chat_row["total_msgs"] if chat_row else 0
    total_sessions = chat_row["total_sessions"] if chat_row else 0
    
    conn.close()
    
    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0
    wf_rate = round((completed_wf / total_wf * 100), 1) if total_wf > 0 else 0.0
    
    return {
        "tasks": {
            "total": total_tasks,
            "total_tasks": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "completion_rate": completion_rate,
            "by_priority": by_priority
        },
        "calendar": {
            "total_events": total_events,
            "focus_sessions": focus_events
        },
        "focus_sessions": {
            "total_sessions": focus_events
        },
        "emails_udg": {
            "total_emails": total_emails,
            "analyzed_emails": analyzed_emails
        },
        "udg_emails": {
            "total": total_emails,
            "emails_analyzed": analyzed_emails
        },
        "workflows": {
            "total": total_wf,
            "total_workflows": total_wf,
            "completed": completed_wf,
            "successful": completed_wf,
            "active": pending_wf,
            "success_rate": wf_rate
        },
        "chat_sessions": {
            "total_sessions": total_sessions,
            "total_messages": total_msgs
        },
        "interactions": {
            "total_messages": total_msgs,
            "sessions_count": total_sessions
        }
    }

# Inicialitzar la base de dades
init_db()
db_ensure_sample_udg_emails()
