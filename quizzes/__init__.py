from db import get_db

QUIZ_REGISTRY = {}


def register_quiz(quiz_id, titre, description, blueprint):
    QUIZ_REGISTRY[quiz_id] = {
        "titre": titre,
        "description": description,
        "blueprint": blueprint,
    }


def register_all(app):
    from quizzes.binaire import bp as bp_binaire
    from quizzes.reseau import bp as bp_reseau

    # Ne rien faire de plus avec bp_binaire/bp_reseau ici,
    # register_quiz est appele dans chaque __init__.py

    conn = get_db()
    for quiz_id in QUIZ_REGISTRY:
        conn.execute(
            "INSERT OR IGNORE INTO quiz_config (quiz_id) VALUES (?)",
            (quiz_id,),
        )
    conn.commit()
    conn.close()

    for quiz_id, meta in QUIZ_REGISTRY.items():
        app.register_blueprint(meta["blueprint"], url_prefix=f"/{quiz_id}")
