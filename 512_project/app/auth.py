from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .database_helper import register_user, get_user_by_username, check_password, get_administrator_by_userid, check_administrator_password, register_administrator

bp_auth = Blueprint('auth', __name__)

# Route for login page
@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        # If the user is already logged in, redirect to the ML prediction page
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists and if the password is correct
        user = get_user_by_username(username)
        if user and check_password(user, password):
            session['username'] = username  # Store username in session
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))  # Redirect to ML prediction page
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

# Route for registration page
@bp_auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords don't match.", 'danger')
            return redirect(url_for('auth.register'))

        # Check if user already exists
        if get_user_by_username(username):
            flash("Username already exists. Please choose another.", 'danger')
            return redirect(url_for('auth.register'))

        # Register the user
        register_user(username, password)
        flash("Registration successful! Please log in.", 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# Route for administrator login page
@bp_auth.route('/administrator_login', methods=['GET', 'POST'])
def administrator_login():
    """
    if 'administrator_userid' in session:
        # If the administrator is already logged in, redirect to the admin dashboard or another page
        return redirect(url_for('admin.dashboard'))  # You need to create an admin dashboard page
    """
    if request.method == 'POST':
        administrator_userid = request.form['administrator_userid']
        administrator_password = request.form['administrator_password']

        # Check if the administrator exists and if the password is correct
        administrator = get_administrator_by_userid(administrator_userid)
        if administrator and check_administrator_password(administrator, administrator_password):
            session['administrator_userid'] = administrator_userid  # Store administrator userid in session
            flash('Administrator login successful!', 'success')
            return redirect(url_for('main.admin_dashboard'))  # Redirect to admin dashboard or any other page
        else:
            flash('Invalid administrator ID or password.', 'danger')

    return render_template('administrator_login.html')

# Route for administrator registration page
@bp_auth.route('/administrator_register', methods=['GET', 'POST'])
def administrator_register():
    if request.method == 'POST':
        administrator_userid = request.form['administrator_userid']
        administrator_password = request.form['administrator_password']
        confirm_password = request.form['confirm_password']

        if administrator_password != confirm_password:
            flash("Passwords don't match.", 'danger')
            return redirect(url_for('auth.administrator_register'))

        # Check if administrator already exists
        if get_administrator_by_userid(administrator_userid):
            flash("Administrator ID already exists. Please choose another.", 'danger')
            return redirect(url_for('auth.administrator_register'))

        # Register the administrator
        register_administrator(administrator_userid, administrator_password)
        flash("Administrator registration successful! Please log in.", 'success')
        return redirect(url_for('auth.administrator_login'))

    return render_template('administrator_register.html')

# Route for logout
@bp_auth.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session to log the user out
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))  # Redirect to login page