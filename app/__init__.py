from flask import Flask, app
from flask_cors import CORS # type: ignore
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from app.cli import register_cli_commands
register_cli_commands(app)


db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db, directory=app.config.get("MIGRATIONS_DIR", "migrations"))

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # Để Alembic phát hiện models
    with app.app_context():
        from . import models  # noqa: F401

    return app
