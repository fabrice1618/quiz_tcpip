import os
import random
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "resultats.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS resultats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id TEXT NOT NULL,
        code TEXT NOT NULL,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        date TEXT NOT NULL,
        score_total_correct INTEGER,
        score_total_total INTEGER,
        donnees TEXT NOT NULL,
        UNIQUE(quiz_id, code)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS quiz_config (
        quiz_id TEXT PRIMARY KEY,
        mode TEXT NOT NULL DEFAULT 'entrainement',
        ouvert INTEGER NOT NULL DEFAULT 0
    )""")
    conn.commit()
    conn.close()


def generer_code(conn, quiz_id):
    """Genere un code unique de 6 chiffres pour un quiz donne."""
    for _ in range(100):
        code = f"{random.randint(0, 999999):06d}"
        row = conn.execute(
            "SELECT 1 FROM resultats WHERE quiz_id=? AND code=?",
            (quiz_id, code),
        ).fetchone()
        if row is None:
            return code
    raise RuntimeError("Impossible de générer un code unique")
