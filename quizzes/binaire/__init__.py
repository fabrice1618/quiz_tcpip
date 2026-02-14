from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify

from db import get_db
from quizzes import register_quiz
from quizzes.binaire.logic import (
    formater_donnee, format_bin,
    generer_exercice2, generer_exercice3,
    corriger, sauvegarder_resultat, charger_resultats,
)

bp = Blueprint(
    "binaire",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/binaire/static",
)

QUIZ_ID = "binaire"
TITRE = "Test info atelier - partie 1"
DESCRIPTION = "Conversions numériques et opérations logiques"
TOTAL_EXERCICES = 3


def _sk(key):
    """Clé de session namespacée."""
    return f"binaire_{key}"


register_quiz(QUIZ_ID, TITRE, DESCRIPTION, bp)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/")
def accueil():
    return render_template(
        "accueil.html",
        quiz_id=QUIZ_ID,
        titre=TITRE,
        description=DESCRIPTION,
    )


@bp.route("/start", methods=["POST"])
def start():
    # Nettoyer les clés de ce quiz
    for key in list(session.keys()):
        if key.startswith("binaire_"):
            session.pop(key)

    session[_sk("nom")] = request.form.get("nom", "").strip()
    session[_sk("prenom")] = request.form.get("prenom", "").strip()
    session[_sk("ex2_data")] = generer_exercice2()
    session[_sk("ex3_operands")] = generer_exercice3()

    # Vérifier le mode test
    conn = get_db()
    row = conn.execute(
        "SELECT mode, ouvert FROM quiz_config WHERE quiz_id=?", (QUIZ_ID,)
    ).fetchone()
    conn.close()

    if row and row["mode"] == "test" and not row["ouvert"]:
        return redirect(url_for(".attente"))

    return redirect(url_for(".exercice", n=1))


@bp.route("/attente")
def attente():
    if _sk("nom") not in session:
        return redirect(url_for(".accueil"))
    return render_template(
        "salle_attente.html",
        quiz_id=QUIZ_ID,
        titre=TITRE,
        nom=session.get(_sk("nom"), ""),
        prenom=session.get(_sk("prenom"), ""),
    )


@bp.route("/attente/status")
def attente_status():
    conn = get_db()
    row = conn.execute(
        "SELECT mode, ouvert FROM quiz_config WHERE quiz_id=?", (QUIZ_ID,)
    ).fetchone()
    conn.close()
    if row and (row["mode"] == "entrainement" or row["ouvert"]):
        return jsonify(ouvert=True)
    return jsonify(ouvert=False)


@bp.route("/exercice/<int:n>", methods=["GET", "POST"])
def exercice(n):
    if n not in (1, 2, 3):
        return redirect(url_for(".accueil"))

    if _sk("nom") not in session:
        return redirect(url_for(".accueil"))

    # Garde : vérifier le mode test
    conn = get_db()
    row = conn.execute(
        "SELECT mode, ouvert FROM quiz_config WHERE quiz_id=?", (QUIZ_ID,)
    ).fetchone()
    conn.close()
    if row and row["mode"] == "test" and not row["ouvert"]:
        return redirect(url_for(".attente"))

    if request.method == "POST":
        reponses = session.get(_sk("reponses"), {})
        for key, value in request.form.items():
            if key != "direction":
                reponses[key] = value
        session[_sk("reponses")] = reponses

        if request.form.get("direction") == "prev" and n > 1:
            return redirect(url_for(".exercice", n=n - 1))
        elif n < 3:
            return redirect(url_for(".exercice", n=n + 1))
        else:
            return redirect(url_for(".confirmation"))

    reponses = session.get(_sk("reponses"), {})
    kwargs = {
        "n": n,
        "reponses": reponses,
        "titre": TITRE,
        "total_exercices": TOTAL_EXERCICES,
        "nom": session.get(_sk("nom"), ""),
        "prenom": session.get(_sk("prenom"), ""),
        "quiz_id": QUIZ_ID,
    }

    if n == 2:
        ex2_data = session.get(_sk("ex2_data"), [])
        kwargs["lignes"] = [
            (row, col, formater_donnee(val, col)) for row, col, val in ex2_data
        ]
    elif n == 3:
        op = session.get(_sk("ex3_operands"), {})
        kwargs["ex3_a"] = format_bin(op.get("a", 0))
        kwargs["ex3_b"] = format_bin(op.get("b", 0))

    return render_template(f"binaire/exercice{n}.html", **kwargs)


@bp.route("/confirmation")
def confirmation():
    if _sk("nom") not in session:
        return redirect(url_for(".accueil"))

    if _sk("code") in session:
        return render_template(
            "confirmation.html",
            code=session[_sk("code")],
            nom=session.get(_sk("nom"), ""),
            prenom=session.get(_sk("prenom"), ""),
        )

    reponses = session.get(_sk("reponses"), {})
    ex2_data = session.get(_sk("ex2_data"), [])
    ex3_operands = session.get(_sk("ex3_operands"), {})

    scores, total_c, total_q = corriger(reponses, ex2_data, ex3_operands)

    enonce = {"ex2_data": ex2_data, "ex3_operands": ex3_operands}
    code = sauvegarder_resultat(
        session[_sk("nom")], session[_sk("prenom")],
        enonce, reponses, scores, total_c, total_q,
    )
    session[_sk("code")] = code

    return render_template(
        "confirmation.html",
        code=code,
        nom=session.get(_sk("nom"), ""),
        prenom=session.get(_sk("prenom"), ""),
    )


@bp.route("/resultats")
def resultats():
    tous = charger_resultats()
    return render_template("binaire/resultats.html", resultats=tous)
