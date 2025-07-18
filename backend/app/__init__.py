# backend/app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    from .routes.hello import hello_bp
    app.register_blueprint(hello_bp)

    
    from .routes.users import users_bp
    app.register_blueprint(users_bp)
    
    from app import models

    return app
