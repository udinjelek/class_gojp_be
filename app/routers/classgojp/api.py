import uuid
import hashlib
import random
import time
import os
from flask import Blueprint, request, jsonify
from flask_mail import Message
from app.mail import mail
from sqlalchemy import text
from db import db_use  # Import SQLAlchemy instance
from datetime import datetime
from werkzeug.utils import secure_filename

api_blueprint = Blueprint('auth', __name__)
address_storage = 'https://classgojp-file.polaris.my.id/'
upload_path = '../public_html/classgojp/'
folder_profil_pic = 'images/users/'

# Function to generate a shortened UUID
def generate_short_uuid():
    return str(uuid.uuid4())[:8]

def generate_time_short_uuid():
    unix_time = int(time.time())  # Current Unix timestamp
    base36_time = base36_encode(unix_time)  # Convert timestamp to Base36
    random_uuid = str(uuid.uuid4())[:8]  # First 8 characters of UUID
    return f"{base36_time}-{random_uuid}"

def base36_encode(number):
    """Encodes an integer into a Base36 string."""
    if number < 0:
        raise ValueError("Base36 encoding only supports non-negative integers.")
    
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while number > 0:
        number, remainder = divmod(number, 36)
        result = chars[remainder] + result
    return result or "0"

def hash_password_md5(password: str) -> str:
    # Encode the password to bytes, then hash it using MD5
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def generate_random_caticon():
    # Generate a random number between 1 and 24 (inclusive)
    random_number = random.randint(1, 24)
    return f"images/default/caticon{random_number}.jpg"

# Route for creating a new user
@api_blueprint.route('/create_user', methods=['POST'])
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

@api_blueprint.route("/user_login", methods=["POST"])
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
@api_blueprint.route('/testdb', methods=['GET'])
def get_user_by_idx():
    params_id = '80b78ea3'
    query = text("SELECT * FROM users WHERE user_id = :id")
    result = db_use.session.execute(query, {"id": params_id}).mappings().fetchone()

    if result:
        return jsonify(dict(result))  # Convert to JSON response
    else:
        return jsonify({"error": "User not found"}), 404

# Simple test route
@api_blueprint.route('/test', methods=['GET'])
def get_test():
    return jsonify({"error": "User not found"})

@api_blueprint.route('/get_list_days_hours', methods=['GET'])
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

@api_blueprint.route('/load_weekly_schedule_template', methods=['GET'])
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

@api_blueprint.route('/save_weekly_schedule_template', methods=['POST'])
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
    
@api_blueprint.route('/get_schedule_teacher', methods=['GET'])
def get_schedule_teacher():
    teacher_id = request.args.get('teacher_id')
    student_id = request.args.get('student_id')
    formatted_date = request.args.get('formattedDate')  # might need this later
    day_of_week = request.args.get('dayOfWeek')
    show_unavailable_arg = request.args.get('showUnavailable')
    if show_unavailable_arg in ['false', False]:
        show_unavailable = 0
    else:
        show_unavailable = 1

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
                    WHEN booked_data.status is not null THEN 
                        case 
                            when booked_data.type != 'in session' then booked_data.status
                            else booked_data.type
                        end
                    WHEN unavail_data.status is not null and :show_unavailable = 1 THEN unavail_data.status
                    WHEN avail_data.status is not null THEN avail_data.status
                    ELSE ''
                end status,
                coalesce(booked_data.member_slots , 0) as member_slots,
                coalesce(booked_data.count_member,0) as count_member, 
                coalesce(booked_data.name,'') as name,  
                CASE
                    WHEN booked_data.member_status is not null then true
                    ELSE false
                end participant
        from hour_mapping hm
        -- left join dengan course yg status nya sudah di booked
        left join 	(
                        select :teacher_id teacher_id, :formatted_date as date,  hm.id ,  hm.hour_ampm , hm.hour_24 , 'Booked' status, c.member_slots, c.name, ce_count.count_member, ce.status as member_status, cs.type , cs.course_id
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
        where 
            :show_unavailable = 1
            or  (   :show_unavailable = 0
                     and	(  	booked_data.id is not null 
                            or 
                            (	avail_data.id is not null 
                                and unavail_data.id is null
                            )	
                )
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
                 , 'show_unavailable': show_unavailable
        }
    })

@api_blueprint.route('/get_schedule_teacher_ignore_weekly_template', methods=['GET'])
def get_schedule_teacher_ignore_weekly_template():
    teacher_id = request.args.get('teacher_id')
    formatted_date = request.args.get('formattedDate')  # might need this later
    day_of_week = request.args.get('dayOfWeek')
    show_unavailable_arg = request.args.get('showUnavailable')
    if show_unavailable_arg in ['false', False]:
        show_unavailable = 0
    else:
        show_unavailable = 1

    # Check for missing parameters
    if not teacher_id or not day_of_week or not formatted_date :
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameters",
            "data": None
        }), 400



    # Query the database for the schedule
    query = text("""
        select hm.id as hm_id, hm.*,
                case 
                    when cs.id is not null then 'Booked'
                    when us.id is not null then 'Unavailable'
                    else 'Available'
                end as status,
                case 
                    when cs.id is not null then cs.type
                    when us.id is not null then us.status
                    else 'Available'
                end as type
        from hour_mapping hm 
        left join (	select * 
                    from unavailable_schedules 
                    where date = :formatted_date
                    and teacher_id = :teacher_id
                    and is_deleted = false
                    ) as us
        on hm.id = us.hour_id
        left join (	select cs.* , c.teacher_id, c.name, c.type_class 
                    from course_schedules cs 
                    inner join courses c 
                    on cs.course_id = c.id
                    where date = :formatted_date
                    and teacher_id = :teacher_id
                    and cs.is_deleted = false
                    and c.is_deleted = false
                    ) as cs
        on hm.id = cs.hour_id
        where :show_unavailable = TRUE
        order by hm.id
    """)
    result = db_use.session.execute(query, {"teacher_id":teacher_id , "formatted_date": formatted_date, "show_unavailable":show_unavailable }).mappings().all()

    
    if not result:
        return jsonify({
                "status": False,
                "status_code": 401,
                "message": "Data no found",
                "data": None
            }), 401
    
    # Convert results to JSON-serializable format
    schedule = [dict(row) for row in result]
    
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Schedule retrieved successfully",
        "data": {"schedule" : schedule}
    })

@api_blueprint.route('/get_schedule_user', methods=['GET'])
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
        -- Query 1: For "learning with Sensei" (student perspective)
        SELECT 
            DATE_FORMAT(cs.date, '%Y-%m-%d')  AS schedule_date,
            hm.hour_ampm AS schedule_hour,
            cs.hour_id AS hm_id,
            cs.duration,
            c.name AS course_name,
            c.type_class AS course_type,
            c.description AS course_description,
            c.teacher_id AS teacher_user_id,
            c.member_slots,
            c.id as course_id,
            u.full_name as teacher_name,
            concat( :address_storage , u.profile_pic) as teacher_profile_pic,
            'Learning with Sensei' AS criteria
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
            AND cs.type != 'in session'
        UNION
        -- Query 2: For "teaching private / group" (teacher perspective)
        SELECT 
            DATE_FORMAT(cs.date, '%Y-%m-%d')  AS schedule_date,
            hm.hour_ampm AS schedule_hour,
            cs.hour_id AS hm_id,
            cs.duration,
            c.name AS course_name,
            c.type_class AS course_type,
            c.description AS course_description,
            c.teacher_id AS teacher_user_id,
            c.member_slots,
            c.id as course_id,
            u.full_name as teacher_name,
            concat( :address_storage , u.profile_pic) as teacher_profile_pic,
            'Teaching' AS criteria
        FROM courses c
        JOIN course_schedules cs ON cs.course_id = c.id
        JOIN hour_mapping hm on hm.id = cs.hour_id
        left JOIN users u on u.user_id = c.teacher_id 
        WHERE 
            c.teacher_id = :user_id
            AND cs.date >= CURRENT_DATE
            AND cs.is_deleted = FALSE
            AND c.is_deleted = FALSE
            AND cs.type != 'in session'
        -- Final ordering by date and hour
        ORDER BY 
            schedule_date, hm_id;
    """)
    result = db_use.session.execute(query, {"user_id":user_id , "address_storage": address_storage}).mappings().all()

    course_id_arr = [row['course_id'] for row in result if 'course_id' in row]
    if course_id_arr:
        next_query = text("""
            SELECT 
                ce_data.course_id, 
                c.member_slots,          
                ce_data.count_member,
                ce_data.student_id,
                COALESCE(u.full_name, '') AS student_name,
                CASE 
                        WHEN COALESCE(u.profile_pic, '') = '' THEN ''
                        ELSE concat(:address_storage, u.profile_pic)
                END AS student_profile_pic
            FROM (
                SELECT 
                    ce.course_id,
                    COALESCE(COUNT(ce.user_id),0) AS count_member,
                    CASE 
                        WHEN COUNT(ce.user_id) = 1 THEN MAX(ce.user_id)
                        ELSE 0
                    END AS student_id
                FROM course_enrollments AS ce
                WHERE 
                    ce.status = 'active'
                    AND ce.is_deleted = FALSE
                    AND ce.course_id IN :course_id_arr
                GROUP BY 
                    ce.course_id
            ) AS ce_data
            JOIN courses AS c ON c.id = ce_data.course_id
            LEFT JOIN users AS u ON u.user_id = ce_data.student_id
            WHERE 
                c.is_deleted = FALSE
                ;

        """)

        # Execute the next query with the extracted course_id array
        result_count_member_class = db_use.session.execute(next_query, {"course_id_arr": tuple(course_id_arr),"address_storage":address_storage}).mappings().all()
        
    else:
        return jsonify({
                "status": False,
                "status_code": 401,
                "message": "member class not found",
                "data": None
            }), 401

    # Convert results to JSON-serializable format
    schedule = [dict(row) for row in result]
    count_member_class = [dict(row) for row in result_count_member_class]

    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Schedule retrieved successfully",
        "data": {   "schedule" : schedule
                 ,  "count_member_class":count_member_class
                 
        }
    })


@api_blueprint.route('/set_unavailable_schedule', methods=['POST'])
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
        
@api_blueprint.route('/get_list_teachers', methods=['GET'])
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
    
@api_blueprint.route('/get_detail_teacher', methods=['GET'])
def get_detail_teacher():
    # Get the user_id from request parameters
    user_id = request.args.get('user_id')
    teacher_id = request.args.get('teacher_id')
    
    if not teacher_id:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameter 'teacher_id'",
            "data": None
        }), 400

    query_profile = text("""
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
        WHERE u.user_id = :teacher_id
    """)
    result_profile = db_use.session.execute(query_profile, {"teacher_id": teacher_id, "address_storage":address_storage}).mappings().fetchone()
    
    if not result_profile:
        return jsonify({
            "status": False,
            "status_code": 404,
            "message": "Teacher not found",
            "data": None
        }), 404
    
    query_list_group_courses = text("""
        select 
            COALESCE (ce.total,0) current_join , c.name, c.description, c.type_class, c.status, c.member_slots, c.id as course_id, c.created_at, cs.total_class , COALESCE(ce.is_user_join, 0) is_user_join 
        from courses c
        inner join 
        (	select 
                course_id, count(*) total_class from course_schedules cs
            where type = 'scheduled'  
                and is_deleted = 0
            group by course_id
        )	cs 
        on cs.course_id = c.id 
        left JOIN 
        (   SELECT 
                COUNT(DISTINCT user_id) AS total,
                course_id,
                SUM(CASE 
                    WHEN user_id = :user_id THEN 1
                    ELSE 0
                END) > 0 AS is_user_join
            FROM course_enrollments ce
            WHERE ce.is_deleted = 0
            GROUP BY course_id
        ) ce
        on ce.course_id = c.id 
        where c.teacher_id = :teacher_id
            and c.type_class = 'Group'
            and c.is_deleted  = 0
    """)
    result_list_group_courses = db_use.session.execute(query_list_group_courses, {"teacher_id": teacher_id, "user_id":user_id}).mappings().fetchall()
    
    # Convert RowMapping objects to dictionaries
    profile_data = dict(result_profile) if result_profile else None
    list_group_courses_data = [dict(row) for row in result_list_group_courses] if result_list_group_courses else []

    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Teacher details retrieved successfully",
        "data": {
                "profile": profile_data,
                "listGroupCourses": list_group_courses_data
            }
    })
    

@api_blueprint.route('/create_course_bystudent', methods=['POST'])
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
        duration = data.get('duration')
        description = 'Private' # default private
        id = generate_time_short_uuid()

        if not all([student_id, teacher_id, date, hour_id]):
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400

        # Insert into courses table
        insert_course_query = text("""
            INSERT INTO courses (id, created_by, teacher_id, type_class, member_slots, name, course_end_date, description) 
            VALUES (:id, :student_id, :teacher_id, :type_class, :member_slots, :name, :course_end_date, :description)
        """)
        db_use.session.execute(insert_course_query, {
            "id":id,
            "student_id": student_id,
            "teacher_id": teacher_id,
            "type_class" : type_class,
            "member_slots": member_slots,
            "name":name,
            "course_end_date":date,
            "description": description
        })
        db_use.session.commit()

        # Get the last inserted course_id
        course_id = id

        # Insert into course_schedules table
        insert_schedule_query = text("""
            INSERT INTO course_schedules (course_id, date, hour_id, duration, type)
            VALUES (:course_id, :date, :hour_id, :duration, 'scheduled')
        """)
        db_use.session.execute(insert_schedule_query, {
            "course_id": course_id,
            "date": date,
            "hour_id": hour_id,
            "duration": duration
        })

        # Calculate and insert 'in session' entries
        in_session_query = text("""
            INSERT INTO course_schedules (course_id, date, hour_id, duration, type)
            VALUES (:course_id, :date, :hour_id, 0, 'in session')
        """)

        # Generate the additional 'in session' entries
        for offset in range(30, duration, 30):  # Increment by 30 minutes
            db_use.session.execute(in_session_query, {
                "course_id": course_id,
                "date": date,
                "hour_id": hour_id + offset
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

@api_blueprint.route('/get_detail_course', methods=['GET'])
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

def send_email(subject, sender, recipients, body):
    try:
        msg = Message(subject=subject, sender=sender, recipients=recipients, body=body)
        mail.send(msg)
    except Exception as e:
        print("Failed to send email:", e)
        return jsonify({"status": False, "message": "Failed to send email"}), 500
    
@api_blueprint.route('/send-test-email', methods=['GET'])
def send_test_email():
    try:
        # Define email details
        recipient = 'ganip.xra@gmail.com'
        subject = 'Test Send Email'
        body = 'Hello World'

        # Create email message
        msg = Message(subject=subject, recipients=[recipient], body=body)

        # Send email
        mail.send(msg)
        return jsonify({"status": True, "message": f"Test email sent to {recipient}."})
    except Exception as e:
        return jsonify({"status": False, "message": "Failed to send email", "error": str(e)}), 500
    
@api_blueprint.route('/create_custom_course', methods=['POST'])
def create_custom_course():
    try:
        # Get parameters from request
        data = request.json
        user_id = data.get('user_id')
        teacher_id = data.get('teacher_id')
        name = data.get('course_name')
        member_slots = data.get('max_participants')
        course_schedule = data.get('course_schedule')
        id = generate_time_short_uuid()
        
        description = 'Group' # default value
        type_class = 'Group' # default value

        if not all([name, teacher_id, member_slots, course_schedule]):
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400

        # Insert into courses table
        insert_course_query = text("""
            INSERT INTO courses (id, created_by, teacher_id, type_class, member_slots, name, description) 
            VALUES (:id, :user_id, :teacher_id, :type_class, :member_slots, :name, :description)
        """)
        db_use.session.execute(insert_course_query, {
            "id":id,
            "user_id": user_id,
            "teacher_id": teacher_id,
            "type_class" : type_class,
            "member_slots": member_slots,
            "name":name,
            "description": description
        })
        # db_use.session.commit()

        # Get the last inserted course_id
        course_id = id
        latest_date = None

        for schedule in course_schedule:
            date = schedule.get('date')
            hour_id = schedule.get('hm_id')
            duration = schedule.get('duration')
            
            if latest_date is None:
                latest_date = date
            elif latest_date < date:
                latest_date = date

            # Insert the main scheduled entry
            insert_schedule_query = text("""
                INSERT INTO course_schedules (course_id, date, hour_id, duration, type)
                VALUES (:course_id, :date, :hour_id, :duration, 'scheduled')
            """)
            db_use.session.execute(insert_schedule_query, {
                "course_id": course_id,
                "date": date,
                "hour_id": hour_id,
                "duration": duration
            })
            
            # Insert the 'in session' entries
            in_session_query = text("""
                INSERT INTO course_schedules (course_id, date, hour_id, duration, type)
                VALUES (:course_id, :date, :hour_id, 0, 'in session')
            """)
            
            # Generate additional 'in session' entries incremented by 30 minutes
            for offset in range(30, int(duration), 30):  # Increment by 30 minutes
                db_use.session.execute(in_session_query, {
                    "course_id": course_id,
                    "date": date,
                    "hour_id": hour_id + offset
                })
        
        # Update the course's course_end_date with the latest_date
        update_course_query = text("""
            UPDATE courses
            SET course_end_date = :latest_date
            WHERE id = :id
        """)
        db_use.session.execute(update_course_query, {
            "id": course_id,
            "latest_date": latest_date
        })

        # Commit the transaction after processing all schedules
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
    
@api_blueprint.route('/get_list_group_courses', methods=['GET'])
def get_list_group_courses():
    # Get the course_id from the request arguments
    teacher_id = request.args.get('teacher_id')

    if not all([teacher_id]):
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400
    
    list_query = text("""   select COALESCE (ce.total,0) current_join , c.name, c.description, c.type_class, c.status, c.member_slots  from courses c
                            inner join 
                            (	select DISTINCT course_id from course_schedules cs 
                                where type = 'scheduled'  
                                and is_deleted = 0
                            )	cs 
                            on cs.course_id = c.id 
                            left JOIN 
                            (   select DISTINCT count(user_id) as total , course_id from course_enrollments ce 
                                where is_deleted = 0
                                GROUP by course_id
                            ) as ce
                            on ce.course_id = c.id 
                            where c.teacher_id = :teacher_id
                            and c.type_class = 'Group'
                            and c.is_deleted  = 0
                            """)
    list_result = db_use.session.execute(list_query, {"teacher_id": teacher_id,"address_storage": address_storage}).mappings().all()
    course_list = [dict(row) for row in list_result] if list_result else []

    # Return response
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Course details retrieved successfully",
        "data": {
            "course_list": course_list
        }
    })

@api_blueprint.route('/get_schedule_group_course', methods=['GET'])
def get_schedule_group_course():
    # Get the course_id from the request arguments
    course_id = request.args.get('course_id')

    if not all([course_id]):
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400
    
    list_query = text("""   SELECT DATE_FORMAT(cs.date, '%Y-%m-%d')  AS schedule_date , cs.hour_id, cs.duration,cs.type, hm.hour_ampm, hm.hour_24  
                            FROM course_schedules cs 
                            left join hour_mapping hm 
                                on hm.id =cs.hour_id 
                            where course_id = :course_id
                                and type = 'scheduled'
                                and cs.is_deleted  = 0
                            order by date, hour_id 
                            """)
    list_result = db_use.session.execute(list_query, {"course_id": course_id}).mappings().all()
    course_list = [dict(row) for row in list_result] if list_result else []

    # Return response
    return jsonify({
        "status": True,
        "status_code": 200,
        "message": "Course details retrieved successfully",
        "data": course_list
    })

@api_blueprint.route('/join_course', methods=['POST'])
def join_course():
    try:
        # Get parameters from request
        data = request.json
        student_id = data.get('student_id')
        course_id = data.get('course_id')

        if not all([student_id, course_id]):
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400

        # Check if the student is the teacher of the course
        check_teacher_query = text("""
            SELECT teacher_id 
            FROM courses 
            WHERE id = :course_id
        """)
        teacher_result = db_use.session.execute(check_teacher_query, {
            "course_id": course_id
        }).fetchone()

        if teacher_result and teacher_result.teacher_id == student_id:
            return jsonify({
                "status": False,
                "status_code": 403,
                "message": "Teachers are not allowed to enroll as students in their own courses.",
                "data": None
            }), 403

        # Check if the student is already enrolled in the course
        check_enrollment_query = text("""
            SELECT COUNT(*) AS count
            FROM course_enrollments
            WHERE user_id = :student_id 
              AND course_id = :course_id 
              AND is_deleted = 0
        """)
        result = db_use.session.execute(check_enrollment_query, {
            "student_id": student_id,
            "course_id": course_id
        }).fetchone()

        if result.count > 0:
            return jsonify({
                "status": False,
                "status_code": 409,
                "message": "User is already enrolled in this class.",
                "data": None
            }), 409

        # Check the current number of enrolled students
        check_member_slots_query = text("""            
                select c.id, c.member_slots, COALESCE (ce.enrolled_count , 0) as enrolled_count
                from courses c 
                left join (
                    SELECT COUNT(*) AS enrolled_count, course_id 
                    FROM course_enrollments ce
                    WHERE course_id = :course_id 
                    AND is_deleted = 0
                    GROUP by ce.course_id 
                    ) ce
                on ce.course_id = c.id 	
                WHERE id = :course_id
        """)
        enrollment_result = db_use.session.execute(check_member_slots_query, {
            "course_id": course_id
        }).fetchone()

        # Extract results for comparison
        enrolled_count = enrollment_result.enrolled_count if enrollment_result else 0
        member_slots = enrollment_result.member_slots if enrollment_result else 0

        if enrolled_count >= member_slots:
            return jsonify({
                "status": False,
                "status_code": 409,
                "message": "The course has reached its maximum capacity.",
                "data": None
            }), 409

        # Enroll the student into the course
        insert_enrollment_query = text("""
            INSERT INTO course_enrollments (course_id, user_id, status, is_deleted)
            VALUES (:course_id, :student_id, 'active', 0)
        """)
        db_use.session.execute(insert_enrollment_query, {
            "course_id": course_id,
            "student_id": student_id
        })
        db_use.session.commit()

        return jsonify({
            "status": True,
            "status_code": 201,
            "message": "User successfully enrolled in the course.",
            "data": {
                "course_id": course_id,
                "user_id": student_id
            }
        }), 201

    except Exception as e:
        db_use.session.rollback()
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }), 500

@api_blueprint.route('/get_detail_self', methods=['GET'])
def get_detail_self():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({
            "status": False,
            "status_code": 400,
            "message": "Missing required parameters",
            "data": None
        }), 400
    
    try:
        selfData_query = text("""
            SELECT 
                u.user_id, 
                u.full_name, 
                u.email, 
                u.role, 
                u.phone_number, 
                CONCAT(:address_storage, profile_pic) AS profile_pic,
                up.location, 
                up.description, 
                up.about, 
                up.testimonial, 
                up.message
            FROM users u
            LEFT JOIN user_profiles up 
            ON up.user_id = u.user_id 
            WHERE u.user_id = :user_id
        """)
        
        result = db_use.session.execute(
            selfData_query, 
            {"user_id": user_id, "address_storage": address_storage}
        ).mappings().fetchone()
        
        # The result is already a dictionary or None
        self_detail = dict(result) if result else {}

        # Return response
        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Self details retrieved successfully",
            "data": self_detail
        })

    except Exception as e:
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }), 500

@api_blueprint.route('/upload-profile-pic', methods=['POST'])
def upload_profile_pic():
    try:
        user_id = request.form.get('user_id')
        file_name = request.form.get('file_name')
        
        if not user_id or not file_name:
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400
        
        # Ensure a file is included in the request
        if 'file' not in request.files:
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "No file provided",
                "data": None
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "No file selected",
                "data": None
            }), 400
        
        # Sanitize the file name and save the file
        filename = secure_filename(file_name)
        save_path = os.path.join(upload_path, folder_profil_pic, user_id + '_' + filename)
        file.save(save_path)
        
        # Generate the file URL
        profile_pic_path = f"{folder_profil_pic}{user_id + '_' + filename}"
        file_url = f"{address_storage}{profile_pic_path}"
        
        # Update the database
        update_query = text("""
            UPDATE users
            SET profile_pic = :profile_pic
            WHERE user_id = :user_id
        """)
        db_use.session.execute(update_query, {"profile_pic": profile_pic_path, "user_id": user_id})
        db_use.session.commit()
        
        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Profile picture uploaded successfully",
            "data": {
                "file_url": file_url
            }
        })
    except Exception as e:
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }), 500
    
@api_blueprint.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        # Parse JSON data from the request
        user_data = request.json.get('user_data', {})

        # Ensure `user_id` is present in the user_data
        user_id = user_data.get('user_id')
        if not user_id:
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing user_id in request",
                "data": None
            }), 400

        # Extract data with default values
        full_name = user_data.get('full_name', '')
        email = user_data.get('email', '')
        phone_number = user_data.get('phone_number', '')
        location = user_data.get('location', '')
        description = user_data.get('description', '')
        about = user_data.get('about', '')
        testimonial = user_data.get('testimonial', '')
        message = user_data.get('message', '')

        # Update `users` table
        users_update_query = text("""
            UPDATE users
            SET full_name = :full_name,
                email = :email,
                phone_number = :phone_number
            WHERE user_id = :user_id
        """)
        db_use.session.execute(users_update_query, {
            "full_name": full_name,
            "email": email,
            "phone_number": phone_number,
            "user_id": user_id
        })

        # Update `user_profiles` table
        user_profiles_update_query = text("""
            UPDATE user_profiles
            SET location = :location,
                description = :description,
                about = :about,
                testimonial = :testimonial,
                message = :message
            WHERE user_id = :user_id
        """)
        db_use.session.execute(user_profiles_update_query, {
            "location": location,
            "description": description,
            "about": about,
            "testimonial": testimonial,
            "message": message,
            "user_id": user_id
        })

        # Commit changes
        db_use.session.commit()

        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Profile updated successfully",
            "data": None
        })
    except Exception as e:
        # Rollback changes if an error occurs
        db_use.session.rollback()
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }), 500

@api_blueprint.route('/update_password', methods=['POST'])
def update_password():
    try:
        # Parse request JSON data
        data = request.json
        user_id = data.get('user_id')
        passwords_current = data.get('passwords_current', '')
        passwords_new = data.get('passwords_new', '')
        passwords_confirm = data.get('passwords_confirm', '')

        # Check for missing parameters
        if not user_id or not passwords_current or not passwords_new or not passwords_confirm:
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400

        # Validate that the new password and confirmation match
        if passwords_new != passwords_confirm:
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "New password and confirmation do not match",
                "data": None
            }), 400

        # Retrieve the current user and validate their current password
        user_query = text("SELECT password FROM users WHERE user_id = :user_id")
        user_result = db_use.session.execute(user_query, {"user_id": user_id}).mappings().fetchone()

        if not user_result:
            return jsonify({
                "status": False,
                "status_code": 404,
                "message": "User not found",
                "data": None
            }), 404

        # Check if the current password matches the hash in the database
        db_hashed_password = user_result['password']
        input_hashed_password = hash_password_md5(passwords_current)

        if not (input_hashed_password == db_hashed_password):
            return jsonify({
                "status": False,
                "status_code": 400,
                "message": "Current password is incorrect",
                "data": None
            }), 400

        new_hashed_password =  hash_password_md5(passwords_confirm)
        # Update the user's password in the database
        update_password_query = text("""
            UPDATE users 
            SET password = :new_password 
            WHERE user_id = :user_id
        """)
        db_use.session.execute(update_password_query, {
            "new_password": new_hashed_password,
            "user_id": user_id
        })

        # Commit the changes
        db_use.session.commit()

        return jsonify({
            "status": True,
            "status_code": 200,
            "message": "Password updated successfully",
            "data": None
        })

    except Exception as e:
        # Rollback in case of an error
        db_use.session.rollback()
        return jsonify({
            "status": False,
            "status_code": 500,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }), 500