from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify

from db import get_db
from quizzes import register_quiz
from quizzes.reseau.logic import (
    MACHINES, EX2_DEVICES, EX2_GIVEN,
    corriger_ex1, corriger_ex2,
    sauvegarder_resultat, charger_resultats,
)

bp = Blueprint(
    "reseau",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/reseau/static",
)

QUIZ_ID = "reseau"
TITRE = "Test info atelier - partie 2"
DESCRIPTION = "Adressage IP et routage"
TOTAL_EXERCICES = 2


def _sk(key):
    """Clé de session namespacée."""
    return f"reseau_{key}"


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
        if key.startswith("reseau_"):
            session.pop(key)

    session[_sk("nom")] = request.form.get("nom", "").strip()
    session[_sk("prenom")] = request.form.get("prenom", "").strip()

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
    if n not in (1, 2):
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
        elif n < 2:
            return redirect(url_for(".exercice", n=n + 1))
        else:
            return redirect(url_for(".confirmation"))

    reponses = session.get(_sk("reponses"), {})
    kwargs = {
        "n": n,
        "reponses": reponses,
        "total_exercices": TOTAL_EXERCICES,
        "titre": TITRE,
        "nom": session.get(_sk("nom"), ""),
        "prenom": session.get(_sk("prenom"), ""),
        "quiz_id": QUIZ_ID,
    }

    if n == 1:
        kwargs["machines"] = MACHINES
    elif n == 2:
        kwargs["devices"] = EX2_DEVICES
        kwargs["given"] = EX2_GIVEN

    return render_template(f"reseau/exercice{n}.html", **kwargs)


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

    scores_ex1 = corriger_ex1(reponses)
    scores_ex2 = corriger_ex2(reponses)

    scores = {"ex1": scores_ex1, "ex2": scores_ex2}
    code = sauvegarder_resultat(
        session[_sk("nom")], session[_sk("prenom")], reponses, scores
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
    return render_template("reseau/resultats.html", resultats=tous)
