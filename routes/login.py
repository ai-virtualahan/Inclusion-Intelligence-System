from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection
from datetime import datetime, timedelta
import secrets
from flask_mail import Message
from extensions import mail
from config import MAIL_USERNAME


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



@login_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    
    email = request.form['email']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE work_email = %s", (email,))
    user = cursor.fetchone()

    if user:
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(minutes=15)

        cursor.execute("""
            UPDATE users
            SET reset_token = %s,
                reset_token_expiry = %s
            WHERE work_email = %s
        """, (token, expiry, email))

        conn.commit()

        reset_link = url_for('login.reset_password', token=token, _external=True)

        msg = Message(
            subject="Reset Your Password - Inclusion Intelligence System",
            sender=MAIL_USERNAME,
            recipients=[email]
        )

        msg.body = f"""
        Hello {user.get('contact_person', '')},

        We received a request to reset the password associated with your Inclusion Intelligence System account.

        Please click the link below to create a new password:

        {reset_link}

        For security purposes, this link will expire in 15 minutes.

        If you did not request a password reset, you may safely ignore this email.

        Thank you,
        Inclusion Intelligence System Support Team
        Empowering Inclusion. Enriching Lives.
        """

        print("ABOUT TO SEND EMAIL TO:",  email)
        mail.send(msg)
        print ("EMAIL SENT SUCCESSFULLY")

        flash("A password reset link has been sent to your email.", "success")
    else:
        flash("Email not found.", "error")

    cursor.close()
    conn.close()

    return redirect(url_for('login.login'))


@login_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM users
        WHERE reset_token = %s
          AND reset_token_expiry > NOW()
    """, (token,))

    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        flash("Reset link is invalid or expired.", "error")
        return redirect(url_for('login.login'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            cursor.close()
            conn.close()
            return render_template('reset_password.html', token=token)

        hashed_password = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE users
            SET password_hash = %s,
                reset_token = NULL,
                reset_token_expiry = NULL
            WHERE id = %s
        """, (hashed_password, user['id']))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Password reset successful. You may now login.", "success")
        return redirect(url_for('login.login'))

    cursor.close()
    conn.close()

    return render_template('reset_password.html', token=token)


