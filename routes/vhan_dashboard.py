from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db import get_db_connection
from flask_mail import Message
from extensions import mail
from routes.access_request_utils import approve_access_request, find_existing_registration
from settings_utils import can_role_approve_access_requests, get_bool_setting, load_system_settings

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

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM organizations
        WHERE status = 'approved'
    """)
    approved_organizations = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM email_notifications
    """)
    email_logs_count = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM reports
    """)
    reports_count = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template(
        'vhan_dashboard.html',
        requests=requests,
        approved_organizations=approved_organizations,
        email_logs_count=email_logs_count,
        reports_count=reports_count
    )


@vhan_bp.route('/vhan/approve/<int:req_id>', methods=['POST'])
def approve_request(req_id):
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if not can_role_approve_access_requests(cursor, session.get('role')):
            flash("VHAN Admin approval is disabled in System Settings.", "warning")
            return redirect(url_for('vhan.vhan_dashboard'))

        _, message, category = approve_access_request(cursor, req_id, session.get('user_id'))
        conn.commit()
        flash(message, category)
    except Exception as e:
        conn.rollback()
        flash(f"Unable to approve access request: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('vhan.vhan_dashboard'))


@vhan_bp.route('/vhan/reject/<int:req_id>', methods=['POST'])
def reject_request(req_id):
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    require_reason = get_bool_setting(cursor, "require_rejection_reason", True)
    rejection_reason = (request.form.get('rejection_reason') or '').strip()
    if require_reason and not rejection_reason:
        cursor.close()
        conn.close()
        flash("Please provide a rejection reason before rejecting this request.", "warning")
        return redirect(url_for('vhan.pending_approvals'))

    cursor.execute("""
        SELECT id, status
        FROM access_requests
        WHERE id = %s
    """, (req_id,))
    req = cursor.fetchone()

    if not req:
        cursor.close()
        conn.close()
        flash("Access request not found.", "danger")
        return redirect(url_for('vhan.pending_approvals'))

    if req['status'] != 'pending':
        cursor.close()
        conn.close()
        flash("Only pending requests can be rejected.", "warning")
        return redirect(url_for('vhan.pending_approvals'))

    cursor.execute("""
        UPDATE access_requests
        SET status = 'rejected',
            reviewed_by = %s,
            reviewed_at = NOW(),
            rejection_reason = %s
        WHERE id = %s
    """, (
        session.get('user_id'),
        rejection_reason or 'Rejected by VHAN admin.',
        req_id
    ))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Access request rejected successfully.", "success")
    return redirect(url_for('vhan.pending_approvals'))


@vhan_bp.route('/vhan/pending-approvals')
def pending_approvals():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    settings = load_system_settings(cursor)

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

    return render_template('pending_approvals.html', requests=requests, settings=settings)


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
        existing_registration = find_existing_registration(cursor, recipient_email)
        if existing_registration:
            flash("Invitation not sent. This email is already registered or has an access request.", "warning")
            cursor.close()
            conn.close()
            return redirect(url_for('vhan.email_logs'))

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
