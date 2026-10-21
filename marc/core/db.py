import os
import sqlite3
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Taula de Correus (Inbox, Sent, Drafts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        folder TEXT DEFAULT 'inbox',
        is_read INTEGER DEFAULT 0,
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

    conn.commit()

    # Si la base de dades és buida, inserim dades inicials demostratives
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        avui = datetime.now().strftime("%Y-%m-%d")
        dema = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Tasques inicials
        cursor.execute("""
        INSERT INTO tasks (title, description, due_date, priority, status)
        VALUES 
        ('Revisar la memòria inicial del TFG', 'Adaptar els objectius cap al secretari personal intel·ligent.', ?, 'alta', 'pendent'),
        ('Preparar la reunió de seguiment', 'Resumir les noves eines i la integració del panell HUD.', ?, 'mitjana', 'pendent'),
        ('Configurar credencials opcionals de correu i Telegram', 'Revisar l arxiu .env amb les claus d API.', ?, 'baixa', 'pendent')
        """, (avui, avui, dema))

        # Esdeveniments inicials
        cursor.execute("""
        INSERT INTO events (title, description, start_time, end_time, location)
        VALUES 
        ('Reunió de seguiment del TFG', 'Comentar l enfocament d assistent executiu i calendari.', ? || ' 16:30', ? || ' 17:30', 'Despatx Tutor / Online'),
        ('Sessió de planificació setmanal', 'Revisió de tasques pendents i prioritats.', ? || ' 11:00', ? || ' 11:45', 'Sala d reunions')
        """, (avui, avui, dema, dema))

        # Correus inicials
        cursor.execute("""
        INSERT INTO emails (sender, recipient, subject, body, folder, is_read)
        VALUES 
        ('tutor.tfg@universitat.cat', 'usuari@tfg.cat', 'Revisió del nou enfocament de M.A.R.C.', 'Hola Marc, he vist la proposta de canvi cap a secretari executiu i em sembla excel·lent. Té molt més sentit pràctic. Ens veiem a la reunió d avui per comentar-ho.', 'inbox', 0),
        ('equip.projecte@startup.com', 'usuari@tfg.cat', 'Actualització de fites setmanals', 'Bon dia, et passem el resum de les fites pendents d aquesta setmana per poder coordinar agendes.', 'inbox', 0)
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
def db_add_event(title: str, start_time: str, end_time: str = None, location: str = "", description: str = ""):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (title, description, start_time, end_time, location) VALUES (?, ?, ?, ?, ?)",
        (title.strip(), description.strip(), start_time.strip(), end_time.strip() if end_time else None, location.strip())
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

def db_add_email(sender: str, recipient: str, subject: str, body: str, folder: str = "inbox", is_read: int = 0):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO emails (sender, recipient, subject, body, folder, is_read) VALUES (?, ?, ?, ?, ?, ?)",
        (sender.strip(), recipient.strip(), subject.strip(), body.strip(), folder, is_read)
    )
    conn.commit()
    email_id = c.lastrowid
    conn.close()
    return email_id

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

# Inicialitzar la base de dades al carregar el mòdul
init_db()
