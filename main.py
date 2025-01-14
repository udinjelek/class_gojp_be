from flask import Flask, request, jsonify, current_app
from flask_mail import Mail, Message
from flask_cors import CORS
from app.routers.classgojp.api import api_blueprint  as api_classgojp
from config import Config  # Import Config class from config.py
from db import db_use  # Import the SQLAlchemy instance
from app.mail import mail

app = Flask(__name__)
app.config.from_object(Config)

mail.init_app(app)

db_use.init_app(app)  # Initialize the SQLAlchemy instance with the Flask app

# Define CORS settings
CORS(app, resources=Config.CORS_SETTINGS)


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
            subject='Test Email lagi dan',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['x.setyori@gmail.com'],
            body='Hello, this is a test email lagi. how are you, are you'
        )
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        print(f'Error: {e}')
        return str(e), 500

@app.route('/emailreset', methods=['GET'])
def get_test_email_reset_test():
    try:
        tokenResetPassword ="c91297b1-34ede142"
        frontend_url = current_app.config['FRONTEND_URL']
        reset_link = f"{frontend_url}reset-password/{tokenResetPassword}"

        msg = Message(
            subject='Reset Your Password',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['x.setyori@gmail.com'],
            html=f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Reset Your Password</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                background-color: #f4f4f4;
                                margin: 0;
                                padding: 0;
                            }}
                            .container {{
                                width: 100%;
                                max-width: 600px;
                                margin: 0 auto;
                                background-color: #ffffff;
                                border-radius: 8px;
                                overflow: hidden;
                                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                            }}
                            .header {{
                                background-color: #2c3e50;
                                color: white;
                                padding: 20px;
                                text-align: center;
                            }}
                            .content {{
                                padding: 20px;
                                color: #333333;
                            }}
                            .button {{
                                background-color: #3498db;
                                color: white !important;  /* Ensure the text stays white */
                                text-decoration: none;
                                padding: 12px 20px;
                                border-radius: 4px;
                                display: inline-block;
                                margin-top: 20px;
                                font-weight: bold;
                                border: none;
                                text-align: center;
                            }}
                            .footer {{
                                text-align: center;
                                padding: 20px;
                                font-size: 12px;
                                color: #777777;
                            }}
                            .footer a {{
                                color: #3498db;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>Password Reset Request</h1>
                            </div>
                            <div class="content">
                                <p>Hi there,</p>
                                <p>We received a request to reset your password for your account. If you did not request a password reset, please ignore this email.</p>
                                <p>To reset your password, click the button below:</p>
                                <a href="{reset_link}" class="button">Reset My Password</a>
                                <p>If you have any issues, feel free to contact our support team.</p>
                                <p>Best regards, <br>IT Care Team</p>
                            </div>
                            <div class="footer">
                                <p>If you did not request a password reset, you can safely ignore this email. <br>For more help, visit <a href="https://google.com">our support page</a>.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                """
        )
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        print(f'Error: {e}')
        return str(e), 500


if __name__ == "__main__":  
    app.run()
