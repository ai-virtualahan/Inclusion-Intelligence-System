
import hashlib
import re
import secrets
from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash
from flask_mail import Message
from mysql.connector import Error
from werkzeug.security import generate_password_hash

from flask import Blueprint
from config import APP_BASE_URL
from db import get_db_connection
from extensions import mail
from settings_utils import get_int_setting

register_bp = Blueprint('register', __name__)

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s().-]{8,18}[0-9]$")


def is_valid_email(email):
    return bool(email and EMAIL_PATTERN.fullmatch(email.strip()))


def is_valid_phone_number(phone_number):
    if not phone_number or not PHONE_PATTERN.fullmatch(phone_number.strip()):
        return False

    digits = re.sub(r"\D", "", phone_number)
    return 10 <= len(digits) <= 15


def verification_token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_verification_link(token):
    path = url_for("register.verify_email", token=token)
    if APP_BASE_URL:
        return f"{APP_BASE_URL.rstrip('/')}{path}"
    return url_for("register.verify_email", token=token, _external=True)


def send_verification_email(cursor, recipient_email, contact_person, token):
    verification_link = build_verification_link(token)
    subject = "Verify Your Email - Inclusion Intelligence System"
    message_body = f"""Hello {contact_person},

Please verify your email address to continue your Inclusion Intelligence System registration.

Verification link:
{verification_link}

This link will expire in 24 hours. Once verified, your access request will be sent to the administrator for approval.

Thank you,
Inclusion Intelligence System Team"""

    try:
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=message_body
        )
        mail.send(msg)

        cursor.execute("""
            INSERT INTO email_notifications (
                recipient_email,
                notification_type,
                subject,
                message_body,
                send_status,
                sent_at
            )
            VALUES (%s, 'email_verification', %s, %s, 'sent', NOW())
        """, (recipient_email, subject, message_body))
        return True
    except Exception as e:
        cursor.execute("""
            INSERT INTO email_notifications (
                recipient_email,
                notification_type,
                subject,
                message_body,
                send_status,
                error_message
            )
            VALUES (%s, 'email_verification', %s, %s, 'failed', %s)
        """, (recipient_email, subject, message_body, str(e)))
        return False


@register_bp.route('/register')
def register():
    return render_template('register.html')


@register_bp.route('/verify-email/<token>')
def verify_email(token):
    token_hash = verification_token_hash(token)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, status
            FROM access_requests
            WHERE verification_token_hash = %s
              AND verification_token_expiry > NOW()
            LIMIT 1
        """, (token_hash,))
        access_request = cursor.fetchone()

        if not access_request:
            flash("Verification link is invalid or expired. Please submit your registration again.", "danger")
            return redirect(url_for('register.register'))

        if access_request['status'] != 'email_unverified':
            flash("This email has already been verified.", "success")
            return redirect(url_for('login.login'))

        cursor.execute("""
            UPDATE access_requests
            SET email_verified_at = NOW(),
                verification_token_hash = NULL,
                verification_token_expiry = NULL,
                status = 'pending'
            WHERE id = %s
        """, (access_request['id'],))
        conn.commit()

        flash("Email verified successfully. Your access request is now pending admin approval.", "success")
        return redirect(url_for('login.login'))
    except Error as e:
        conn.rollback()
        flash(f"Unable to verify email: {e}", "danger")
        return redirect(url_for('register.register'))
    finally:
        cursor.close()
        conn.close()


@register_bp.route('/submit_registration', methods=['POST'])
def submit_registration():
    full_name = request.form.get('full_name')
    position = request.form.get('position')
    work_email = (request.form.get('work_email') or '').strip().lower()
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

    if not is_valid_email(work_email):
        flash("Please enter a valid work email address.", "danger")
        return redirect(url_for('register.register'))

    if not is_valid_phone_number(contact_number):
        flash("Please enter a valid contact number.", "danger")
        return redirect(url_for('register.register'))

    if company_number and not is_valid_phone_number(company_number):
        flash("Please enter a valid company number.", "danger")
        return redirect(url_for('register.register'))

    if not agree_terms:
        flash("You must agree to the Terms of Use and Privacy Policy.", "danger")
        return redirect(url_for('register.register'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        min_password_length = get_int_setting(cursor, "password_min_length", 8)
        if len(password) < min_password_length:
            flash(f"Password must be at least {min_password_length} characters long.", "danger")
            return redirect(url_for('register.register'))

        check_request_sql = """
            SELECT id, status
            FROM access_requests
            WHERE work_email = %s
            LIMIT 1
        """
        cursor.execute(check_request_sql, (work_email,))
        existing_request = cursor.fetchone()

        if existing_request:
            if existing_request['status'] == 'email_unverified':
                token = secrets.token_urlsafe(32)
                token_hash = verification_token_hash(token)
                token_expiry = datetime.now() + timedelta(hours=24)
                hashed_password = generate_password_hash(password)

                cursor.execute("""
                    UPDATE access_requests
                    SET company_name = %s,
                        industry = %s,
                        company_size = %s,
                        company_number = %s,
                        contact_person = %s,
                        password_hash = %s,
                        position_title = %s,
                        contact_number = %s,
                        verification_token_hash = %s,
                        verification_token_expiry = %s,
                        email_verified_at = NULL,
                        status = 'email_unverified'
                    WHERE id = %s
                """, (
                    company_name,
                    industry,
                    company_size,
                    company_number,
                    full_name,
                    hashed_password,
                    position,
                    contact_number,
                    token_hash,
                    token_expiry,
                    existing_request['id']
                ))

                email_sent = send_verification_email(cursor, work_email, full_name, token)
                conn.commit()
                if email_sent:
                    flash("Verification email sent. Please check your inbox to continue registration.", "success")
                else:
                    flash("Registration saved, but the verification email failed. Please contact support.", "warning")
                return redirect(url_for('register.register'))

            if existing_request['status'] == 'pending':
                flash("A pending access request already exists for this email.", "warning")
            elif existing_request['status'] == 'approved':
                flash("This email is already approved. Please log in.", "warning")
            else:
                flash("This email already has a rejected access request. Please contact the administrator.", "warning")
            return redirect(url_for('register.register'))

        check_user_sql = """
            SELECT id FROM users
            WHERE work_email = %s
        """
        cursor.execute(check_user_sql, (work_email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("This email is already registered. Please log in.", "warning")
            return redirect(url_for('login.login'))

        hashed_password = generate_password_hash(password)
        token = secrets.token_urlsafe(32)
        token_hash = verification_token_hash(token)
        token_expiry = datetime.now() + timedelta(hours=24)

        insert_sql = """
            INSERT INTO access_requests
            (
                company_name,
                industry,
                company_size,
                company_number,
                contact_person,
                work_email,
                password_hash,
                verification_token_hash,
                verification_token_expiry,
                position_title,
                contact_number,
                status,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'email_unverified', NOW())
        """

        values = (
            company_name,
            industry,
            company_size,
            company_number,
            full_name,
            work_email,
            hashed_password,
            token_hash,
            token_expiry,
            position,
            contact_number
                        
        )

        cursor.execute(insert_sql, values)
        email_sent = send_verification_email(cursor, work_email, full_name, token)
        conn.commit()

        if email_sent:
            flash("Verification email sent. Please check your inbox to continue registration.", "success")
        else:
            flash("Registration saved, but the verification email failed. Please contact support.", "warning")
        return redirect(url_for('register.register'))

    except Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for('register.register'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
