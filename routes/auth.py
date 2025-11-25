from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from models.database import mysql

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('tasks.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hashed_password))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Username or email already exists!', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('tasks.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('tasks.dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """View and update user profile (username, email)."""
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    if request.method == 'POST':
        # Update username/email
        new_username = request.form.get('username')
        new_email = request.form.get('email')

        try:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET username = %s, email = %s WHERE id = %s",
                       (new_username, new_email, user_id))
            mysql.connection.commit()
            cur.close()

            # Update session display name
            session['username'] = new_username
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            flash('Could not update profile (username/email may already be in use).', 'danger')
            return redirect(url_for('auth.profile'))

    # GET: load user
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email, created_at FROM users WHERE id = %s", [user_id])
    user = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user)


@auth_bp.route('/profile/change-password', methods=['POST'])
def change_password():
    """Change the logged-in user's password (requires current password)."""
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_password or new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('auth.profile'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT password FROM users WHERE id = %s", [user_id])
    user = cur.fetchone()

    if not user or not bcrypt.check_password_hash(user['password'], current_password):
        cur.close()
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('auth.profile'))

    # Update password
    hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')
    cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
    mysql.connection.commit()
    cur.close()

    flash('Password changed successfully.', 'success')
    return redirect(url_for('auth.profile'))