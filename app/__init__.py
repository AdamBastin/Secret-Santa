import os
from pathlib import Path

from flask import Flask

from .database import close_db, init_db
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app_root = Path(app.root_path)
    instance_path = Path(app.instance_path)
    app.config.from_mapping(
        DATABASE=instance_path / "secret_santa.sqlite",
        QUESTIONNAIRE_PATH=app_root / "config" / "questionnaire.json",
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-change-me"),
    )
    if test_config:
        app.config.update(test_config)

    instance_path.mkdir(parents=True, exist_ok=True)
    init_db(app)

    app.register_blueprint(bp)
    app.teardown_appcontext(close_db)

    return app
