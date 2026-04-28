
from flask import render_template, request, redirect, url_for, flash
from mysql.connector import Error
from werkzeug.security import generate_password_hash

from flask import Blueprint
from db import get_db_connection

register_bp = Blueprint('register', __name__)


@register_bp.route('/register')
def register():
    return render_template('register.html')


@register_bp.route('/submit_registration', methods=['POST'])
def submit_registration():
    full_name = request.form.get('full_name')
    position = request.form.get('position')
    work_email = request.form.get('work_email')
    contact_number = request.form.get('contact_number')
    company_name = request.form.get('company_name')
    company_size = request.form.get('company_size')
    industry = request.form.get('industry')
    company_number = request.form.get('company_number')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    agree_terms = request.form.get('agree_terms')

    if not all([
        full_name, position, work_email, contact_number,
        company_name, company_size, industry, password, confirm_password
    ]):
        flash("Please fill out all required fields.", "danger")
        return redirect(url_for('register.register'))

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('register.register'))

    if not agree_terms:
        flash("You must agree to the Terms of Use and Privacy Policy.", "danger")
        return redirect(url_for('register.register'))

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        check_request_sql = """
            SELECT id FROM access_requests
            WHERE work_email = %s AND status = 'pending'
        """
        cursor.execute(check_request_sql, (work_email,))
        existing_request = cursor.fetchone()

        if existing_request:
            flash("A pending access request already exists for this email.", "warning")
            return redirect(url_for('register.register'))

        check_user_sql = """
            SELECT id FROM users
            WHERE email = %s
        """
        cursor.execute(check_user_sql, (work_email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("This email is already registered. Please log in.", "warning")
            return redirect(url_for('login'))

        insert_sql = """
            INSERT INTO access_requests
            (
                company_name,
                industry,
                company_size,
                contact_person,
                work_email,
                password_hash,
                position_title,
                contact_number,
                notes,
                status,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
        """

        values = (
            company_name,
            industry,
            company_size,
            full_name,
            work_email,
            hashed_password,
            position,
            contact_number,
            company_number
        )

        cursor.execute(insert_sql, values)
        conn.commit()

        flash("Your access request has been submitted successfully. Please wait for admin approval.", "success")
        return redirect(url_for('login'))

    except Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for('register.register'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()