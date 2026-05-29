from flask_mail import Message

from extensions import mail
from settings_utils import get_bool_setting


def find_existing_registration(cursor, email):
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return "missing"

    cursor.execute("""
        SELECT id
        FROM users
        WHERE LOWER(work_email) = %s
        LIMIT 1
    """, (normalized_email,))
    if cursor.fetchone():
        return "registered"

    cursor.execute("""
        SELECT id, status
        FROM access_requests
        WHERE LOWER(work_email) = %s
        LIMIT 1
    """, (normalized_email,))
    request_row = cursor.fetchone()
    if request_row:
        return request_row["status"] if isinstance(request_row, dict) else request_row[1]

    return None


def send_account_approval_email(cursor, req, user_id, organization_id, reviewer_id):
    subject = "Account Approved - Inclusion Intelligence System"
    message_body = f"""Hello {req['contact_person']},

Your organization, {req['company_name']}, has been approved for the Inclusion Intelligence System.

You may now log in using your registered work email:
{req['work_email']}

Thank you,
Inclusion Intelligence System Team"""

    try:
        msg = Message(
            subject=subject,
            recipients=[req["work_email"]],
            body=message_body
        )
        mail.send(msg)

        cursor.execute("""
            INSERT INTO email_notifications (
                user_id,
                organization_id,
                notification_type,
                recipient_email,
                subject,
                message_body,
                send_status,
                sent_at,
                triggered_by
            )
            VALUES (%s, %s, 'account_approval', %s, %s, %s, 'sent', NOW(), %s)
        """, (
            user_id,
            organization_id,
            req["work_email"],
            subject,
            message_body,
                reviewer_id
        ))
        return True
    except Exception as e:
        cursor.execute("""
            INSERT INTO email_notifications (
                user_id,
                organization_id,
                notification_type,
                recipient_email,
                subject,
                message_body,
                send_status,
                error_message,
                triggered_by
            )
            VALUES (%s, %s, 'account_approval', %s, %s, %s, 'failed', %s, %s)
        """, (
            user_id,
            organization_id,
            req["work_email"],
            subject,
            message_body,
            str(e),
                reviewer_id
        ))
        return False


def approve_access_request(cursor, req_id, reviewer_id):
    cursor.execute("""
        SELECT *
        FROM access_requests
        WHERE id = %s
    """, (req_id,))
    req = cursor.fetchone()

    if not req:
        return False, "Access request not found.", "danger"

    if req["status"] != "pending":
        return False, "Only pending requests can be approved.", "warning"

    duplicate_status = find_existing_registration(cursor, req["work_email"])
    if duplicate_status == "registered":
        return False, "This email is already registered and cannot be approved again.", "warning"

    cursor.execute("""
        INSERT INTO organizations (
            company_name,
            industry,
            company_size,
            company_number,
            status,
            approved_at,
            approved_by
        )
        VALUES (%s, %s, %s, %s, 'approved', NOW(), %s)
    """, (
        req["company_name"],
        req["industry"],
        req["company_size"],
        req["company_number"],
        reviewer_id
    ))
    org_id = cursor.lastrowid

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
        req["contact_person"],
        req["work_email"],
        req["password_hash"],
        req["contact_number"],
        req["position_title"]
    ))
    new_user_id = cursor.lastrowid

    cursor.execute("""
        UPDATE access_requests
        SET status = 'approved',
            reviewed_by = %s,
            reviewed_at = NOW()
        WHERE id = %s
    """, (reviewer_id, req_id))

    if not get_bool_setting(cursor, "auto_send_approval_email", True):
        return True, "Access request approved. Approval email sending is currently disabled.", "success"

    email_sent = send_account_approval_email(cursor, req, new_user_id, org_id, reviewer_id)
    if email_sent:
        return True, "Access request approved and confirmation email sent.", "success"
    return True, "Access request approved, but the confirmation email failed. Check email logs.", "warning"
