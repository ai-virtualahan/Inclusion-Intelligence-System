from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection


login_bp = Blueprint('login', __name__)



@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, contact_person, work_email, password_hash, role, status
            FROM users
            WHERE work_email = %s
        """, (email,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            flash("Email not found.", "error")
            return redirect(url_for('login.login'))

        if not check_password_hash(user['password_hash'], password):
            flash("Incorrect password.", "error")
            return redirect(url_for('login.login'))

        # 🔐 APPROVAL CHECK
        if user['role'] == 'org_admin' and user['status'] != 'approved':
            flash("Your account is still pending approval.", "warning")
            return redirect(url_for('login.login'))

        # ✅ SESSION
        session['user_id'] = user['id']
        session['contact_person'] = user['contact_person']
        session['role'] = user['role']

        # 🔀 ROLE-BASED REDIRECT
        if user['role'] == 'org_admin':
            return redirect(url_for('assessment'))

        elif user['role'] == 'vhan_admin':
            return redirect(url_for('vhan.vhan_dashboard'))

        elif user['role'] == 'super_admin':
            return redirect(url_for('super_admin.super_dashboard'))

    return render_template('login.html')

    
@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))