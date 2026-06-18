import secrets
from datetime import datetime, timedelta

from flask_mail import Message

from extensions import mail
from routes.access_request_utils import find_existing_registration
from routes.register import is_valid_email, send_verification_email, verification_token_hash
from settings_utils import load_system_settings


VALID_INQUIRY_STATUSES = {"new", "in_progress", "resolved"}
VALID_INQUIRY_SOURCES = {"public", "organization"}
VALID_INQUIRY_CATEGORIES = {
    "registration_correction",
    "account_access",
    "assessment_question",
    "scoring_report",
    "technical_issue",
    "general_inquiry",
}
CORRECTABLE_REQUEST_STATUSES = {"email_unverified", "pending", "rejected"}
PROFILE_FIELDS = {
    "company_name",
    "industry",
    "company_size",
    "company_number",
    "contact_person",
    "position_title",
    "contact_number",
}


def list_contact_inquiries(cursor, status_filter=None, source_filter=None):
    filters = []
    params = []

    if status_filter in VALID_INQUIRY_STATUSES:
        filters.append("ci.status = %s")
        params.append(status_filter)

    if source_filter in VALID_INQUIRY_SOURCES:
        filters.append("ci.source = %s")
        params.append(source_filter)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    cursor.execute(
        f"""
        SELECT
            ci.id,
            ci.source,
            ci.user_id,
            ci.organization_id,
            ci.contact_name,
            ci.contact_email,
            ci.inquiry_type,
            ci.subject,
            ci.message,
            ci.status,
            ci.category,
            ci.admin_notes,
            ci.resolution_message,
            ci.resolved_at,
            ci.last_response_at,
            ci.email_status,
            ci.email_error,
            ci.created_at,
            ci.updated_at,
            o.company_name,
            u.work_email AS registered_email
        FROM contact_inquiries ci
        LEFT JOIN organizations o
            ON ci.organization_id = o.id
        LEFT JOIN users u
            ON ci.user_id = u.id
        {where_clause}
        ORDER BY
            FIELD(ci.status, 'new', 'in_progress', 'resolved'),
            ci.created_at DESC
        """,
        params,
    )
    return cursor.fetchall()


def count_contact_inquiries_by_status(cursor):
    cursor.execute(
        """
        SELECT status, COUNT(*) AS total
        FROM contact_inquiries
        GROUP BY status
        """
    )
    return {row["status"]: row["total"] for row in cursor.fetchall()}


def set_contact_inquiry_status(cursor, inquiry_id, status):
    if status not in VALID_INQUIRY_STATUSES:
        return False, "Please choose a valid inquiry status.", "danger"

    cursor.execute("SELECT id FROM contact_inquiries WHERE id = %s", (inquiry_id,))
    if not cursor.fetchone():
        return False, "Inquiry not found.", "danger"

    cursor.execute(
        """
        UPDATE contact_inquiries
        SET status = %s
        WHERE id = %s
        """,
        (status, inquiry_id),
    )

    return True, "Inquiry status updated.", "success"


def update_inquiry_resolution(cursor, inquiry_id, category, admin_notes, resolution_message, status, reviewer_id):
    category = (category or "").strip()
    admin_notes = (admin_notes or "").strip()
    resolution_message = (resolution_message or "").strip()

    if category and category not in VALID_INQUIRY_CATEGORIES:
        return False, "Please choose a valid inquiry category.", "danger"

    if status and status not in VALID_INQUIRY_STATUSES:
        return False, "Please choose a valid inquiry status.", "danger"

    cursor.execute("SELECT id FROM contact_inquiries WHERE id = %s", (inquiry_id,))
    if not cursor.fetchone():
        return False, "Inquiry not found.", "danger"

    cursor.execute(
        """
        UPDATE contact_inquiries
        SET category = NULLIF(%s, ''),
            admin_notes = NULLIF(%s, ''),
            resolution_message = NULLIF(%s, ''),
            status = COALESCE(NULLIF(%s, ''), status),
            resolved_at = CASE
                WHEN %s = 'resolved' THEN COALESCE(resolved_at, NOW())
                WHEN %s IN ('new', 'in_progress') THEN NULL
                ELSE resolved_at
            END,
            resolved_by = CASE
                WHEN %s = 'resolved' THEN %s
                WHEN %s IN ('new', 'in_progress') THEN NULL
                ELSE resolved_by
            END
        WHERE id = %s
        """,
        (
            category,
            admin_notes,
            resolution_message,
            status,
            status,
            status,
            status,
            reviewer_id,
            status,
            inquiry_id,
        ),
    )

    return True, "Inquiry details saved.", "success"


def _email_used_by_other(cursor, email, user_id=None, access_request_id=None):
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE LOWER(work_email) = %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (email, user_id, user_id),
    )
    if cursor.fetchone():
        return True

    cursor.execute(
        """
        SELECT id
        FROM access_requests
        WHERE LOWER(work_email) = %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (email, access_request_id, access_request_id),
    )
    return bool(cursor.fetchone())


def _find_target_by_email(cursor, email):
    email = (email or "").strip().lower()
    if not email:
        return None

    cursor.execute(
        """
        SELECT 'access_request' AS target_type, id, NULL AS user_id, NULL AS organization_id,
               status, contact_person, work_email
        FROM access_requests
        WHERE LOWER(work_email) = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (email,),
    )
    target = cursor.fetchone()
    if target:
        return target

    cursor.execute(
        """
        SELECT 'user' AS target_type, NULL AS id, id AS user_id, organization_id,
               status, contact_person, work_email
        FROM users
        WHERE LOWER(work_email) = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (email,),
    )
    return cursor.fetchone()


def _find_correction_target(cursor, inquiry_id, current_email):
    target = _find_target_by_email(cursor, current_email)
    if target:
        return target

    cursor.execute(
        """
        SELECT id, user_id, organization_id, contact_email
        FROM contact_inquiries
        WHERE id = %s
        """,
        (inquiry_id,),
    )
    inquiry = cursor.fetchone()
    if not inquiry:
        return None

    if inquiry["user_id"]:
        cursor.execute(
            """
            SELECT 'user' AS target_type, NULL AS id, id AS user_id, organization_id,
                   status, contact_person, work_email
            FROM users
            WHERE id = %s
            """,
            (inquiry["user_id"],),
        )
        target = cursor.fetchone()
        if target:
            return target

    fallback_email = (inquiry["contact_email"] or "").strip().lower()
    if fallback_email:
        return _find_target_by_email(cursor, fallback_email)

    return None


def _non_empty_profile_updates(form):
    updates = {}
    for field in PROFILE_FIELDS:
        value = (form.get(field) or "").strip()
        if value:
            updates[field] = value
    return updates


def _apply_access_request_updates(cursor, target, updates, corrected_email):
    assignments = []
    values = []

    field_map = {
        "company_name": "company_name",
        "industry": "industry",
        "company_size": "company_size",
        "company_number": "company_number",
        "contact_person": "contact_person",
        "position_title": "position_title",
        "contact_number": "contact_number",
    }

    for form_field, column in field_map.items():
        if form_field in updates:
            assignments.append(f"{column} = %s")
            values.append(updates[form_field])

    email_changed = bool(corrected_email and corrected_email != target["work_email"].lower())
    if email_changed:
        if target["status"] not in CORRECTABLE_REQUEST_STATUSES:
            return False, "Only unverified, pending, or rejected access requests can change email here.", "warning"

        if _email_used_by_other(cursor, corrected_email, access_request_id=target["id"]):
            return False, "The corrected email is already used by another account or request.", "warning"

        token = secrets.token_urlsafe(32)
        assignments.extend([
            "work_email = %s",
            "verification_token_hash = %s",
            "verification_token_expiry = %s",
            "email_verified_at = NULL",
            "status = 'email_unverified'",
        ])
        values.extend([
            corrected_email,
            verification_token_hash(token),
            datetime.now() + timedelta(hours=24),
        ])
    else:
        token = None

    if not assignments:
        return False, "Enter at least one field to correct.", "warning"

    values.append(target["id"])
    cursor.execute(
        f"""
        UPDATE access_requests
        SET {', '.join(assignments)}
        WHERE id = %s
        """,
        values,
    )

    if email_changed:
        contact_person = updates.get("contact_person") or target["contact_person"]
        email_sent = send_verification_email(cursor, corrected_email, contact_person, token)
        if not email_sent:
            return True, "Profile updated, but the verification email failed. Check Email Logs.", "warning"

    return True, "Registration profile updated successfully.", "success"


def _apply_user_updates(cursor, target, updates, corrected_email):
    user_assignments = []
    user_values = []
    org_assignments = []
    org_values = []

    user_map = {
        "contact_person": "contact_person",
        "position_title": "position_title",
        "contact_number": "contact_number",
    }
    org_map = {
        "company_name": "company_name",
        "industry": "industry",
        "company_size": "company_size",
        "company_number": "company_number",
    }

    for form_field, column in user_map.items():
        if form_field in updates:
            user_assignments.append(f"{column} = %s")
            user_values.append(updates[form_field])

    for form_field, column in org_map.items():
        if form_field in updates:
            org_assignments.append(f"{column} = %s")
            org_values.append(updates[form_field])

    email_changed = bool(corrected_email and corrected_email != target["work_email"].lower())
    if email_changed:
        if _email_used_by_other(cursor, corrected_email, user_id=target["user_id"]):
            return False, "The corrected email is already used by another account or request.", "warning"
        user_assignments.append("work_email = %s")
        user_values.append(corrected_email)

    if not user_assignments and not org_assignments:
        return False, "Enter at least one field to correct.", "warning"

    if user_assignments:
        user_values.append(target["user_id"])
        cursor.execute(
            f"""
            UPDATE users
            SET {', '.join(user_assignments)}
            WHERE id = %s
            """,
            user_values,
        )

    if org_assignments and target["organization_id"]:
        org_values.append(target["organization_id"])
        cursor.execute(
            f"""
            UPDATE organizations
            SET {', '.join(org_assignments)}
            WHERE id = %s
            """,
            org_values,
        )

    return True, "Organization profile updated successfully.", "success"


def apply_inquiry_profile_correction(cursor, inquiry_id, form):
    current_email = (form.get("current_email") or "").strip().lower()
    corrected_email = (form.get("work_email") or "").strip().lower()

    if current_email and not is_valid_email(current_email):
        return False, "Enter a valid current email address.", "danger"

    if corrected_email and not is_valid_email(corrected_email):
        return False, "Enter a valid corrected work email address.", "danger"

    target = _find_correction_target(cursor, inquiry_id, current_email)
    if not target:
        return False, "No matching registration or user account was found.", "danger"

    updates = _non_empty_profile_updates(form)

    if target["target_type"] == "access_request":
        success, message, category = _apply_access_request_updates(cursor, target, updates, corrected_email)
    else:
        success, message, category = _apply_user_updates(cursor, target, updates, corrected_email)

    if success:
        cursor.execute(
            """
            UPDATE contact_inquiries
            SET status = CASE
                    WHEN status = 'resolved' THEN status
                    ELSE 'in_progress'
                END,
                category = COALESCE(category, 'registration_correction')
            WHERE id = %s
            """,
            (inquiry_id,),
        )

    return success, message, category


def correct_registration_email(cursor, inquiry_id, current_email, corrected_email):
    current_email = (current_email or "").strip().lower()
    corrected_email = (corrected_email or "").strip().lower()

    if not is_valid_email(current_email) or not is_valid_email(corrected_email):
        return False, "Enter both the current and corrected email addresses.", "danger"

    if current_email == corrected_email:
        return False, "The corrected email must be different from the current email.", "warning"

    cursor.execute(
        """
        SELECT id, status, contact_person
        FROM access_requests
        WHERE LOWER(work_email) = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (current_email,),
    )
    access_request = cursor.fetchone()

    if not access_request:
        return False, "No access request was found for the current email.", "danger"

    if access_request["status"] not in CORRECTABLE_REQUEST_STATUSES:
        return (
            False,
            "Only unverified, pending, or rejected access requests can be corrected here.",
            "warning",
        )

    duplicate_status = find_existing_registration(cursor, corrected_email)
    if duplicate_status:
        return False, "The corrected email is already used by another account or request.", "warning"

    token = secrets.token_urlsafe(32)
    token_hash = verification_token_hash(token)
    token_expiry = datetime.now() + timedelta(hours=24)

    cursor.execute(
        """
        UPDATE access_requests
        SET work_email = %s,
            verification_token_hash = %s,
            verification_token_expiry = %s,
            email_verified_at = NULL,
            status = 'email_unverified'
        WHERE id = %s
        """,
        (corrected_email, token_hash, token_expiry, access_request["id"]),
    )

    cursor.execute(
        """
        UPDATE contact_inquiries
        SET status = CASE
                WHEN status = 'resolved' THEN status
                ELSE 'in_progress'
            END
        WHERE id = %s
        """,
        (inquiry_id,),
    )

    email_sent = send_verification_email(
        cursor,
        corrected_email,
        access_request["contact_person"],
        token,
    )

    if email_sent:
        return True, "Registration email corrected and verification email resent.", "success"

    return (
        True,
        "Registration email corrected, but the verification email failed. Check Email Logs.",
        "warning",
    )


def send_inquiry_response(cursor, inquiry_id, response_message, sender_id):
    response_message = (response_message or "").strip()
    if not response_message:
        return False, "Write a response message before sending.", "warning"

    cursor.execute(
        """
        SELECT *
        FROM contact_inquiries
        WHERE id = %s
        """,
        (inquiry_id,),
    )
    inquiry = cursor.fetchone()
    if not inquiry:
        return False, "Inquiry not found.", "danger"

    settings = load_system_settings(cursor)
    subject = f"Re: {inquiry['subject']}"
    message_body = (
        f"Hello {inquiry['contact_name']},\n\n"
        f"{response_message}\n\n"
        f"Thank you,\n"
        f"{settings['primary_contact']}"
    )

    send_status = "sent"
    error_message = None
    try:
        msg = Message(
            subject=subject,
            recipients=[inquiry["contact_email"]],
            body=message_body,
            reply_to=settings["support_email"],
        )
        mail.send(msg)
    except Exception as exc:
        send_status = "failed"
        error_message = str(exc)

    cursor.execute(
        """
        INSERT INTO email_notifications (
            user_id,
            organization_id,
            notification_type,
            recipient_email,
            subject,
            message_body,
            send_status,
            sent_at,
            error_message,
            triggered_by
        )
        VALUES (
            %s,
            %s,
            'support_response',
            %s,
            %s,
            %s,
            %s,
            CASE WHEN %s = 'sent' THEN NOW() ELSE NULL END,
            %s,
            %s
        )
        """,
        (
            inquiry["user_id"],
            inquiry["organization_id"],
            inquiry["contact_email"],
            subject,
            message_body,
            send_status,
            send_status,
            error_message,
            sender_id,
        ),
    )

    cursor.execute(
        """
        UPDATE contact_inquiries
        SET resolution_message = %s,
            last_response_at = CASE WHEN %s = 'sent' THEN NOW() ELSE last_response_at END,
            status = CASE WHEN %s = 'sent' THEN 'resolved' ELSE status END,
            resolved_at = CASE WHEN %s = 'sent' THEN COALESCE(resolved_at, NOW()) ELSE resolved_at END,
            resolved_by = CASE WHEN %s = 'sent' THEN %s ELSE resolved_by END
        WHERE id = %s
        """,
        (
            response_message,
            send_status,
            send_status,
            send_status,
            send_status,
            sender_id,
            inquiry_id,
        ),
    )

    if send_status == "sent":
        return True, "Response email sent and inquiry marked resolved.", "success"

    return True, "Response saved, but email sending failed. Check Email Logs.", "warning"
