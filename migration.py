#!/usr/bin/env python3
"""Migration one-shot : resultats.json -> resultats.db"""
import json, sqlite3, os

for quiz in ("quiz_binaire", "quiz_reseau"):
    json_path = os.path.join(quiz, "resultats.json")
    db_path = os.path.join(quiz, "resultats.db")
    if not os.path.exists(json_path):
        print(f"  {json_path} non trouvé, ignoré")
        continue
    with open(json_path, "r", encoding="utf-8") as f:
        resultats = json.load(f)
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS resultats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL, prenom TEXT NOT NULL,
        date TEXT NOT NULL,
        score_total_correct INTEGER, score_total_total INTEGER,
        donnees TEXT NOT NULL
    )""")
    for r in resultats:
        st = r.get("score_total", {})
        conn.execute(
            "INSERT OR IGNORE INTO resultats (code, nom, prenom, date, score_total_correct, score_total_total, donnees) VALUES (?,?,?,?,?,?,?)",
            (r["code"], r["nom"], r["prenom"], r["date"],
             st.get("correct", 0), st.get("total", 0),
             json.dumps(r, ensure_ascii=False)),
        )
    conn.commit()
    conn.close()
    print(f"  {json_path} -> {db_path} ({len(resultats)} entrées)")
