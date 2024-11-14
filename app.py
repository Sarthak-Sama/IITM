from flask import Flask, redirect, url_for
from models import db  # Import db from models, instead of initializing here
from routes import admin_bp, customer_bp, professional_bp, auth_bp

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize the database here
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(customer_bp, url_prefix='/customer')
app.register_blueprint(professional_bp, url_prefix='/professional')

if __name__ == '__main__':
    with app.app_context():  # Ensure the app context is pushed before creating tables
        try:
            db.create_all()  # Creates the database tables if they don't exist
        except Exception as e:
            print(f"Error creating database tables: {e}")  # Error handling for database creation
    app.run(debug=True)
