from flask import Flask, jsonify
from flask_mail import Mail, Message
from flask_cors import CORS
from app.routers.classgojp.api import api_blueprint  as api_classgojp
from config import Config  # Import Config class from config.py
from db import db_use  # Import the SQLAlchemy instance
from app.mail import mail

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'mail.polaris.my.id'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'noreply@polaris.my.id'
app.config['MAIL_PASSWORD'] = 'sherlock666'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@polaris.my.id'
# app.config['MAIL_DEBUG'] = True

mail.init_app(app)

# Set up database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
db_use.init_app(app)  # Initialize the SQLAlchemy instance with the Flask app

# Define CORS settings
CORS(app, resources=app.config['CORS_SETTINGS'])


# Register Blueprints
app.register_blueprint(api_classgojp, url_prefix='/classgojp')  # Register the auth Blueprint

# Simple test route
@app.route('/', methods=['GET'])
def get_test0():
    return jsonify({"cat": "cat not found"})


@app.route('/email', methods=['GET'])
def get_test_email_test():
    try:
        msg = Message(
            subject='Test Email lagi',
            sender='noreply@polaris.my.id',
            recipients=['x.setyori@gmail.com'],
            body='Hello, this is a test email lagi.'
        )
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        print(f'Error: {e}')
        return str(e), 500


if __name__ == "__main__":  
    app.run()
