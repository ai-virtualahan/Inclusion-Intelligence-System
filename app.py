import hmac
import secrets

from flask import Flask, abort, flash, render_template, request, redirect, session, url_for, jsonify
from collections import OrderedDict
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

# Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(super_admin_bp)
app.register_blueprint(vhan_bp)
app.register_blueprint(register_bp)
app.register_blueprint(org_dashboard_bp)
app.register_blueprint(contact_bp)


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": csrf_token}


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

    if not expected_token or not submitted_token or not hmac.compare_digest(expected_token, submitted_token):
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


@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(DISTINCT organization_id) AS users_assessed
        FROM assessments
        WHERE status IN ('submitted', 'completed')
    """)
    users_assessed = cursor.fetchone()['users_assessed']

    cursor.execute("SELECT COUNT(*) AS progress_tracked FROM assessments")
    progress_tracked = cursor.fetchone()['progress_tracked']

    settings = load_system_settings(cursor)

    cursor.close()
    conn.close()
    return render_template(
        'home.html',
        users_assessed=users_assessed,
        progress_tracked=progress_tracked,
        support_email=settings["support_email"],
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
        assessment_lock=assessment_lock
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
        return render_template(
            'assessment_locked.html',
            lock_title="Assessment Access Locked",
            lock_message=(
                "Your organization is currently suspended. Assessment submissions are locked "
                "until the organization is reactivated by an administrator."
            ),
            next_eligible=None
        ), 403

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
            return render_template('assessment_locked.html',
                                   next_eligible=unlock_date.strftime("%B %d, %Y"))

    # ── Determine cycle number ────────────────────────────────────────────
    cursor.execute("""
        SELECT COUNT(*) AS cnt FROM assessments
        WHERE organization_id = %s AND status = 'completed'
    """, (organization_id,))
    cnt = cursor.fetchone()['cnt']
    cycle_number = cnt + 1
    assessment_type = 'baseline' if cycle_number == 1 else 'reassessment'

    cursor2 = conn.cursor()  # non-dict cursor for inserts

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

        if active_question_ids != submitted_question_ids:
            return "Error: Please answer all active assessment questions before submitting.", 400

        cursor2.execute("""
            INSERT INTO assessments (organization_id, assessment_type, status, cycle_number, started_at)
            VALUES (%s, %s, 'submitted', %s, CURRENT_TIMESTAMP)
        """, (organization_id, assessment_type, cycle_number))
        assessment_id = cursor2.lastrowid

        # Save answers
        for key, selected_choice_id in request.form.items():
            if key.startswith("answer_"):
                q_id = key.replace("answer_", "")
                cursor2.execute("""
                    SELECT qc.choice_score
                    FROM question_choices qc
                    JOIN question_bank qb
                        ON qc.question_id = qb.id
                    WHERE qc.id = %s
                      AND qc.question_id = %s
                      AND qb.is_active = 1
                """, (selected_choice_id, q_id))
                row = cursor2.fetchone()
                if not row:
                    conn.rollback()
                    return "Error: Invalid answer selected for an active question.", 400

                score_value = row[0]
                cursor2.execute("""
                    INSERT INTO assessment_answers
                        (assessment_id, question_id, selected_choice_id, score_value, saved_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (assessment_id, q_id, selected_choice_id, score_value))

        # Auto-compute scores
        compute_assessment_scores(cursor2, assessment_id)
        conn.commit()
        return redirect(f'/assessment_result/{assessment_id}')

    except Exception as e:
        conn.rollback()
        return f"Error: {e}", 500

    finally:
        cursor.close()
        cursor2.close()
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
            SELECT overall_score, maturity_level
            FROM assessments
            WHERE id = %s
        """, (assessment_id,))
    else:
        cursor.execute("""
            SELECT a.overall_score, a.maturity_level
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
            gf.gap_definition,
            gf.recommendation_text,
            qc.choice_letter,
            qc.choice_text
        FROM gap_flags gf
        JOIN assessment_dimensions ad
            ON gf.dimension_id = ad.id
        LEFT JOIN question_choices qc
            ON gf.selected_choice_id = qc.id
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
