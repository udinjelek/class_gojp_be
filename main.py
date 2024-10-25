from flask import Flask, jsonify
from flask_cors import CORS
from routers.classgojp.auth import auth_blueprint  # Updated for Flask Blueprints
from config import Config  # Import Config class from config.py
from db import db_use  # Import the SQLAlchemy instance

app = Flask(__name__)

# Set up database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
db_use.init_app(app)  # Initialize the SQLAlchemy instance with the Flask app

# Define CORS settings
CORS(app, resources={r"/classgojp/*": {"origins": [
    "http://localhost:4001",
    "http://127.0.0.1:4001",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://class-gojp.polaris.my.id",
]}})

# Register Blueprints
app.register_blueprint(auth_blueprint, url_prefix='/classgojp')  # Register the auth Blueprint

# Simple test route
@app.route('/', methods=['GET'])
def get_test0():
    return jsonify({"cat": "cat not found"})

if __name__ == "__main__":
    app.run()
