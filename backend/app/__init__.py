# backend/app/__init__.py

from flask import Flask
from .api import register_blueprints
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    register_blueprints(app)
    return app
