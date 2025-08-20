from . import models 
from flask import Flask
from .config import DevConfig
from .extensions import db, migrate, login_manager
from .blueprints.auth import bp as auth_bp
from .blueprints.main import bp as main_bp

def create_app(config_class=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    return app
