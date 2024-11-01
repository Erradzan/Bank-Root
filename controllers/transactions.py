from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import SessionLocal
from models import Account, Transaction, User
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal

# Create a Blueprint for transactions
transactions_bp = Blueprint('transactions', __name__)

# Helper function to close the session
def close_session(session):
    if session:
        session.close()

# Helper function to validate user access to account by account number
def validate_account_owner_by_number(user_id, account_number, session):
    account = session.query(Account).filter_by(account_number=account_number, user_id=user_id).first()
    return account

# Route to view all transactions of the authenticated user
@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def get_transactions():
    """
    Retrieve all transactions for the authenticated user
    ---
    tags:
      - Transactions
    responses:
      200:
        description: A list of transactions
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              type:
                type: string
              amount:
                type: number
                format: float
              description:
                type: string
              from_account_id:
                type: integer
              to_account_id:
                type: integer
              created_at:
                type: string
                format: date-time
    """
    user_id = get_jwt_identity()
    session = SessionLocal()
    try:
        # Get all accounts for the user and their transactions
        accounts = session.query(Account).filter_by(user_id=user_id).all()
        transactions = []
        for account in accounts:
            account_transactions = session.query(Transaction).filter_by(from_account_id=account.id).all()
            transactions.extend(account_transactions)

        # Serialize transactions
        transaction_list = [
            {
                "id": t.id,
                "type": t.type,
                "amount": float(t.amount),
                "description": t.description,
                "from_account_id": t.from_account_id,
                "to_account_id": t.to_account_id,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
        
        return jsonify(transactions=transaction_list), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        close_session(session)

# Route to create a new transaction
@transactions_bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():
    """
    Create a new transaction for the authenticated user
    ---
    tags:
      - Transactions
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            from_account_number:
              type: string
            to_account_number:
              type: string
            amount:
              type: number
              format: float
            type:
              type: string
              example: deposit
            description:
              type: string
              example: "Deposit funds"
    responses:
      201:
        description: Transaction created successfully
      400:
        description: Bad request
      403:
        description: Unauthorized access to the account
      500:
        description: Internal server error
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    from_account_number = data.get('from_account_number')
    to_account_number = data.get('to_account_number')
    amount = Decimal(data.get('amount'))
    transaction_type = data.get('type')
    description = data.get('description', '')

    session = SessionLocal()
    try:
        # Validate from_account ownership by account_number
        from_account = validate_account_owner_by_number(user_id, from_account_number, session)
        if not from_account:
            return jsonify({"error": "Unauthorized access to the account"}), 403

        # Retrieve target account by account_number
        to_account = session.query(Account).filter_by(account_number=to_account_number).first() if to_account_number else None

        # Check transaction type and process
        if transaction_type == "deposit":
            from_account.balance += amount
        elif transaction_type == "withdrawal":
            if from_account.balance >= amount:
                from_account.balance -= amount
            else:
                return jsonify({"error": "Insufficient funds"}), 400
        elif transaction_type == "transfer":
            if from_account.balance >= amount and to_account:
                from_account.balance -= amount
                to_account.balance += amount
            else:
                return jsonify({"error": "Insufficient funds or invalid target account"}), 400
        else:
            return jsonify({"error": "Invalid transaction type"}), 400

        # Create a transaction record
        transaction = Transaction(
            from_account_id=from_account.id,
            to_account_id=to_account.id if to_account else None,
            amount=amount,
            type=transaction_type,
            description=description
        )
        session.add(transaction)
        session.commit()

        return jsonify({"message": "Transaction completed successfully"}), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        close_session(session)