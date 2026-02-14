#!/usr/bin/env python3
"""Lister toutes les soumissions des quiz."""

import json
import os
import sqlite3
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "resultats.db")


def main():
    if not os.path.exists(DB_PATH):
        print(f"Base introuvable : {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT quiz_id, donnees FROM resultats ORDER BY quiz_id, date"
    ).fetchall()
    conn.close()

    W_QUIZ, W_NOM, W_PRE, W_CODE, W_DATE, W_SCORE = 8, 14, 14, 6, 16, 7

    print(
        f"  {'Quiz':<{W_QUIZ}} {'Nom':<{W_NOM}} {'Prénom':<{W_PRE}} "
        f"{'Code':<{W_CODE}} {'Date':<{W_DATE}} {'Score':>{W_SCORE}}"
    )
    print(
        f"  {'─'*W_QUIZ} {'─'*W_NOM} {'─'*W_PRE} "
        f"{'─'*W_CODE} {'─'*W_DATE} {'─'*W_SCORE}"
    )

    total = 0
    for row in rows:
        r = json.loads(row["donnees"])
        sc = r.get("score_total", {})
        score = f"{sc.get('correct', '?')}/{sc.get('total', '?')}"
        dt = datetime.fromisoformat(r["date"]).strftime("%d-%m-%Y %H:%M")
        print(
            f"  {row['quiz_id']:<{W_QUIZ}} {r['nom']:<{W_NOM}} {r['prenom']:<{W_PRE}} "
            f"{r['code']:<{W_CODE}} {dt:<{W_DATE}} {score:>{W_SCORE}}"
        )
        total += 1

    print(f"\n  {total} soumission(s)")


if __name__ == "__main__":
    main()
