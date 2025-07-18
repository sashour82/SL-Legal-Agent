from .routes.legal_api import legal_bp
from .routes.hello import hello_bp

def register_blueprints(app):
    app.register_blueprint(legal_bp)
    app.register_blueprint(hello_bp)