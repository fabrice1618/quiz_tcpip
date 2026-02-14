from flask import Blueprint, render_template, request, session, redirect, url_for

import config
from db import get_db
from quizzes import QUIZ_REGISTRY

main_bp = Blueprint("main", __name__)
admin_bp = Blueprint("admin", __name__, template_folder="templates/admin")


# ---------------------------------------------------------------------------
# Main — Page d'accueil
# ---------------------------------------------------------------------------

@main_bp.route("/")
def index():
    conn = get_db()
    configs = {}
    for row in conn.execute("SELECT quiz_id, mode, ouvert FROM quiz_config").fetchall():
        configs[row["quiz_id"]] = {"mode": row["mode"], "ouvert": row["ouvert"]}
    conn.close()

    quizzes = []
    for quiz_id, meta in QUIZ_REGISTRY.items():
        cfg = configs.get(quiz_id, {"mode": "entrainement", "ouvert": 0})
        quizzes.append({
            "id": quiz_id,
            "titre": meta["titre"],
            "description": meta["description"],
            "mode": cfg["mode"],
            "ouvert": cfg["ouvert"],
        })
    return render_template("index.html", quizzes=quizzes)


# ---------------------------------------------------------------------------
# Admin — Gestion des quiz
# ---------------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin.dashboard"))
        return render_template("login.html", error="Mot de passe incorrect")
    return render_template("login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("main.index"))


@admin_bp.route("/")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin.login"))

    conn = get_db()
    configs = {}
    for row in conn.execute("SELECT quiz_id, mode, ouvert FROM quiz_config").fetchall():
        configs[row["quiz_id"]] = {"mode": row["mode"], "ouvert": row["ouvert"]}
    conn.close()

    quizzes = []
    for quiz_id, meta in QUIZ_REGISTRY.items():
        cfg = configs.get(quiz_id, {"mode": "entrainement", "ouvert": 0})
        quizzes.append({
            "id": quiz_id,
            "titre": meta["titre"],
            "description": meta["description"],
            "mode": cfg["mode"],
            "ouvert": cfg["ouvert"],
        })
    return render_template("dashboard.html", quizzes=quizzes)


@admin_bp.route("/toggle/<quiz_id>/<action>", methods=["POST"])
def toggle(quiz_id, action):
    if not session.get("admin"):
        return redirect(url_for("admin.login"))

    conn = get_db()
    if action == "mode":
        row = conn.execute(
            "SELECT mode FROM quiz_config WHERE quiz_id=?", (quiz_id,)
        ).fetchone()
        if row:
            new_mode = "test" if row["mode"] == "entrainement" else "entrainement"
            conn.execute(
                "UPDATE quiz_config SET mode=?, ouvert=0 WHERE quiz_id=?",
                (new_mode, quiz_id),
            )
    elif action == "ouvert":
        row = conn.execute(
            "SELECT ouvert FROM quiz_config WHERE quiz_id=?", (quiz_id,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE quiz_config SET ouvert=? WHERE quiz_id=?",
                (1 - row["ouvert"], quiz_id),
            )
    conn.commit()
    conn.close()
    return redirect(url_for("admin.dashboard"))
