import uuid
import hashlib
import random
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from db import db_use  # Import SQLAlchemy instance

auth_blueprint = Blueprint('auth', __name__)

# Function to generate a shortened UUID
def generate_short_uuid():
    return str(uuid.uuid4())[:8]

def hash_password_md5(password: str) -> str:
    # Encode the password to bytes, then hash it using MD5
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def generate_random_caticon():
    # Generate a random number between 1 and 24 (inclusive)
    random_number = random.randint(1, 24)
    return f"images/default/caticon{random_number}.jpg"

# Route for creating a new user
@auth_blueprint.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    full_name = data.get('full_name')
    phone_number = data.get('phone_number')
    email = data.get('email')
    password = data.get('password')

    # Check if the email already exists in the database
    check_email_query = text("SELECT * FROM users WHERE email = :email")
    existing_user = db_use.session.execute(check_email_query, {"email": email}).mappings().fetchone()

    if existing_user:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Email already used by another user",
            "data": None
        }), 400  # Return a 400 status code for existing email

    # Generate a unique user_id, hash the password, and select a profile picture
    user_id = generate_short_uuid()
    hashed_password = hash_password_md5(password)
    profile_pic = generate_random_caticon()

    # Insert the new user into the database
    insert_user_query = text("""
        INSERT INTO users (user_id, full_name, email, phone_number, password, profile_pic) 
        VALUES (:user_id, :full_name, :email, :phone_number, :password, :profile_pic)
    """)
    db_use.session.execute(insert_user_query, {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "phone_number": phone_number,
        "password": hashed_password,
        "profile_pic": profile_pic
    })
    db_use.session.commit()

    # Retrieve the inserted user data to return as response
    result = db_use.session.execute(
        text("SELECT * FROM users WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).mappings().fetchone()

    # Convert result to a dictionary and return JSON response
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "User created successfully",
        "data": dict(result)  # Convert SQLAlchemy row to a dictionary
    })

@auth_blueprint.route("/user_login", methods=["POST"])
def user_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Hash the provided password
    hashed_password = hash_password_md5(password)
    
    # Query the database to check if email and hashed password match
    query = text("SELECT * FROM users WHERE email = :email AND password = :password")
    result = db_use.session.execute(query, {"email": email, "password": hashed_password}).fetchone()

    # Check if the result exists and convert it to a dictionary
    if result:
        # Convert to dictionary format so jsonify can handle it
        result_dict = dict(result._mapping)  # Ensure it's a dictionary

        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Login successful",
            "data": result_dict
        })
    else:
        return jsonify({
            "status": False,
            "status_code": 401,
            "message": "Invalid email or password",
            "data": None
        }), 401

# Test route for database
@auth_blueprint.route('/testdb', methods=['GET'])
def get_user_by_idx():
    params_id = '80b78ea3'
    query = text("SELECT * FROM users WHERE user_id = :id")
    result = db_use.session.execute(query, {"id": params_id}).mappings().fetchone()

    if result:
        return jsonify(dict(result))  # Convert to JSON response
    else:
        return jsonify({"error": "User not found"}), 404


# Simple test route
@auth_blueprint.route('/test', methods=['GET'])
def get_test():
    return jsonify({"error": "User not found"})
