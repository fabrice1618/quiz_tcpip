#!/usr/bin/env python3
"""Lister toutes les soumissions des deux quiz."""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

QUIZ = [
    ("binaire", os.path.join(BASE, "quiz_binaire", "resultats.json")),
    ("reseau",  os.path.join(BASE, "quiz_reseau",  "resultats.json")),
]


def charger(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
