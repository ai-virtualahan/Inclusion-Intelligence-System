import re

from flask import Blueprint, flash, redirect, request, session, url_for
from flask_mail import Message

from db import get_db_connection
from extensions import mail
from settings_utils import load_system_settings


contact_bp = Blueprint("contact", __name__)

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)

PUBLIC_INQUIRY_TYPES = {
    "registration": "Registration",
    "fellowship": "Fellowship",
    "partnership": "Partnership",
    "others": "Others",
}

ORGANIZATION_ISSUE_TYPES = {
    "account_access": "Account Access",
    "assessment_scoring": "Assessment or Scoring",
    "technical_issue": "Technical Issue",
    "reports": "Reports",
    "others": "Others",
}


def _valid_email(email):
    return bool(email and EMAIL_PATTERN.fullmatch(email))


def _send_inquiry_email(recipient, reply_to, subject, body):
    msg = Message(
        subject=subject,
        recipients=[recipient],
        body=body,
        reply_to=reply_to,
    )
    mail.send(msg)


def _save_inquiry(
    cursor,
    source,
    contact_name,
    contact_email,
    inquiry_type,
    subject,
    message,
    user_id=None,
    organization_id=None,
):
    cursor.execute(
        """
        INSERT INTO contact_inquiries (
            source,
            user_id,
            organization_id,
            contact_name,
            contact_email,
            inquiry_type,
            subject,
            message
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            source,
            user_id,
            organization_id,
            contact_name,
            contact_email,
            inquiry_type,
            subject,
            message,
        ),
    )
    return cursor.lastrowid


def _update_email_status(cursor, inquiry_id, status, error=None):
    cursor.execute(
        """
        UPDATE contact_inquiries
        SET email_status = %s,
            email_error = %s
        WHERE id = %s
        """,
        (status, error, inquiry_id),
    )


@contact_bp.route("/contact/inquiry", methods=["POST"])
def public_inquiry():
    if request.form.get("website"):
        return redirect(f"{url_for('home')}#contact")

    contact_name = (request.form.get("contact_name") or "").strip()
    contact_email = (request.form.get("contact_email") or "").strip().lower()
    inquiry_key = (request.form.get("inquiry_type") or "").strip()
    message = (request.form.get("message") or "").strip()
    inquiry_type = PUBLIC_INQUIRY_TYPES.get(inquiry_key)

    if not contact_name or not contact_email or not inquiry_type or not message:
        flash("Please complete all required contact fields.", "warning")
        return redirect(f"{url_for('home')}#contact")

    if not _valid_email(contact_email):
        flash("Please enter a valid email address.", "warning")
        return redirect(f"{url_for('home')}#contact")

    if len(contact_name) > 150 or len(message) > 5000:
        flash("Your contact form entry is too long.", "warning")
        return redirect(f"{url_for('home')}#contact")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        settings = load_system_settings(cursor)
        subject = f"Public inquiry: {inquiry_type}"
        inquiry_id = _save_inquiry(
            cursor,
            "public",
            contact_name,
            contact_email,
            inquiry_type,
            subject,
            message,
        )
        conn.commit()

        email_subject = f"[IIS Contact #{inquiry_id}] {inquiry_type} inquiry"
        email_body = (
            f"New public inquiry received through the Inclusion Intelligence System.\n\n"
            f"Inquiry ID: {inquiry_id}\n"
            f"Name: {contact_name}\n"
            f"Email: {contact_email}\n"
            f"Type: {inquiry_type}\n\n"
            f"Message:\n{message}"
        )

        try:
            _send_inquiry_email(
                settings["support_email"],
                contact_email,
                email_subject,
                email_body,
            )
            _update_email_status(cursor, inquiry_id, "sent")
            conn.commit()
            flash("Thank you. Your inquiry has been sent to the Virtualahan team.", "success")
        except Exception as exc:
            _update_email_status(cursor, inquiry_id, "failed", str(exc))
            conn.commit()
            flash(
                "Your inquiry was saved, but the email notification could not be sent. "
                "The Virtualahan team can still review it.",
                "warning",
            )
    except Exception:
        conn.rollback()
        flash("Unable to submit your inquiry right now. Please try again later.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(f"{url_for('home')}#contact")


@contact_bp.route("/contact/organization", methods=["POST"])
def organization_inquiry():
    user_id = session.get("user_id")
    if not user_id or session.get("role") != "org_admin":
        flash("Please log in with an organization account to submit a support request.", "warning")
        return redirect(url_for("login.login"))

    issue_key = (request.form.get("inquiry_type") or "").strip()
    subject = (request.form.get("subject") or "").strip()
    message = (request.form.get("message") or "").strip()
    inquiry_type = ORGANIZATION_ISSUE_TYPES.get(issue_key)

    if not inquiry_type or not subject or not message:
        flash("Please complete all required support request fields.", "warning")
        return redirect(url_for("assessment", page="contact"))

    if len(subject) > 200 or len(message) > 5000:
        flash("Your support request is too long.", "warning")
        return redirect(url_for("assessment", page="contact"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                u.id,
                u.organization_id,
                u.contact_person,
                u.work_email,
                o.company_name
            FROM users u
            LEFT JOIN organizations o
                ON o.id = u.organization_id
            WHERE u.id = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            flash("Your organization account could not be found.", "danger")
            return redirect(url_for("assessment", page="contact"))

        settings = load_system_settings(cursor)
        inquiry_id = _save_inquiry(
            cursor,
            "organization",
            user["contact_person"],
            user["work_email"],
            inquiry_type,
            subject,
            message,
            user_id=user["id"],
            organization_id=user["organization_id"],
        )
        conn.commit()

        company_name = user["company_name"] or "Organization not specified"
        email_subject = f"[IIS Support #{inquiry_id}] {company_name}: {subject}"
        email_body = (
            f"New organization support request received.\n\n"
            f"Inquiry ID: {inquiry_id}\n"
            f"Organization: {company_name}\n"
            f"Contact: {user['contact_person']}\n"
            f"Email: {user['work_email']}\n"
            f"Issue type: {inquiry_type}\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}"
        )

        try:
            _send_inquiry_email(
                settings["support_email"],
                user["work_email"],
                email_subject,
                email_body,
            )
            _update_email_status(cursor, inquiry_id, "sent")
            conn.commit()
            flash("Your support request has been sent to the Virtualahan team.", "success")
        except Exception as exc:
            _update_email_status(cursor, inquiry_id, "failed", str(exc))
            conn.commit()
            flash(
                "Your support request was saved, but the email notification could not be sent.",
                "warning",
            )
    except Exception:
        conn.rollback()
        flash("Unable to submit your support request right now. Please try again later.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("assessment", page="contact"))
