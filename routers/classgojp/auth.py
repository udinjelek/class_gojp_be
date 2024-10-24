import uuid
import hashlib
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import get_db  # Absolute import
from pydantic import BaseModel

router = APIRouter()

# Function to generate a shortened UUID
def generate_short_uuid():
    return str(uuid.uuid4())[:8]

def hash_password_md5(password: str) -> str:
    # Encode the password to bytes, then hash it using MD5
    hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
    return hashed_password

def generate_random_caticon():
    # Generate a random number between 1 and 24 (inclusive)
    random_number = random.randint(1, 24)
    # Concatenate the random number into the string
    return f"images/default/caticon{random_number}.jpg"

# Define the request body model
class UserCreateRequest(BaseModel):
    full_name: str
    phone_number: str
    email: str
    password: str

@router.post('/create_user')
async def create_user(user: UserCreateRequest,  db: Session = Depends(get_db)):
    # Check if the email already exists in the database
    check_email_query = text("SELECT * FROM users WHERE email = :email")
    existing_user = db.execute(check_email_query, {"email": user.email}).mappings().fetchone()

    if existing_user:
        return {
            "status": False,
            "status_code": 400,
            "message": "Email already used by other",
            "data": None
        }

    # Generate a unique user_id
    user_id = generate_short_uuid()

    # Hash the password using MD5
    hashed_password = hash_password_md5(user.password)

    profile_pic = generate_random_caticon()

    # Insert the new user into the database
    insert_user_query = text("""
        INSERT INTO users (user_id, full_name, email, phone_number, password, profile_pic) 
        VALUES (:user_id, :full_name, :email, :phone_number, :password, :profile_pic)
    """)
    
    # Execute the insert query
    db.execute(insert_user_query, {
        "user_id": user_id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "password": hashed_password,  # Store the MD5 hashed password
        "profile_pic": profile_pic
    })

    # Commit the changes to the database
    db.commit()

    query = text("SELECT * FROM users WHERE user_id = :user_id")
    result = db.execute(query, {"user_id": user_id}).mappings().fetchone()
    
    return {
        "status": True,
        "status_code": 200,
        "message": "User created successfully",
        "data": dict(result)  # Return the user data in the 'data' field
    }
    return {"message": "User created successfully", "user_id": user_id}
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/user_login")
async def user_login(user: LoginRequest, db: Session = Depends(get_db)):
    # Hash the provided password
    hashed_password = hash_password_md5(user.password)
    
    # Query the database to check if email and hashed password match
    query = text("SELECT * FROM users WHERE email = :email AND password = :password")
    result = db.execute(query, {"email": user.email, "password": hashed_password}).mappings().fetchone()

    # If no result found, raise an error
    if not result:
       if not result:
        return {
            "status": False,
            "status_code": 401,
            "message": "Invalid email or password",
            "data": None
        }

    # If login successful, return some user information (excluding sensitive details)
    return {
        "status": True,
        "status_code": 200,
        "message": "Login successful",
        "data": dict(result)  # Return the user data in the 'data' field
    }

@router.get('/testdb')
async def get_user_by_idx(db: Session = Depends(get_db)):
    params_id = '80b78ea3'
    query = text("SELECT * FROM users WHERE user_id = :id ")
    result = db.execute(query, 
                        {"id": params_id}
                        ).mappings().fetchone()  # Fetch result as dictionary-like object
    
    if result:
        return dict(result)  # Convert the result to a dictionary
    else:
        return {"error": "User not found"}


# @router.get('/user')
# async def get_user_by_id(params_id: str, db: Session = Depends(get_db)):
#     if not params_id:
#         return {"error": "Missing id parameter"}, 400

#     # Use raw SQL query to fetch the user data
#     query = "SELECT * FROM users WHERE id = :id"
#     result = db.execute(query, {'id': params_id})  # Execute the query with the id parameter

#     user = result.fetchone()

#     if user:
#         return {
#             "id": user['id'],
#             "name": user['name'],
#             "email": user['email']
#         }, 200
#     else:
#         return {"error": "User not found"}, 404
    

@router.get('/test')
async def get_test():
   
        return {"error": "User not found"}

