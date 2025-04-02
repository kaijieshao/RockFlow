from flask import Flask, redirect, url_for, session
from .routes import bp as main_bp
from .auth import bp_auth

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'  # Required for session management
    app.register_blueprint(main_bp)  # Main Blueprint for ML predictions
    app.register_blueprint(bp_auth)  # Auth Blueprint for login/register

    # Default route to check login status
    @app.route('/')
    def home():
        if 'username' in session:
            # If user is logged in, redirect to ML prediction page
            return redirect(url_for('main.index'))
        else:
            # If user is not logged in, redirect to login page
            return redirect(url_for('auth.login'))

    return app
