from flask import Blueprint, render_template, session, redirect, url_for, request
from db import get_db_connection
from flask_mail import Message
from extensions import mail

vhan_bp = Blueprint('vhan', __name__)


@vhan_bp.route('/vhan/dashboard')
def vhan_dashboard():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            company_name,
            industry,
            company_size,
            company_number,
            contact_person,
            position_title,
            contact_number,
            work_email,
            status,
            created_at
        FROM access_requests
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """)

    requests = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('vhan_dashboard.html', requests=requests)


@vhan_bp.route('/vhan/approve/<int:req_id>')
def approve_request(req_id):
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get request data
    cursor.execute("""
        SELECT *
        FROM access_requests
        WHERE id = %s
    """, (req_id,))

    req = cursor.fetchone()

    # Safety check: if request does not exist
    if not req:
        cursor.close()
        conn.close()
        return redirect(url_for('vhan.vhan_dashboard'))

    # Safety check: only pending requests can be approved
    if req['status'] != 'pending':
        cursor.close()
        conn.close()
        return redirect(url_for('vhan.vhan_dashboard'))

    # Insert approved organization
    cursor.execute("""
        INSERT INTO organizations (
            company_name,
            industry,
            company_size,
            company_number,
            status,
            approved_at
        )
        VALUES (%s, %s, %s, %s, 'approved', NOW())
    """, (
        req['company_name'],
        req['industry'],
        req['company_size'],
        req['company_number']
    ))

    org_id = cursor.lastrowid

    # Insert organization admin user
    cursor.execute("""
        INSERT INTO users (
            organization_id,
            contact_person,
            work_email,
            password_hash,
            role,
            status,
            contact_number,
            position_title
        )
        VALUES (%s, %s, %s, %s, 'org_admin', 'approved', %s, %s)
    """, (
        org_id,
        req['contact_person'],
        req['work_email'],
        req['password_hash'],
        req['contact_number'],
        req['position_title']
    ))

    # Update access request status
    cursor.execute("""
        UPDATE access_requests
        SET status = 'approved'
        WHERE id = %s
    """, (req_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('vhan.vhan_dashboard'))


@vhan_bp.route('/vhan/pending-approvals')
def pending_approvals():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            company_name,
            industry,
            company_size,
            company_number,
            contact_person,
            position_title,
            contact_number,
            work_email,
            status,
            created_at
        FROM access_requests
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """)

    requests = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('pending_approvals.html', requests=requests)


@vhan_bp.route('/vhan/email-logs', methods=['GET', 'POST'])
def email_logs():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        company_name = request.form.get('company_name')
        recipient_email = request.form.get('recipient_email')
        message_body = request.form.get('message_body')

        subject = "Registration Invitation - Inclusion Intelligence"

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
                    sent_at,
                    triggered_by
                )
                VALUES (%s, 'registration_invitation', %s, %s, 'sent', NOW(), %s)
            """, (
                recipient_email,
                subject,
                message_body,
                session.get('user_id')
            ))

            conn.commit()

        except Exception as e:

            print("EMAIL SEND ERROR:", e)

            cursor.execute("""
                INSERT INTO email_notifications (
                    recipient_email,
                    notification_type,
                    subject,
                    message_body,
                    send_status,
                    error_message,
                    triggered_by
                )
                VALUES (%s, 'registration_invitation', %s, %s, 'failed', %s, %s)
            """, (
                recipient_email,
                subject,
                message_body,
                str(e),
                session.get('user_id')
            ))

            conn.commit()

        return redirect(url_for('vhan.email_logs'))

                

    cursor.execute("""
        SELECT
            en.id,
            en.recipient_email,
            en.notification_type,
            en.subject,
            en.message_body,
            en.send_status,
            en.sent_at,
            en.error_message,
            COALESCE(o.company_name, 'System') AS triggered_by_company
        FROM email_notifications en
        LEFT JOIN organizations o
            ON en.organization_id = o.id
        ORDER BY en.created_at DESC
    """)

    email_logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'vhan_email.html',
        email_logs=email_logs
    )