from flask import Blueprint

hello_bp = Blueprint('hello', __name__, url_prefix="/api")

@hello_bp.route('/hello')
def hello():
    return {"message": "Hello from Flask!"}
