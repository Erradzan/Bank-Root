from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import SessionLocal
from models import Account, User

accounts_bp = Blueprint('accounts', __name__)

# Test Route
@accounts_bp.route('/test', methods=['GET'])
def test_account_route():
    """
    Test the accounts route
    ---
    tags:
      - Accounts
    responses:
      200:
        description: Accounts route is working
        schema:
          type: object
          properties:
            message:
              type: string
              example: Accounts route is working
    """
    return jsonify({"message": "Accounts route is working"}), 200

# Helper function to close the session
def close_session(session):
    if session:
        session.close()

# Retrieve all accounts of the authenticated user
@accounts_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_accounts():
    """
    Retrieve all accounts for the authenticated user
    ---
    tags:
      - Accounts
    responses:
      200:
        description: A list of accounts
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              account_type:
                type: string
              account_number:
                type: string
              balance:
                type: number
                format: float
              owner:
                type: object
                properties:
                  id:
                    type: integer
                  username:
                    type: string
    """
    user_id = get_jwt_identity()
    
    session = SessionLocal()
    accounts = session.query(Account).filter_by(user_id=user_id).all()
    
    accounts_data = [
        {
            "id": account.id,
            "account_type": account.account_type,
            "account_number": account.account_number,
            "balance": float(account.balance),
            "owner": {
                "id": user_id,
                "username": session.query(User).filter_by(id=user_id).first().username
            }
        } for account in accounts
    ]
    
    close_session(session)
    return jsonify(accounts_data), 200

# Retrieve a specific account by ID
@accounts_bp.route('/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    """
    Retrieve a specific account by ID
    ---
    tags:
      - Accounts
    parameters:
      - in: path
        name: account_id
        required: true
        type: integer
    responses:
      200:
        description: Account details
        schema:
          type: object
          properties:
            id:
              type: integer
            account_type:
              type: string
            account_number:
              type: string
            balance:
              type: number
              format: float
            owner:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
      404:
        description: Account not found
    """
    user_id = get_jwt_identity()
    
    session = SessionLocal()
    account = session.query(Account).filter_by(id=account_id, user_id=user_id).first()
    
    if account:
        account_data = {
            "id": account.id,
            "account_type": account.account_type,
            "account_number": account.account_number,
            "balance": float(account.balance),
            "owner": {
                "id": user_id,
                "username": session.query(User).filter_by(id=user_id).first().username
            }
        }
        close_session(session)
        return jsonify(account_data), 200
    
    close_session(session)
    return jsonify({"message": "Account not found"}), 404

# Create a new account for the authenticated user
@accounts_bp.route('/new', methods=['POST'])
@jwt_required()
def create_account():
    """
    Create a new account for the authenticated user
    ---
    tags:
      - Accounts
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            account_type:
              type: string
              example: Savings
            account_number:
              type: string
              example: 123456789
            balance:
              type: number
              format: float
              example: 1000.0
    responses:
      201:
        description: Account created successfully
      400:
        description: Bad request
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    account_type = data.get("account_type")
    account_number = data.get("account_number")
    initial_balance = data.get("balance", 0.0)
    
    session = SessionLocal()
    new_account = Account(
        user_id=user_id,
        account_type=account_type,
        account_number=account_number,
        balance=initial_balance
    )
    
    session.add(new_account)
    session.commit()
    close_session(session)
    
    return jsonify({"message": "Account created successfully"}), 201

# Update account details
@accounts_bp.route('/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    """
    Update account details
    ---
    tags:
      - Accounts
    parameters:
      - in: path
        name: account_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            account_type:
              type: string
            balance:
              type: number
              format: float
    responses:
      200:
        description: Account updated successfully
      404:
        description: Account not found
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    account_type = data.get("account_type")
    balance = data.get("balance")
    
    session = SessionLocal()
    account = session.query(Account).filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        close_session(session)
        return jsonify({"message": "Account not found"}), 404
    
    if account_type:
        account.account_type = account_type
    if balance is not None:
        account.balance = balance
    
    session.commit()
    close_session(session)
    
    return jsonify({"message": "Account updated successfully"}), 200

# Delete an account
@accounts_bp.route('/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    """
    Delete an account
    ---
    tags:
      - Accounts
    parameters:
      - in: path
        name: account_id
        required: true
        type: integer
    responses:
      200:
        description: Account deleted successfully
      404:
        description: Account not found
    """
    user_id = get_jwt_identity()
    
    session = SessionLocal()
    account = session.query(Account).filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        close_session(session)
        return jsonify({"message": "Account not found"}), 404
    
    session.delete(account)
    session.commit()
    close_session(session)
    
    return jsonify({"message": "Account deleted successfully"}), 200