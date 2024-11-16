import uuid
import hashlib
import random
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from db import db_use  # Import SQLAlchemy instance
from datetime import datetime

auth_blueprint = Blueprint('auth', __name__)
address_storage = 'https://classgojp-file.polaris.my.id/'

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

    # Insert the new user's profile into the user_profiles table
    insert_user_profile_query = text("""
        INSERT INTO user_profiles (user_id) 
        VALUES (:user_id)
    """)
    db_use.session.execute(insert_user_profile_query, {
        "user_id": user_id
    })

    # Retrieve the inserted user data to return as response
    result = db_use.session.execute(
        text("SELECT user_id, full_name, concat( :address_storage ,profile_pic) as profile_pic, role FROM users WHERE user_id = :user_id"),
        {"user_id": user_id, "address_storage": address_storage}
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
    query = text("SELECT user_id, full_name, concat( :address_storage ,profile_pic) as profile_pic, role FROM users WHERE email = :email AND password = :password")
    result = db_use.session.execute(query, {"email": email, "password": hashed_password, "address_storage": address_storage}).fetchone()

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

@auth_blueprint.route('/get_list_days_hours', methods=['GET'])
def get_list_days_hours():
    query_hours = text("SELECT * FROM hour_mapping WHERE is_deleted = false order by id")
    result_hours = db_use.session.execute(query_hours).mappings().all()  # Retrieve all rows with .mappings()

    query_days = text("SELECT * FROM day_mapping WHERE is_deleted = false order by id")
    result_days = db_use.session.execute(query_days).mappings().all()  # Retrieve all rows with .mappings()
    
    if not result_hours or not result_days:
        return jsonify({
                "status": False,
                "status_code": 401,
                "message": "No hours found",
                "data": None
            }), 401
    
    # Convert each row to a dictionary and prepare the response as a list
    hours = [dict(row) for row in result_hours]
    days = [dict(row) for row in result_days]
    
    return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Login successful",
             "data": {
                        "hours": hours,
                        "days": days
                    }
        })

@auth_blueprint.route('/load_weekly_schedule_template', methods=['GET'])
def load_weekly_schedule_template():
    # Get the user_id from the request arguments
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "user_id is required",
            "data": None
        }), 400

    # Query to select schedule templates for the specified user
    query = text("SELECT user_id, day_id as day, hour_id as hour FROM weekly_schedule_template WHERE is_deleted = false AND user_id = :user_id ORDER BY id")
    result = db_use.session.execute(query, {"user_id": user_id}).mappings().all()

    # Format the result as a list of dictionaries
    schedule_templates = [dict(row) for row in result]

    query_hours = text("SELECT * FROM hour_mapping WHERE is_deleted = false order by id")
    result_hours = db_use.session.execute(query_hours).mappings().all()  # Retrieve all rows with .mappings()

    query_days = text("SELECT * FROM day_mapping WHERE is_deleted = false order by id")
    result_days = db_use.session.execute(query_days).mappings().all()  # Retrieve all rows with .mappings()

    hours = [dict(row) for row in result_hours]
    days = [dict(row) for row in result_days]
    # Return the schedule templates in JSON format
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Schedule templates loaded successfully",
        "data": {   "schedule_templates": schedule_templates
                ,  "hours": hours
                ,  "days": days
        }
    }), 200

@auth_blueprint.route('/save_weekly_schedule_template', methods=['POST'])
def save_weekly_schedule_template():
    data = request.get_json()
    user_id = data.get("user_id")
    selected_times = data.get("selectedTimes")  # Array of objects, e.g., [{'day': 1, 'time': 8}, ...]

    if not user_id or not selected_times:
        return jsonify({"status": False, "message": "User ID and selected times are required"}), 400

    try:
        # Clear existing records for the user (soft delete) if you want to replace the old template
        delete_query = text("UPDATE weekly_schedule_template SET is_deleted = true WHERE user_id = :user_id")
        db_use.session.execute(delete_query, {"user_id": user_id})
        
        # Insert new schedule entries
        for selection in selected_times:
            day_id = selection.get("day")
            hour_id = selection.get("hour")
            duration = selection.get("duration", 1)  # Default duration if not provided

            insert_query = text("""
                INSERT INTO weekly_schedule_template (user_id, day_id, hour_id, duration, created_at, updated_at)
                VALUES (:user_id, :day_id, :hour_id, :duration, :created_at, :updated_at)
            """)
            db_use.session.execute(insert_query, {
                "user_id": user_id,
                "day_id": day_id,
                "hour_id": hour_id,
                "duration": duration,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })

        # Commit the transaction
        db_use.session.commit()

        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Weekly schedule template saved successfully"
        }), 200

    except Exception as e:
        db_use.session.rollback()
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": "An error occurred while saving the schedule",
            "error": str(e)
        }), 500
    
@auth_blueprint.route('/get_schedule_teacher', methods=['GET'])
def get_schedule_teacher():
    teacher_id = request.args.get('teacher_id')
    student_id = request.args.get('student_id')
    formatted_date = request.args.get('formattedDate')  # might need this later
    day_of_week = request.args.get('dayOfWeek')
    show_unavailable = request.args.get('showUnavailable')

    # Check for missing parameters
    if not teacher_id or not day_of_week or not formatted_date :
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameters",
            "data": None
        }), 400

    # check day_id
    query_day_id = text("SELECT id FROM day_mapping WHERE day_en = :day_of_week AND is_deleted = false")
    day_id_result = db_use.session.execute(query_day_id, {"day_of_week": day_of_week}).fetchone()
    

    if not day_id_result:
        return jsonify({
            "status": False,
            "status_code": 404,
            "message": "Days not found",
            "data": None
        }), 404
    
    day_id = day_id_result.id

    # Query the database for the schedule
    query = text("""
        select 	:teacher_id teacher_id, 
                :formatted_date as date, 
                dm.day_en as day,
                hm.id as hm_id, 
                hm.hour_ampm as time, 
                hm.hour_24,
                booked_data.course_id,
                CASE
                    WHEN booked_data.status is not null THEN booked_data.status
                    WHEN unavail_data.status is not null and :show_unavailable = true THEN unavail_data.status
                    WHEN avail_data.status is not null THEN avail_data.status
                    ELSE ''
                end status,
                coalesce(booked_data.member_slots , 0) as member_slots,
                coalesce(booked_data.count_member,0) as count_member, 
                CASE
                    WHEN booked_data.member_status is not null then true
                    ELSE false
                end participant
        from hour_mapping hm
        -- left join dengan course yg status nya sudah di booked
        left join 	(
                        select :teacher_id teacher_id, :formatted_date as date,  hm.id ,  hm.hour_ampm , hm.hour_24 , 'Booked' status, c.member_slots, ce_count.count_member, ce.status as member_status, cs.course_id
                        from hour_mapping hm 
                        -- inner join dengan course_schedules, untuk memastikan hari dan jam nya match dengan query
                        inner join course_schedules as cs
                            on cs.date = :formatted_date
                            and cs.hour_id = hm.id
                            and cs.is_deleted = FALSE 
                        -- inner join dengan courses untuk dapat id course nya, yg bakal di pake di query course_enrollments
                        inner join courses as c 	
                            on cs.course_id = c.id 
                            and c.teacher_id = :teacher_id
                            and c.is_deleted = FALSE 
                        -- left join dengan course_enrollments untuk dapat berapa member sih yg udah join di class ini
                        left join 	(	select ce.course_id, count(user_id) as count_member
                                        from course_enrollments as ce
                                        where ce.status = 'active'
                                        and ce.is_deleted = false
                                        group by ce.course_id
                                    ) as ce_count
                            on c.id = ce_count.course_id
                        -- left join dengan course_enrollments untuk dapat sebenarnya aku udah salah satu orang yg join class ini atau enggak
                        left join course_enrollments ce
                            on ce.course_id = c.id 
                            and ce.user_id = :student_id
                            and ce.is_deleted = false
                        where cs.hour_id is not null
                    ) as booked_data
        on booked_data.id = hm.id
        -- inner join dengan course yg status nya unavailable yg di set oleh teacher di table unavailable_schedules
        left join 	(
                        select :teacher_id teacher_id, :formatted_date as date,  hm.id ,  hm.hour_ampm , hm.hour_24 , 'Unavailable' status
                        from hour_mapping hm 
                        inner join unavailable_schedules us 
                            on us.date = :formatted_date
                            and us.hour_id = hm.id 
                            and us.teacher_id = :teacher_id
                            and us.is_deleted = FALSE 
                        where us.hour_id is not null
                    ) as unavail_data
        on unavail_data.id = hm.id
        -- left join dengan course yg status nya available yg di set oleh teacher di table weekly_schedule_template
        left join 	(
                        select :teacher_id teacher_id, :formatted_date as date,  hm.id ,  hm.hour_ampm , hm.hour_24 , 'Available' status
                        from hour_mapping hm 
                        inner join day_mapping dm 
                            on dm.id = :day_id 
                        inner join weekly_schedule_template wst  
                            on wst.hour_id = hm.id 
                            and wst.user_id  = :teacher_id
                            and wst.is_deleted = FALSE 
                            and wst.day_id = dm.id 
                        where wst.hour_id is not null
                    ) as avail_data
        on avail_data.id = hm.id
        -- left join dengan 
        left join day_mapping dm 
        on dm.id = :day_id
        where booked_data.id is not null 
        or ( avail_data.id is not null and unavail_data.id is null and :show_unavailable = FALSE )
        or ( ( 	avail_data.id is not null or 
                unavail_data.id is not null
            ) 	and :show_unavailable = true
        )
        order by hm.id
    """)
    result = db_use.session.execute(query, {"teacher_id":teacher_id , "formatted_date": formatted_date, "show_unavailable":show_unavailable , "student_id": student_id, "day_id": day_id  }).mappings().all()

    query_hours = text("SELECT * FROM hour_mapping WHERE is_deleted = false order by id")
    result_hours = db_use.session.execute(query_hours).mappings().all()  # Retrieve all rows with .mappings()

    query_days = text("SELECT * FROM day_mapping WHERE is_deleted = false order by id")
    result_days = db_use.session.execute(query_days).mappings().all()  # Retrieve all rows with .mappings()
    
    if not result_hours or not result_days:
        return jsonify({
                "status": False,
                "status_code": 401,
                "message": "No hours found",
                "data": None
            }), 401
    
    # Convert each row to a dictionary and prepare the response as a list
    hours = [dict(row) for row in result_hours]
    days = [dict(row) for row in result_days]
    # Convert results to JSON-serializable format
    schedule = [dict(row) for row in result]
    
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Schedule retrieved successfully",
        "data": {"schedule" : schedule
                 ,  "hours": hours
                 ,  "days": days
                 , "day_of_week" : day_of_week
        }
    })

@auth_blueprint.route('/get_schedule_user', methods=['GET'])
def get_schedule_user():
    user_id = request.args.get('user_id')
    
    # Check for missing parameters
    if not user_id:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameters",
            "data": None
        }), 400

    # Query the database for the schedule
    query = text("""
        -- Query 1: For "learning with sensai" (student perspective)
        SELECT 
            DATE_FORMAT(cs.date, '%Y-%m-%d')  AS schedule_date,
            hm.hour_ampm AS schedule_hour,
            cs.hour_id AS hm_id,
            c.name AS course_name,
            c.type_class AS course_type,
            c.description AS course_description,
            ce.user_id AS student_user_id,
            u.full_name as teacher_name,
            'Learning with Sensai' AS criteria
        FROM course_enrollments ce
        JOIN courses c ON c.id = ce.course_id
        JOIN course_schedules cs ON cs.course_id = c.id
        JOIN hour_mapping hm on hm.id = cs.hour_id 
        left JOIN users u on u.user_id = c.teacher_id
        WHERE 
            ce.user_id = :user_id
            AND cs.date >= CURRENT_DATE
            AND cs.is_deleted = FALSE
            AND c.is_deleted = FALSE
            AND ce.is_deleted = FALSE
        UNION
        -- Query 2: For "teaching private / group" (teacher perspective)
        SELECT 
            DATE_FORMAT(cs.date, '%Y-%m-%d')  AS schedule_date,
            hm.hour_ampm AS schedule_hour,
            cs.hour_id AS hm_id,
            c.name AS course_name,
            c.type_class AS course_type,
            c.description AS course_description,
            c.teacher_id AS teacher_user_id,
            u.full_name as teacher_name,
            'Teaching Private/Group' AS criteria
        FROM courses c
        JOIN course_schedules cs ON cs.course_id = c.id
        JOIN hour_mapping hm on hm.id = cs.hour_id
        left JOIN users u on u.user_id = c.teacher_id 
        WHERE 
            c.teacher_id = :user_id
            AND cs.date >= CURRENT_DATE
            AND cs.is_deleted = FALSE
            AND c.is_deleted = FALSE
        -- Final ordering by date and hour
        ORDER BY 
            schedule_date, hm_id;
    """)
    result = db_use.session.execute(query, {"user_id":user_id}).mappings().all()

    
    # Convert results to JSON-serializable format
    schedule = [dict(row) for row in result]
    
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Schedule retrieved successfully",
        "data": {"schedule" : schedule
        }
    })


@auth_blueprint.route('/set_unavailable_schedule', methods=['POST'])
def set_unavailable_schedule():
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    date = data.get('date')  # expected format: "yyyy-mm-dd"
    hour_id = data.get('hour_id')
    set_unavailable = data.get('set_unavailable')

    # Validate required parameters
    if not teacher_id or not date or hour_id is None or set_unavailable is None:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameters",
            "data": None
        }), 400

    # Check if we're setting the time as unavailable
    if set_unavailable:
        # Insert a new record into `unavailable_schedules`
        insert_query = text("""
            INSERT INTO unavailable_schedules (teacher_id, date, hour_id, duration, status, is_deleted, created_by)
            VALUES (:teacher_id, :date, :hour_id, 1, 'Unavailable', false, :teacher_id)
        """)
        db_use.session.execute(insert_query, {
            "teacher_id": teacher_id,
            "date": date,
            "hour_id": hour_id
        })
        db_use.session.commit()
        
        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Schedule set as unavailable",
            "data": None
        }), 200

    else:
        # Update the existing record to set `is_deleted` to true (unsetting availability)
        update_query = text("""
            UPDATE unavailable_schedules
            SET is_deleted = true
            WHERE teacher_id = :teacher_id AND date = :date AND hour_id = :hour_id
        """)
        result = db_use.session.execute(update_query, {
            "teacher_id": teacher_id,
            "date": date,
            "hour_id": hour_id
        })
        db_use.session.commit()

        if result.rowcount > 0:
            return jsonify({
                "status": True,
                "status_code": 200,
                "message": "Schedule set as available",
                "data": None
            }), 200
        else:
            return jsonify({
                "status": False,
                "status_code": 404,
                "message": "No matching unavailable schedule found",
                "data": None
            }), 404
        
@auth_blueprint.route('/get_list_teachers', methods=['GET'])
def get_list_teachers():
    # SQL query to join users and user_profiles where the role is 'teacher'
    query = text("""
        SELECT 
            u.user_id as id,
            concat(:address_storage, u.profile_pic) as profile_pic,
            u.full_name AS name,
            up.location,
            'Available' as status ,
            up.description
        FROM users u
        JOIN user_profiles up ON u.user_id = up.user_id
        WHERE u.role = 'teacher'
    """)
    result = db_use.session.execute(query, {"address_storage":address_storage}).mappings().all()

    if result:
        # Convert each result row to a dictionary and return the data
        teachers = [dict(row) for row in result]
        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Teachers list retrieved successfully",
            "data": teachers
        })
    else:
        return jsonify({
            "status": False,
            "status_code": 404,
            "message": "No teachers found",
            "data": []
        }), 404
    
@auth_blueprint.route('/get_detail_teacher', methods=['GET'])
def get_detail_teacher():
    # Get the user_id from request parameters
    user_id = request.args.get('id')
    
    if not user_id:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameter 'id'",
            "data": None
        }), 400

    query = text("""
        SELECT 
            concat(:address_storage, u.profile_pic) as profile_pic,
            u.full_name AS name,
            up.location,
            up.description,
            up.about,
            up.testimonial,
            up.message
        FROM users u
        LEFT JOIN user_profiles up ON u.user_id = up.user_id
        WHERE u.user_id = :user_id
    """)
    result = db_use.session.execute(query, {"user_id": user_id, "address_storage":address_storage}).mappings().fetchone()
    
    if not result:
        return jsonify({
            "status": False,
            "status_code": 404,
            "message": "Teacher not found",
            "data": None
        }), 404
    

    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Teacher details retrieved successfully",
        "data": dict(result)
    })
    # Query to join users and user_profiles and get the specified fields
    

    

    # Convert the result to a dictionary safely
    try:
        data = dict(result)  # Using dict() to convert row object
    except TypeError:
        # Handle if result cannot be converted (e.g., result is None)
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": "Unexpected data structure returned",
            "data": None
        }), 500

    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Teacher details retrieved successfully",
        "data": user_id
    })

@auth_blueprint.route('/create_course_bystudent', methods=['POST'])
def create_course_bystudent():
    try:
        # Get parameters from request
        data = request.json
        student_id = data.get('user_id')
        teacher_id = data.get('teacher_id')
        date = data.get('date')
        hour_id = data.get('hour_id')
        type_class = data.get('type_class')
        name = data.get('name')
        member_slots = 1 # default private
        description = 'Private' # default private

        if not all([student_id, teacher_id, date, hour_id]):
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400

        # Insert into courses table
        insert_course_query = text("""
            INSERT INTO courses (created_by, teacher_id, type_class, member_slots, name, description) 
            VALUES (:student_id, :teacher_id, :type_class, :member_slots, :name, :description)
        """)
        db_use.session.execute(insert_course_query, {
            "student_id": student_id,
            "teacher_id": teacher_id,
            "type_class" : type_class,
            "member_slots": member_slots,
            "name":name,
            "description": description
        })
        db_use.session.commit()

        # Get the last inserted course_id
        course_id = db_use.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        # Insert into course_schedules table
        insert_schedule_query = text("""
            INSERT INTO course_schedules (course_id, date, hour_id)
            VALUES (:course_id, :date, :hour_id)
        """)
        db_use.session.execute(insert_schedule_query, {
            "course_id": course_id,
            "date": date,
            "hour_id": hour_id
        })
        db_use.session.commit()

        # Insert into course_enrollments table
        insert_enrollment_query = text("""
            INSERT INTO course_enrollments (course_id, user_id, status)
            VALUES (:course_id, :user_id, 'active')
        """)
        db_use.session.execute(insert_enrollment_query, {
            "course_id": course_id,
            "user_id": student_id
        })
        db_use.session.commit()

        return jsonify({
            "status": True,
            "status_code": 201,
            "message": "Course created and associated records inserted successfully",
            "data": {
                "course_id": course_id
            }
        })

    except Exception as e:
        db_use.session.rollback()
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }), 500

@auth_blueprint.route('/get_detail_course', methods=['GET'])
def get_detail_course():
    # Get the course_id from the request arguments
    course_id = request.args.get('course_id')
    
    # Validate course_id
    if not course_id:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameter: course_id",
            "data": None
        }), 400
    
    # Query to get member list
    member_query = text("""
        SELECT 
            ce.user_id, 
            u.full_name, 
            concat(:address_storage, u.profile_pic) as profile_pic,
            u.email 
        FROM course_enrollments ce
        JOIN users u ON ce.user_id = u.user_id
        WHERE ce.course_id = :course_id
          AND ce.is_deleted = false
    """)
    member_result = db_use.session.execute(member_query, {"course_id": course_id,"address_storage": address_storage}).mappings().all()
    member_list = [dict(row) for row in member_result] if member_result else []

    # Query to get course details
    course_query = text("""
        SELECT 
            c.description, 
            c.type_class, 
            c.name, 
            c.member_slots, 
            c.status,
            u.full_name,  
            c.teacher_id  
        FROM courses c
        left join users u
        on u.user_id = c.teacher_id 
        WHERE c.id = :course_id
        AND c.is_deleted = false
    """)
    course_result = db_use.session.execute(course_query, {"course_id": course_id}).mappings().fetchone()
    course_detail = dict(course_result) if course_result else {}

    # Check if data is found
    if not course_detail:
        return jsonify({
            "status": False,
            "status_code": 404,
            "message": "Course not found or deleted",
            "data": None
        }), 404

    # Return response
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Course details retrieved successfully",
        "data": {
            "course_detail": course_detail,
            "member_list": member_list
        }
    })
