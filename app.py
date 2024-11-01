from flask import Flask
from flask_jwt_extended import JWTManager
from db import init_db
from controllers.users import auth_bp
from controllers.accounts import accounts_bp
from controllers.transactions import transactions_bp
from swagger import init_swagger

app = Flask(__name__)

# Set up JWT configuration
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"
jwt = JWTManager(app)

# Register Swagger
swagger = init_swagger(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(accounts_bp, url_prefix='/accounts')
app.register_blueprint(transactions_bp, url_prefix='/transactions')

# Initialize the database only once
db_initialized = False

@app.before_request
def setup():
    global db_initialized
    if not db_initialized:
        init_db()
        db_initialized = True

# Main endpoint
@app.route('/', methods=['GET'])
def index():
    return {"message": "Welcome to the Bank Root API"}

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return {"status": "API is running"}

if __name__ == '__main__':
    app.run(debug=True)