from flask import Blueprint, jsonify

hello_bp = Blueprint('hello_bp', __name__, url_prefix='/api')

@hello_bp.route("/")
def hello():
    return jsonify({"message": "Hello from Flask Blueprint"})
