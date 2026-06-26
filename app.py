import hmac
import secrets
import time

from flask import Flask, abort, flash, render_template, request, redirect, session, url_for, jsonify
from collections import OrderedDict
from mysql.connector import Error as MySQLError
from db import get_db_connection
from assessment_scoring import compute_assessment_scores
from datetime import datetime, timedelta
from settings_utils import get_bool_setting, get_int_setting, load_system_settings

from routes.login import login_bp
from routes.super_dashboard import super_admin_bp
from routes.vhan_dashboard import vhan_bp
from routes.register import register_bp
from routes.org_dashboard import org_dashboard_bp
from routes.contact import contact_bp

from extensions import mail

app = Flask(__name__)

# App config
app.config.from_object('config')

mail.init_app(app)

ASSESSMENT_SUBMIT_MAX_ATTEMPTS = 3
ASSESSMENT_SUBMIT_RETRY_ERRORS = {1205, 1213}

# Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(super_admin_bp)
app.register_blueprint(vhan_bp)
app.register_blueprint(register_bp)
app.register_blueprint(org_dashboard_bp)
app.register_blueprint(contact_bp)


def csrf_token():
    session.permanent = True
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def public_form_token(form_name):
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    payload = f"{form_name}|{timestamp}|{nonce}"
    signature = hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        payload.encode("utf-8"),
        "sha256"
    ).hexdigest()
    return f"{timestamp}:{nonce}:{signature}"


def valid_public_form_token(token, form_name):
    try:
        timestamp, nonce, signature = (token or "").split(":", 2)
        token_age = time.time() - int(timestamp)
    except (TypeError, ValueError):
        return False

    max_age = app.config.get("REGISTRATION_FORM_TOKEN_LIFETIME_SECONDS", 3600)
    if token_age < 0 or token_age > max_age:
        return False

    payload = f"{form_name}|{timestamp}|{nonce}"
    expected_signature = hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        payload.encode("utf-8"),
        "sha256"
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


@app.context_processor
def inject_csrf_token():
    current_user_dashboard_url = (
        dashboard_url_for_role(session.get("role"))
        if session.get("user_id")
        else None
    )
    return {
        "csrf_token": csrf_token,
        "public_form_token": public_form_token,
        "current_user_dashboard_url": current_user_dashboard_url,
    }


@app.before_request
def enforce_session_timeout():
    if request.endpoint in {None, "static", "login.logout"}:
        return None

    if not session.get("user_id"):
        return None

    now = datetime.now()
    timeout_minutes = app.config["PERMANENT_SESSION_LIFETIME"].seconds // 60

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        timeout_minutes = get_int_setting(cursor, "session_timeout_minutes", timeout_minutes)
    except Exception:
        pass
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    last_activity = session.get("_last_activity_at")
    if last_activity:
        try:
            last_activity_at = datetime.fromisoformat(last_activity)
            if now - last_activity_at > timedelta(minutes=timeout_minutes):
                session.clear()
                flash("Your session expired. Please log in again.", "warning")
                return redirect(url_for("login.login"))
        except ValueError:
            session.pop("_last_activity_at", None)

    session.permanent = True
    session["_last_activity_at"] = now.isoformat()
    return None


@app.before_request
def protect_post_requests():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return None

    if request.endpoint is None:
        return None

    expected_token = session.get("_csrf_token")
    submitted_token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")

    session_token_is_valid = (
        expected_token
        and submitted_token
        and hmac.compare_digest(expected_token, submitted_token)
    )
    registration_token_is_valid = (
        request.endpoint == "register.submit_registration"
        and valid_public_form_token(submitted_token, "registration")
    )

    if not session_token_is_valid and not registration_token_is_valid:
        if request.endpoint == "register.submit_registration":
            session.pop("_csrf_token", None)
            flash("Your registration form token expired. Please review the form and submit again.", "warning")
            return redirect(url_for("register.register"))
        abort(400, description="Invalid or missing CSRF token.")

    return None


def current_user_org_status(cursor, user_id):
    cursor.execute("""
        SELECT u.organization_id, o.status AS organization_status
        FROM users u
        LEFT JOIN organizations o
            ON u.organization_id = o.id
        WHERE u.id = %s
    """, (user_id,))
    return cursor.fetchone()


def assessment_is_locked_for_org(cursor, organization_status):
    return (
        organization_status == "suspended"
        and get_bool_setting(cursor, "suspend_lock_assessments", True)
    )


def is_retryable_mysql_error(error):
    return isinstance(error, MySQLError) and getattr(error, "errno", None) in ASSESSMENT_SUBMIT_RETRY_ERRORS


def wants_plain_text_response():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@app.errorhandler(500)
def handle_internal_server_error(error):
    original_error = getattr(error, "original_exception", None)
    if request.endpoint == "submit_assessment" and wants_plain_text_response():
        app.logger.exception("Unhandled assessment submission error")
        return f"Error: {original_error or error}", 500
    return error


def assessment_locked_response(lock_title=None, lock_message=None, next_eligible=None, status=403):
    if wants_plain_text_response():
        if lock_message:
            return lock_message, status
        if next_eligible:
            return f"Assessment locked until {next_eligible}.", status
        return "Assessment submission is currently locked.", status

    return render_template(
        'assessment_locked.html',
        lock_title=lock_title,
        lock_message=lock_message,
        next_eligible=next_eligible
    ), status


def dashboard_url_for_role(role):
    dashboard_endpoints = {
        "org_admin": "assessment",
        "vhan_admin": "vhan.vhan_dashboard",
        "super_admin": "super_admin.super_dashboard",
    }
    endpoint = dashboard_endpoints.get(role)
    return url_for(endpoint) if endpoint else url_for("login.login")


@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(DISTINCT organization_id) AS organizations_assessed
        FROM assessments
        WHERE status = 'completed'
    """)
    organizations_assessed = cursor.fetchone()['organizations_assessed']

    cursor.execute("""
        SELECT COUNT(*) AS completed_assessments
        FROM assessments
        WHERE status = 'completed'
    """)
    completed_assessments = cursor.fetchone()['completed_assessments']

    settings = load_system_settings(cursor)

    cursor.close()
    conn.close()
    is_logged_in = bool(session.get("user_id"))
    dashboard_url = dashboard_url_for_role(session.get("role")) if is_logged_in else None

    return render_template(
        'home.html',
        organizations_assessed=organizations_assessed,
        completed_assessments=completed_assessments,
        support_email=settings["support_email"],
        is_logged_in=is_logged_in,
        dashboard_url=dashboard_url,
    )


@app.route('/assessment')
def assessment():
    user_id = session.get('user_id')
    profile = {k: '' for k in ['full_name','position','work_email','contact_number',
                                'company_name','company_size','industry','company_number']}
    active_exams = OrderedDict()
    assessment_lock = {
        "locked": False,
        "reason": "",
        "next_eligible": None,
    }

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if user_id:
        org_status = current_user_org_status(cursor, user_id)
        if org_status and assessment_is_locked_for_org(cursor, org_status.get("organization_status")):
            cursor.close()
            conn.close()
            return render_template(
                'assessment_locked.html',
                lock_title="Assessment Access Locked",
                lock_message=(
                    "Your organization is currently suspended. Assessment access is locked "
                    "until the organization is reactivated by an administrator."
                ),
                next_eligible=None
            ), 403

        cursor.execute("""
            SELECT u.contact_person AS full_name, u.position_title AS position,
                   u.work_email, u.contact_number,
                   o.company_name, o.company_size, o.industry, o.company_number
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE u.id = %s
        """, (user_id,))
        result = cursor.fetchone()
        if result:
            profile = {k: (v or '') for k, v in result.items()}

        if org_status and org_status.get("organization_id"):
            cursor.execute("""
                SELECT submitted_at FROM assessments
                WHERE organization_id = %s AND status = 'completed'
                ORDER BY submitted_at DESC LIMIT 1
            """, (org_status["organization_id"],))
            last = cursor.fetchone()
            if last and last['submitted_at']:
                last_date = last['submitted_at']
                if isinstance(last_date, str):
                    last_date = datetime.fromisoformat(last_date)
                lock_days = get_int_setting(cursor, "reassessment_lock_days", 182)
                unlock_date = last_date + timedelta(days=lock_days)
                if datetime.now() < unlock_date:
                    assessment_lock = {
                        "locked": True,
                        "reason": "reassessment",
                        "next_eligible": unlock_date.strftime("%B %d, %Y"),
                    }

    cursor.execute("""
        SELECT
            qb.id AS question_id,
            qb.question_text,
            ad.name AS dimension_name,
            ad.id AS dimension_id,
            qc.id AS choice_id,
            qc.choice_letter,
            qc.choice_text,
            qc.choice_score
        FROM question_bank qb
        JOIN assessment_dimensions ad
            ON qb.dimension_id = ad.id
        JOIN question_choices qc
            ON qb.id = qc.question_id
        WHERE qb.is_active = 1
        ORDER BY
            ad.id ASC,
            COALESCE(qb.version_group_id, qb.id) ASC,
            qb.id ASC,
            qc.choice_letter ASC
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    for row in rows:
        dim_name = row['dimension_name']
        if dim_name not in active_exams:
            active_exams[dim_name] = {
                "title": dim_name,
                "startQuestionId": row['question_id'],
                "questions": []
            }

        questions = active_exams[dim_name]["questions"]
        if not questions or questions[-1]["id"] != row['question_id']:
            questions.append({
                "id": row['question_id'],
                "text": row['question_text'],
                "choices": []
            })

        questions[-1]["choices"].append({
            "id": row['choice_id'],
            "letter": row['choice_letter'],
            "text": row['choice_text'],
            "score": float(row['choice_score'])
        })

    return render_template(
        'assessment.html',
        profile=profile,
        active_exams=active_exams,
        assessment_lock=assessment_lock,
        assessment_storage_namespace=f"user:{user_id}" if user_id else "guest"
    )


@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get user's organization_id
    cursor.execute("SELECT organization_id FROM users WHERE id = %s", (user_id,))
    user_row = cursor.fetchone()
    if not user_row or not user_row['organization_id']:
        cursor.close()
        conn.close()
        return "Error: No organization linked to your account.", 400

    organization_id = user_row['organization_id']

    cursor.execute("SELECT status FROM organizations WHERE id = %s", (organization_id,))
    organization = cursor.fetchone()
    if organization and assessment_is_locked_for_org(cursor, organization.get("status")):
        cursor.close()
        conn.close()
        return assessment_locked_response(
            lock_title="Assessment Access Locked",
            lock_message=(
                "Your organization is currently suspended. Assessment submissions are locked "
                "until the organization is reactivated by an administrator."
            ),
            next_eligible=None
        )

    # ── 6-month reassessment lock ─────────────────────────────────────────
    cursor.execute("""
        SELECT submitted_at FROM assessments
        WHERE organization_id = %s AND status = 'completed'
        ORDER BY submitted_at DESC LIMIT 1
    """, (organization_id,))
    last = cursor.fetchone()
    if last and last['submitted_at']:
        last_date = last['submitted_at']
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date)
        lock_days = get_int_setting(cursor, "reassessment_lock_days", 182)
        unlock_date = last_date + timedelta(days=lock_days)
        if datetime.now() < unlock_date:
            cursor.close()
            conn.close()
            return assessment_locked_response(
                next_eligible=unlock_date.strftime("%B %d, %Y")
            )

    # Validate the posted answers before opening the write transaction.
    try:
        cursor.execute("""
            SELECT id
            FROM question_bank
            WHERE is_active = 1
            ORDER BY dimension_id ASC, COALESCE(version_group_id, id) ASC, id ASC
        """)
        active_question_ids = {str(row['id']) for row in cursor.fetchall()}
        submitted_question_ids = {
            key.replace("answer_", "")
            for key in request.form
            if key.startswith("answer_")
        }
        submitted_answers = sorted(
            (
                (key.replace("answer_", ""), selected_choice_id)
                for key, selected_choice_id in request.form.items()
                if key.startswith("answer_")
            ),
            key=lambda item: int(item[0]) if item[0].isdigit() else item[0]
        )

        if active_question_ids != submitted_question_ids:
            return "Error: Please answer all active assessment questions before submitting.", 400

        selected_choice_ids = [selected_choice_id for _, selected_choice_id in submitted_answers]
        choice_placeholders = ", ".join(["%s"] * len(selected_choice_ids))
        cursor.execute(f"""
            SELECT
                qc.id AS choice_id,
                qc.question_id,
                qc.choice_score
            FROM question_choices qc
            JOIN question_bank qb
                ON qc.question_id = qb.id
            WHERE qc.id IN ({choice_placeholders})
              AND qb.is_active = 1
        """, tuple(selected_choice_ids))
        valid_choices = {
            (str(row["question_id"]), str(row["choice_id"])): row["choice_score"]
            for row in cursor.fetchall()
        }

        validated_answers = []
        for q_id, selected_choice_id in submitted_answers:
            score_value = valid_choices.get((str(q_id), str(selected_choice_id)))
            if score_value is None:
                return "Error: Invalid answer selected for an active question.", 400
            validated_answers.append((q_id, selected_choice_id, score_value))

        conn.rollback()

        for attempt in range(ASSESSMENT_SUBMIT_MAX_ATTEMPTS):
            cursor2 = conn.cursor()
            try:
                cursor2.execute("SELECT id FROM organizations WHERE id = %s FOR UPDATE", (organization_id,))
                if not cursor2.fetchone():
                    conn.rollback()
                    return "Error: No organization linked to your account.", 400

                cursor2.execute("""
                    SELECT submitted_at FROM assessments
                    WHERE organization_id = %s AND status = 'completed'
                    ORDER BY submitted_at DESC LIMIT 1
                """, (organization_id,))
                latest_completed = cursor2.fetchone()
                if latest_completed and latest_completed[0]:
                    last_date = latest_completed[0]
                    if isinstance(last_date, str):
                        last_date = datetime.fromisoformat(last_date)
                    lock_days = get_int_setting(cursor2, "reassessment_lock_days", 182)
                    unlock_date = last_date + timedelta(days=lock_days)
                    if datetime.now() < unlock_date:
                        conn.rollback()
                        return assessment_locked_response(
                            next_eligible=unlock_date.strftime("%B %d, %Y")
                        )

                cursor2.execute("""
                    SELECT COUNT(*) AS cnt FROM assessments
                    WHERE organization_id = %s AND status = 'completed'
                """, (organization_id,))
                cycle_number = cursor2.fetchone()[0] + 1
                assessment_type = 'baseline' if cycle_number == 1 else 'reassessment'

                cursor2.execute("""
                    INSERT INTO assessments (organization_id, assessment_type, status, cycle_number, started_at)
                    VALUES (%s, %s, 'submitted', %s, CURRENT_TIMESTAMP)
                """, (organization_id, assessment_type, cycle_number))
                assessment_id = cursor2.lastrowid

                cursor2.executemany("""
                    INSERT INTO assessment_answers
                        (assessment_id, question_id, selected_choice_id, score_value, saved_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, [
                    (assessment_id, q_id, selected_choice_id, score_value)
                    for q_id, selected_choice_id, score_value in validated_answers
                ])

                compute_assessment_scores(cursor2, assessment_id)
                conn.commit()
                return redirect(f'/assessment_result/{assessment_id}')
            except MySQLError as e:
                conn.rollback()
                if is_retryable_mysql_error(e) and attempt < ASSESSMENT_SUBMIT_MAX_ATTEMPTS - 1:
                    time.sleep(0.2 * (attempt + 1))
                    continue
                if is_retryable_mysql_error(e):
                    return (
                        "The assessment could not be saved because the database was busy. "
                        "Please wait a moment and submit again."
                    ), 503
                raise
            finally:
                cursor2.close()

    except Exception as e:
        conn.rollback()
        return f"Error: {e}", 500

    finally:
        cursor.close()
        conn.close()


@app.route('/assessment_result/<int:assessment_id>')
def assessment_result(assessment_id):
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id:
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if role == 'super_admin':
        cursor.execute("""
            SELECT id, overall_score, maturity_level, submitted_at, cycle_number, assessment_type
            FROM assessments
            WHERE id = %s
        """, (assessment_id,))
    else:
        cursor.execute("""
            SELECT a.id, a.overall_score, a.maturity_level, a.submitted_at, a.cycle_number, a.assessment_type
            FROM assessments a
            JOIN users u
                ON a.organization_id = u.organization_id
            WHERE a.id = %s
              AND u.id = %s
        """, (assessment_id, user_id))

    assessment = cursor.fetchone()
    if not assessment:
        cursor.close()
        conn.close()
        return "Assessment result not found.", 404

    completed_at = assessment.get("submitted_at")
    if hasattr(completed_at, "strftime"):
        assessment["completed_date"] = completed_at.strftime("%B %d, %Y")
    elif completed_at:
        assessment["completed_date"] = str(completed_at)
    else:
        assessment["completed_date"] = ""
    assessment["overall_score_value"] = float(assessment.get("overall_score") or 0)

    cursor.execute("""
        SELECT ds.score, ds.raw_score, ad.name
        FROM dimension_scores ds
        JOIN assessment_dimensions ad ON ds.dimension_id = ad.id
        WHERE ds.assessment_id = %s
    """, (assessment_id,))
    scores = cursor.fetchall()

    cursor.execute("""
        SELECT
            ad.name AS dimension,
            gf.severity,
            gf.description AS question_text,
            gf.score_value,
            COALESCE(gf.gap_definition, qcr.gap_definition, latest_qcr.gap_definition) AS gap_definition,
            COALESCE(gf.recommendation_text, qcr.recommendation_text, latest_qcr.recommendation_text) AS recommendation_text,
            qc.choice_letter,
            qc.choice_text
        FROM gap_flags gf
        JOIN assessment_dimensions ad
            ON gf.dimension_id = ad.id
        JOIN question_bank gf_question
            ON gf.question_id = gf_question.id
        LEFT JOIN question_choices qc
            ON gf.selected_choice_id = qc.id
        LEFT JOIN question_choice_recommendations qcr
            ON qcr.choice_id = gf.selected_choice_id
            AND qcr.severity = gf.severity
        LEFT JOIN question_bank latest_qb
            ON latest_qb.dimension_id = ad.id
            AND COALESCE(latest_qb.version_group_id, latest_qb.id) = COALESCE(gf_question.version_group_id, gf_question.id)
            AND latest_qb.is_active = 1
        LEFT JOIN question_choices latest_qc
            ON latest_qc.question_id = latest_qb.id
            AND latest_qc.choice_score = gf.score_value
        LEFT JOIN question_choice_recommendations latest_qcr
            ON latest_qcr.choice_id = latest_qc.id
            AND latest_qcr.severity = gf.severity
        WHERE gf.assessment_id = %s
        ORDER BY FIELD(gf.severity, 'critical', 'moderate', 'low'), ad.id, gf.id
    """, (assessment_id,))
    gaps = cursor.fetchall()

    gap_groups_by_dimension = OrderedDict()
    for gap in gaps:
        dimension = gap['dimension']
        if dimension not in gap_groups_by_dimension:
            gap_groups_by_dimension[dimension] = {
                "dimension": dimension,
                "critical_count": 0,
                "moderate_count": 0,
                "low_count": 0,
                "gap_definitions": [],
                "recommendations": [],
                "gaps": []
            }

        group = gap_groups_by_dimension[dimension]
        if gap['severity'] == 'critical':
            group["critical_count"] += 1
        elif gap['severity'] == 'moderate':
            group["moderate_count"] += 1
        elif gap['severity'] == 'low':
            group["low_count"] += 1

        gap_definition = gap.get('gap_definition')
        if gap_definition and gap_definition not in group["gap_definitions"]:
            group["gap_definitions"].append(gap_definition)

        recommendation = gap.get('recommendation_text')
        if recommendation and recommendation not in group["recommendations"]:
            group["recommendations"].append(recommendation)

        group["gaps"].append(gap)

    gap_groups = list(gap_groups_by_dimension.values())

    cursor.close()
    conn.close()
    return render_template(
        'assessment_result.html',
        assessment=assessment,
        scores=scores,
        gaps=gaps,
        gap_groups=gap_groups
    )


if __name__ == '__main__':
    app.run(debug=app.config.get("DEBUG", False), use_reloader=app.config.get("DEBUG", False))
