from flask import Flask

import config
from db import init_db
from routes import main_bp, admin_bp
from quizzes import register_all


def create_app():
    application = Flask(__name__)
    application.secret_key = config.SECRET_KEY

    init_db()

    application.register_blueprint(main_bp)
    application.register_blueprint(admin_bp, url_prefix="/admin")
    register_all(application)

    return application


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
