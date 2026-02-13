#!/usr/bin/env python3
"""Lister toutes les soumissions des deux quiz."""

import json
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

QUIZ = [
    ("binaire", os.path.join(BASE, "quiz_binaire", "resultats.db")),
    ("reseau",  os.path.join(BASE, "quiz_reseau",  "resultats.db")),
]


def charger(db_path):
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT donnees FROM resultats ORDER BY date").fetchall()
    conn.close()
    return [json.loads(row["donnees"]) for row in rows]


def main():
    W_QUIZ, W_NOM, W_PRE, W_CODE, W_DATE, W_SCORE = 8, 14, 14, 6, 19, 7

    print(
        f"  {'Quiz':<{W_QUIZ}} {'Nom':<{W_NOM}} {'Prénom':<{W_PRE}} "
        f"{'Code':<{W_CODE}} {'Date':<{W_DATE}} {'Score':>{W_SCORE}}"
    )
    print(
        f"  {'─'*W_QUIZ} {'─'*W_NOM} {'─'*W_PRE} "
        f"{'─'*W_CODE} {'─'*W_DATE} {'─'*W_SCORE}"
    )

    total = 0
    for nom_quiz, path in QUIZ:
        resultats = charger(path)
        for r in resultats:
            sc = r.get("score_total", {})
            score = f"{sc.get('correct', '?')}/{sc.get('total', '?')}"
            print(
                f"  {nom_quiz:<{W_QUIZ}} {r['nom']:<{W_NOM}} {r['prenom']:<{W_PRE}} "
                f"{r['code']:<{W_CODE}} {r['date']:<{W_DATE}} {score:>{W_SCORE}}"
            )
            total += 1

    print(f"\n  {total} soumission(s)")


if __name__ == "__main__":
    main()
