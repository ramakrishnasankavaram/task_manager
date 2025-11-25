from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.database import mysql
from functools import wraps

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first!', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@tasks_bp.route('/')
@tasks_bp.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    
    # Get statistics
    user_id = session['user_id']
    cur.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = %s", [user_id])
    total_tasks = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as completed FROM tasks WHERE user_id = %s AND status = 'completed'", [user_id])
    completed_tasks = cur.fetchone()['completed']
    
    cur.execute("SELECT COUNT(*) as pending FROM tasks WHERE user_id = %s AND status = 'pending'", [user_id])
    pending_tasks = cur.fetchone()['pending']
    
    cur.execute("SELECT COUNT(*) as in_progress FROM tasks WHERE user_id = %s AND status = 'in_progress'", [user_id])
    in_progress_tasks = cur.fetchone()['in_progress']
    
    cur.close()

    stats = {
        'total': total_tasks,
        'completed': completed_tasks,
        'pending': pending_tasks,
        'in_progress': in_progress_tasks
    }

    # Fetch recent tasks to show on dashboard
    cur2 = mysql.connection.cursor()
    cur2.execute("""
        SELECT id, title, status, priority, due_date
        FROM tasks
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, [user_id])
    recent_tasks = cur2.fetchall()
    cur2.close()

    return render_template('dashboard.html', stats=stats, recent_tasks=recent_tasks)

@tasks_bp.route('/list')
@login_required
def list():
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    
    cur = mysql.connection.cursor()
    query = "SELECT * FROM tasks WHERE user_id = %s"
    params = [session['user_id']]
    
    if status_filter != 'all':
        query += " AND status = %s"
        params.append(status_filter)
    
    if priority_filter != 'all':
        query += " AND priority = %s"
        params.append(priority_filter)
    
    query += " ORDER BY created_at DESC"
    
    cur.execute(query, params)
    tasks_list = cur.fetchall()
    cur.close()
    
    return render_template('tasks.html', tasks=tasks_list, 
                         status_filter=status_filter, 
                         priority_filter=priority_filter)

@tasks_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form['title']
    description = request.form['description']
    priority = request.form['priority']
    due_date = request.form['due_date'] if request.form['due_date'] else None
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO tasks (user_id, title, description, priority, due_date) 
        VALUES (%s, %s, %s, %s, %s)
    """, (session['user_id'], title, description, priority, due_date))
    mysql.connection.commit()
    cur.close()
    
    flash('Task added successfully!', 'success')
    return redirect(url_for('tasks.list'))

@tasks_bp.route('/update/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    title = request.form['title']
    description = request.form['description']
    status = request.form['status']
    priority = request.form['priority']
    due_date = request.form['due_date'] if request.form['due_date'] else None
    
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE tasks 
        SET title = %s, description = %s, status = %s, priority = %s, due_date = %s 
        WHERE id = %s AND user_id = %s
    """, (title, description, status, priority, due_date, task_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    flash('Task updated successfully!', 'success')
    return redirect(url_for('tasks.list'))

@tasks_bp.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", 
                (task_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks.list'))

@tasks_bp.route('/status/<int:task_id>/<status>', methods=['POST'])
@login_required
def update_status(task_id, status):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s", 
                (status, task_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'success': True})