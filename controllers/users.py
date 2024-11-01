from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from db import SessionLocal
from models import User

auth_bp = Blueprint('auth', __name__)

# Helper function to close the session
def close_session(session):
    if session:
        session.close()

# Register a new user
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: user123
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: securepassword
    responses:
      201:
        description: User registered successfully
      400:
        description: Bad request
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    # Hash the password
    password_hash = generate_password_hash(password)

    # Create a new user instance
    session = SessionLocal()
    new_user = User(username=username, email=email, password_hash=password_hash)

    try:
        session.add(new_user)
        session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"message": "Error registering user"}), 400
    finally:
        close_session(session)

# Login a user and issue a JWT token
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login a user and issue a JWT token
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: securepassword
    responses:
      200:
        description: JWT access token
        schema:
          type: object
          properties:
            access_token:
              type: string
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.id)
        close_session(session)
        return jsonify(access_token=access_token), 200

    close_session(session)
    return jsonify({"message": "Invalid credentials"}), 401

# Get profile of the currently authenticated user
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """
    Get profile of the currently authenticated user
    ---
    tags:
      - User Profile
    responses:
      200:
        description: User profile information
        schema:
          type: object
          properties:
            username:
              type: string
              example: user123
            email:
              type: string
              example: user@example.com
      404:
        description: User not found
    """
    user_id = get_jwt_identity()

    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()

    if user:
        user_data = {"username": user.username, "email": user.email}
        close_session(session)
        return jsonify(user_data), 200

    close_session(session)
    return jsonify({"message": "User not found"}), 404

# Update the profile information of the authenticated user
@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update profile information for the authenticated user
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: new_username
            email:
              type: string
              example: new_email@example.com
    responses:
      200:
        description: User profile updated successfully
      400:
        description: Bad request, invalid input
      404:
        description: User not found
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")

    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        close_session(session)
        return jsonify({"message": "User not found"}), 404

    if username:
        user.username = username
    if email:
        user.email = email

    session.commit()
    close_session(session)
    
    return jsonify({"message": "User profile updated successfully"}), 200

# Get all users
@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """
    Get all users
    ---
    tags:
      - Users
    responses:
      200:
        description: A list of users
        schema:
          type: object
          properties:
            users:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  username:
                    type: string
                  email:
                    type: string
    """
    session = SessionLocal()
    users = session.query(User).all()

    users_list = [{"id": user.id, "username": user.username, "email": user.email} for user in users]
    close_session(session)
    return jsonify(users=users_list), 200