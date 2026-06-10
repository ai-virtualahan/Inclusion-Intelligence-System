import re

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from datetime import datetime
from db import get_db_connection
from flask_mail import Message
from extensions import mail
from routes.access_request_utils import (
    approve_access_request,
    find_existing_registration,
    send_account_rejection_email,
)
from settings_utils import (
    can_role_approve_access_requests,
    get_bool_setting,
    get_int_setting,
    load_user_roles,
    load_system_settings,
    render_email_template,
    save_system_settings,
)

super_admin_bp = Blueprint('super_admin', __name__)


def make_role_key(role_label):
    role_key = re.sub(r"[^a-z0-9]+", "_", (role_label or "").strip().lower())
    return role_key.strip("_")


def recommendation_severity_from_score(score):
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "none"

    if score <= 1:
        return "critical"
    if score <= 2:
        return "moderate"
    if score <= 3:
        return "low"
    return "none"


def build_dimension_gap_analysis(dimension_scores, gap_flags):
    gaps_by_dimension = {}
    for gap in gap_flags:
        gaps_by_dimension.setdefault(gap['dimension'], []).append(gap)

    analysis = []
    for dimension in dimension_scores:
        dimension_name = dimension['dimension']
        dimension_gaps = gaps_by_dimension.get(dimension_name, [])
        critical_count = sum(1 for gap in dimension_gaps if gap['severity'] == 'critical')
        moderate_count = sum(1 for gap in dimension_gaps if gap['severity'] == 'moderate')
        low_count = sum(1 for gap in dimension_gaps if gap['severity'] == 'low')
        recommendations = []

        for gap in dimension_gaps:
            recommendation = gap.get('recommendation')
            if recommendation and recommendation not in recommendations:
                recommendations.append(recommendation)

        if critical_count:
            priority = "Critical priority"
            summary = (
                f"{dimension_name} needs immediate attention. "
                f"{critical_count} critical, {moderate_count} moderate, and {low_count} low gap(s) suggest that key practices are missing "
                "or not yet consistently implemented."
            )
        elif moderate_count:
            priority = "Moderate priority"
            summary = (
                f"{dimension_name} has practices in progress, but {moderate_count} moderate gap(s) show areas "
                "that need clearer ownership, timelines, and follow-through."
            )
        elif low_count:
            priority = "Low priority"
            summary = (
                f"{dimension_name} has {low_count} low-priority improvement area(s). "
                "Strengthen and document these practices to move toward full implementation."
            )
        else:
            priority = "On track"
            summary = (
                f"{dimension_name} is currently on track based on the latest assessment responses. "
                "Continue monitoring and sustaining documented practices."
            )

        analysis.append({
            "dimension": dimension_name,
            "score": dimension['score'],
            "raw_score": dimension['raw_score'],
            "priority": priority,
            "critical_count": critical_count,
            "moderate_count": moderate_count,
            "low_count": low_count,
            "summary": summary,
            "recommendations": recommendations[:3]
        })

    return analysis


@super_admin_bp.route('/super-admin/dashboard')
def super_dashboard():
    if session.get('role') != 'super_admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Organizations
    cursor.execute("""
        SELECT COUNT(*) AS total FROM organizations
        WHERE status = 'approved' 
    """)
    total_organizations = cursor.fetchone()['total']

    # Pending Approvals (pwede ni from users or access_requests depende sa imong flow)
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM access_requests
        WHERE status = 'pending'
    """)
    pending_approvals = cursor.fetchone()['total']

    # Assessments Completed
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM assessments
        WHERE status IN ('submitted', 'completed')
    """)
    assessments_completed = cursor.fetchone()['total']

    # Active Users
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE status = 'approved'
    """)
    active_users = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE status = 'inactive'
    """)
    inactive_users = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM organizations
        WHERE status = 'suspended'
    """)
    suspended_organizations = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM email_notifications
        WHERE send_status = 'failed'
    """)
    failed_emails = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM reports
    """)
    generated_reports = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template(
        'super_dashboard.html',
        total_organizations=total_organizations,
        pending_approvals=pending_approvals,
        assessments_completed=assessments_completed,
        active_users=active_users,
        inactive_users=inactive_users,
        suspended_organizations=suspended_organizations,
        failed_emails=failed_emails,
        generated_reports=generated_reports
    )

@super_admin_bp.route('/super-admin/organizations')
def organizations():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    selected_status = request.args.get('status')
    
    if selected_status:
        cursor.execute("""
            SELECT
                o.id,
                o.company_name,
                o.industry,
                o.company_size,
                o.company_number,
                o.status,
                o.created_at,
                o.approved_at,
                o.approved_by,
                u.id AS contact_user_id,
                u.contact_person,
                u.work_email,
                u.contact_number,
                u.position_title
            FROM organizations o
            LEFT JOIN users u
                ON o.id = u.organization_id
                AND u.role = 'org_admin'
            WHERE o.status = %s
            ORDER BY o.id DESC
        """, (selected_status,))
    else:
        cursor.execute("""
            SELECT
                o.id,
                o.company_name,
                o.industry,
                o.company_size,
                o.company_number,
                o.status,
                o.created_at,
                o.approved_at,
                o.approved_by,
                u.id AS contact_user_id,
                u.contact_person,
                u.work_email,
                u.contact_number,
                u.position_title
            FROM organizations o
            LEFT JOIN users u
                ON o.id = u.organization_id
                AND u.role = 'org_admin'
            WHERE o.status IN ('approved', 'suspended', 'rejected')
            ORDER BY o.id DESC
        """)
    organizations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('super_organizations.html',organizations=organizations,
    selected_status=selected_status)


@super_admin_bp.route('/super-admin/pending-approvals')
def pending_approvals():
    if session.get('role') != 'super_admin':
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

    return render_template(
        'super_pending_approvals.html',
        requests=requests,
        settings=settings
    )


@super_admin_bp.route('/super-admin/pending-approvals/approve/<int:req_id>', methods=['POST'])
def approve_pending_request(req_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if not can_role_approve_access_requests(cursor, session.get('role')):
            flash("Super Admin approval is disabled in System Settings.", "warning")
            return redirect(url_for('super_admin.pending_approvals'))

        _, message, category = approve_access_request(cursor, req_id, session.get('user_id'))
        conn.commit()
        flash(message, category)
    except Exception as e:
        conn.rollback()
        flash(f"Unable to approve access request: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.pending_approvals'))


@super_admin_bp.route('/super-admin/pending-approvals/reject/<int:req_id>', methods=['POST'])
def reject_pending_request(req_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        require_reason = get_bool_setting(cursor, "require_rejection_reason", True)
        rejection_reason = (request.form.get('rejection_reason') or '').strip()

        if require_reason and not rejection_reason:
            flash("Please provide a rejection reason before rejecting this request.", "warning")
            return redirect(url_for('super_admin.pending_approvals'))

        cursor.execute("""
            SELECT id, status, contact_person, company_name, work_email
            FROM access_requests
            WHERE id = %s
        """, (req_id,))
        req = cursor.fetchone()

        if not req:
            flash("Access request not found.", "danger")
        elif req['status'] != 'pending':
            flash("Only pending requests can be rejected.", "warning")
        else:
            saved_reason = rejection_reason or 'Rejected by Super Admin.'
            cursor.execute("""
                UPDATE access_requests
                SET status = 'rejected',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    rejection_reason = %s
                WHERE id = %s
            """, (
                session.get('user_id'),
                saved_reason,
                req_id
            ))
            email_sent = None
            if get_bool_setting(cursor, "auto_send_rejection_email", False):
                email_sent = send_account_rejection_email(
                    cursor,
                    req,
                    saved_reason,
                    session.get('user_id')
                )
            conn.commit()
            if email_sent is False:
                flash("Access request rejected, but the rejection email failed. Check email logs.", "warning")
            elif email_sent:
                flash("Access request rejected and notification email sent.", "success")
            else:
                flash("Access request rejected successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to reject access request: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.pending_approvals'))


@super_admin_bp.route('/super-admin/organizations/edit/<int:org_id>', methods=['POST'])
def edit_organization(org_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    company_name = request.form['company_name']
    industry = request.form['industry']
    company_size = request.form['company_size']
    company_number = request.form['company_number']
    status = request.form['status']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE organizations
            SET company_name = %s,
                industry = %s,
                company_size = %s,
                company_number = %s,
                status = %s,
                approved_at = CASE
                    WHEN %s = 'approved' THEN COALESCE(approved_at, NOW())
                    ELSE approved_at
                END,
                approved_by = CASE
                    WHEN %s = 'approved' THEN COALESCE(approved_by, %s)
                    ELSE approved_by
                END
            WHERE id = %s
        """, (
            company_name,
            industry,
            company_size,
            company_number,
            status,
            status,
            status,
            session.get('user_id'),
            org_id
        ))

        if status == 'approved':
            cursor.execute("""
                UPDATE users
                SET status = 'approved'
                WHERE organization_id = %s
                  AND role = 'org_admin'
            """, (org_id,))
        elif status in ('suspended', 'rejected'):
            cursor.execute("""
                UPDATE users
                SET status = 'inactive'
                WHERE organization_id = %s
                  AND role = 'org_admin'
            """, (org_id,))

        conn.commit()
        flash("Organization updated successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to update organization: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.organizations'))
    
@super_admin_bp.route('/super-admin/organizations/suspend/<int:org_id>', methods=['POST'])
def suspend_organization(org_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        deactivate_admins = get_bool_setting(cursor, "suspend_deactivate_admins", True)
        cursor.execute("""
            UPDATE organizations
            SET status = 'suspended'
            WHERE id = %s
        """, (org_id,))
        if deactivate_admins:
            cursor.execute("""
                UPDATE users
                SET status = 'inactive'
                WHERE organization_id = %s
                  AND role = 'org_admin'
            """, (org_id,))
        conn.commit()
        if deactivate_admins:
            flash("Organization suspended and linked organization admins were deactivated.", "success")
        else:
            flash("Organization suspended. Linked users were kept active based on System Settings.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to suspend organization: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.organizations'))


@super_admin_bp.route('/super-admin/organizations/reactivate/<int:org_id>', methods=['POST'])
def reactivate_organization(org_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE organizations
            SET status = 'approved',
                approved_at = COALESCE(approved_at, NOW()),
                approved_by = COALESCE(approved_by, %s)
            WHERE id = %s
        """, (session.get('user_id'), org_id))
        cursor.execute("""
            UPDATE users
            SET status = 'approved'
            WHERE organization_id = %s
              AND role = 'org_admin'
        """, (org_id,))
        conn.commit()
        flash("Organization reactivated and linked organization admins were approved.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to reactivate organization: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.organizations'))


@super_admin_bp.route('/super-admin/assessment-questions')
def assessment_questions():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    selected_dimension = request.args.get('dimension_id')
    selected_question_status = request.args.get('question_status', 'all')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name
        FROM assessment_dimensions
        ORDER BY name ASC
    """)
    dimensions = cursor.fetchall()

    filters = []
    params = []

    if selected_dimension:
        filters.append("qb.dimension_id = %s")
        params.append(selected_dimension)

    if selected_question_status == 'active':
        filters.append("qb.is_active = 1")
    elif selected_question_status == 'inactive':
        filters.append("qb.is_active = 0")
    elif selected_question_status == 'version_1':
        filters.append("qb.version = 1")
    elif selected_question_status == 'version_2':
        filters.append("qb.version = 2")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    cursor.execute(f"""
        SELECT
            qb.id,
            qb.question_text,
            ad.name AS dimension_name,
            qb.version,
            qb.is_active,
            COALESCE(qb.version_group_id, qb.id) AS version_group_id,
            (
                SELECT COUNT(DISTINCT COALESCE(qb2.version_group_id, qb2.id))
                FROM question_bank qb2
                WHERE qb2.dimension_id = qb.dimension_id
                  AND COALESCE(qb2.version_group_id, qb2.id) <= COALESCE(qb.version_group_id, qb.id)
            ) AS question_number
        FROM question_bank qb
        LEFT JOIN assessment_dimensions ad
            ON qb.dimension_id = ad.id
        {where_clause}
        ORDER BY ad.id ASC, question_number ASC, qb.version DESC
    """, params)

    questions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'assessment_questions.html',
        questions=questions,
        dimensions=dimensions,
        selected_dimension=selected_dimension,
        selected_question_status=selected_question_status

    )

@super_admin_bp.route('/super-admin/question/<int:question_id>/choices')
def question_choices(question_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            qb.id,
            qb.question_text,
            ad.name AS dimension_name
        FROM question_bank qb
        LEFT JOIN assessment_dimensions ad
            ON qb.dimension_id = ad.id
        WHERE qb.id = %s
    """, (question_id,))
    question = cursor.fetchone()

    cursor.execute("""
        SELECT
            qc.id,
            qc.choice_letter,
            qc.choice_text,
            qc.choice_score,
            qcr.severity AS recommendation_severity,
            qcr.gap_definition,
            qcr.recommendation_text
        FROM question_choices qc
        LEFT JOIN question_choice_recommendations qcr
            ON qcr.id = (
                SELECT qcr2.id
                FROM question_choice_recommendations qcr2
                WHERE qcr2.choice_id = qc.id
                ORDER BY qcr2.id ASC
                LIMIT 1
            )
        WHERE qc.question_id = %s
        ORDER BY choice_letter ASC
    """, (question_id,))
    choices = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'question_choices.html',
        question=question,
        choices=choices
    )   


@super_admin_bp.route('/super-admin/choice/<int:choice_id>/edit', methods=['POST'])
def edit_choice(choice_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    choice_text = request.form['choice_text']
    choice_score = request.form['choice_score']
    question_id = request.form['question_id']
    recommendation_text = (request.form.get('recommendation_text') or '').strip()
    recommendation_severity = request.form.get('recommendation_severity') or recommendation_severity_from_score(choice_score)
    if recommendation_severity == "optional":
        recommendation_severity = "low"

    if recommendation_severity not in ("none", "low", "moderate", "critical"):
        return {"error": "Recommendation severity is invalid."}, 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        UPDATE question_choices
        SET choice_text = %s,
            choice_score = %s
        WHERE id = %s
    """, (choice_text, choice_score, choice_id))

    cursor.execute("""
        SELECT gap_definition
        FROM question_choice_recommendations
        WHERE choice_id = %s
        ORDER BY id ASC
        LIMIT 1
    """, (choice_id,))
    existing_guidance = cursor.fetchone() or {}
    gap_definition = existing_guidance.get("gap_definition")

    cursor.execute("""
        DELETE FROM question_choice_recommendations
        WHERE choice_id = %s
    """, (choice_id,))

    if gap_definition or recommendation_text:
        cursor.execute("""
            INSERT INTO question_choice_recommendations (
                choice_id,
                severity,
                gap_definition,
                recommendation_text
            )
            VALUES (%s, %s, %s, %s)
        """, (
            choice_id,
            recommendation_severity,
            gap_definition,
            recommendation_text
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return {"success": True, "question_id": question_id}


@super_admin_bp.route('/super-admin/question/<int:question_id>/choices-data')
def question_choices_data(question_id):
    if session.get('role') != 'super_admin':
        return {"error": "Unauthorized"}, 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            qc.id,
            qc.choice_letter,
            qc.choice_text,
            qc.choice_score,
            qcr.severity AS recommendation_severity,
            qcr.gap_definition,
            qcr.recommendation_text
        FROM question_choices qc
        LEFT JOIN question_choice_recommendations qcr
            ON qcr.id = (
                SELECT qcr2.id
                FROM question_choice_recommendations qcr2
                WHERE qcr2.choice_id = qc.id
                ORDER BY qcr2.id ASC
                LIMIT 1
            )
        WHERE qc.question_id = %s
        ORDER BY choice_letter ASC
    """, (question_id,))

    choices = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"choices": choices}


@super_admin_bp.route('/super-admin/question/<int:question_id>/choices/edit', methods=['POST'])
def edit_question_choices(question_id):
    if session.get('role') != 'super_admin':
        return {"error": "Unauthorized"}, 403

    data = request.get_json(silent=True) or {}
    choices = data.get('choices') or []

    if not choices:
        return {"error": "No choices were submitted."}, 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id FROM question_bank WHERE id = %s", (question_id,))
        if not cursor.fetchone():
            return {"error": "Question not found."}, 404

        for choice in choices:
            choice_id = choice.get('id')
            choice_text = (choice.get('choice_text') or '').strip()
            choice_score = choice.get('choice_score')
            recommendation_text = (choice.get('recommendation_text') or '').strip()
            recommendation_severity = (
                choice.get('recommendation_severity')
                or recommendation_severity_from_score(choice_score)
            )
            if recommendation_severity == "optional":
                recommendation_severity = "low"

            if not choice_id or not choice_text:
                return {"error": "Each choice must include text."}, 400

            try:
                choice_score = float(choice_score)
            except (TypeError, ValueError):
                return {"error": "Each choice score must be a number."}, 400

            if recommendation_severity not in ("none", "low", "moderate", "critical"):
                return {"error": "Recommendation severity is invalid."}, 400

            cursor.execute("""
                UPDATE question_choices
                SET choice_text = %s,
                    choice_score = %s
                WHERE id = %s
                  AND question_id = %s
            """, (choice_text, choice_score, choice_id, question_id))

            cursor.execute("""
                SELECT gap_definition
                FROM question_choice_recommendations
                WHERE choice_id = %s
                ORDER BY id ASC
                LIMIT 1
            """, (choice_id,))
            existing_guidance = cursor.fetchone() or {}
            gap_definition = existing_guidance.get("gap_definition")

            cursor.execute("""
                DELETE FROM question_choice_recommendations
                WHERE choice_id = %s
            """, (choice_id,))

            if gap_definition or recommendation_text:
                cursor.execute("""
                    INSERT INTO question_choice_recommendations (
                        choice_id,
                        severity,
                        gap_definition,
                        recommendation_text
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    choice_id,
                    recommendation_severity,
                    gap_definition,
                    recommendation_text
                ))

        conn.commit()

        cursor.execute("""
            SELECT
                qc.id,
                qc.choice_letter,
                qc.choice_text,
                qc.choice_score,
                qcr.severity AS recommendation_severity,
                qcr.gap_definition,
                qcr.recommendation_text
            FROM question_choices qc
            LEFT JOIN question_choice_recommendations qcr
                ON qcr.id = (
                    SELECT qcr2.id
                    FROM question_choice_recommendations qcr2
                    WHERE qcr2.choice_id = qc.id
                    ORDER BY qcr2.id ASC
                    LIMIT 1
                )
            WHERE qc.question_id = %s
            ORDER BY choice_letter ASC
        """, (question_id,))

        return {
            "success": True,
            "question_id": question_id,
            "choices": cursor.fetchall()
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500
    finally:
        cursor.close()
        conn.close()


@super_admin_bp.route('/super-admin/gap-recommendations', methods=['GET', 'POST'])
def gap_recommendations():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    selected_dimension = request.values.get('dimension_id', type=int)
    selected_question_status = request.values.get('question_status', 'active')
    if selected_question_status not in {"all", "active", "inactive"}:
        selected_question_status = "active"

    status_filter = ""
    if selected_question_status == "active":
        status_filter = "AND qb.is_active = 1"
    elif selected_question_status == "inactive":
        status_filter = "AND qb.is_active = 0"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, name
            FROM assessment_dimensions
            ORDER BY id ASC
        """)
        dimensions = cursor.fetchall()

        if not selected_dimension and dimensions:
            selected_dimension = dimensions[0]['id']

        if request.method == 'POST':
            cursor.execute("""
                SELECT qc.id, qc.choice_score
                FROM question_choices qc
                JOIN question_bank qb
                    ON qc.question_id = qb.id
                WHERE qb.dimension_id = %s
                  AND qc.choice_score <= 3
                  {status_filter}
            """.format(status_filter=status_filter), (selected_dimension,))
            editable_choices = cursor.fetchall()

            for choice in editable_choices:
                choice_id = choice['id']
                gap_definition = (request.form.get(f"gap_definition_{choice_id}") or "").strip()
                recommendation_text = (request.form.get(f"recommendation_{choice_id}") or "").strip()
                severity = (
                    request.form.get(f"severity_{choice_id}")
                    or recommendation_severity_from_score(choice['choice_score'])
                )
                if severity == "optional":
                    severity = "low"

                if severity not in ("none", "low", "moderate", "critical"):
                    raise ValueError("Recommendation severity is invalid.")

                cursor.execute("""
                    DELETE FROM question_choice_recommendations
                    WHERE choice_id = %s
                """, (choice_id,))

                if gap_definition or recommendation_text:
                    cursor.execute("""
                        INSERT INTO question_choice_recommendations (
                            choice_id,
                            severity,
                            gap_definition,
                            recommendation_text
                        )
                        VALUES (%s, %s, %s, %s)
                    """, (choice_id, severity, gap_definition or None, recommendation_text))

                cursor.execute("""
                    UPDATE gap_flags
                    SET gap_definition = %s,
                        recommendation_text = %s
                    WHERE selected_choice_id = %s
                """, (
                    gap_definition or None,
                    recommendation_text or None,
                    choice_id
                ))

            conn.commit()
            flash("Gap recommendations saved successfully.", "success")
            return redirect(url_for(
                'super_admin.gap_recommendations',
                dimension_id=selected_dimension,
                question_status=selected_question_status
            ))

        cursor.execute("""
            SELECT
                ad.name AS dimension_name,
                qb.id AS question_id,
                qb.question_text,
                qb.version,
                qb.is_active,
                (
                    SELECT COUNT(DISTINCT COALESCE(qb2.version_group_id, qb2.id))
                    FROM question_bank qb2
                    WHERE qb2.dimension_id = qb.dimension_id
                      AND COALESCE(qb2.version_group_id, qb2.id)
                          <= COALESCE(qb.version_group_id, qb.id)
                ) AS question_number,
                qc.id AS choice_id,
                qc.choice_letter,
                qc.choice_text,
                qc.choice_score,
                qcr.severity,
                qcr.gap_definition,
                qcr.recommendation_text
            FROM question_choices qc
            JOIN question_bank qb
                ON qc.question_id = qb.id
            JOIN assessment_dimensions ad
                ON qb.dimension_id = ad.id
            LEFT JOIN question_choice_recommendations qcr
                ON qcr.id = (
                    SELECT qcr2.id
                    FROM question_choice_recommendations qcr2
                    WHERE qcr2.choice_id = qc.id
                    ORDER BY qcr2.id ASC
                    LIMIT 1
                )
            WHERE qb.dimension_id = %s
              AND qc.choice_score <= 3
              {status_filter}
            ORDER BY
                COALESCE(qb.version_group_id, qb.id) ASC,
                qb.id ASC,
                qc.choice_score ASC,
                qc.choice_letter ASC
        """.format(status_filter=status_filter), (selected_dimension,))
        rows = cursor.fetchall()

        question_groups_by_id = {}
        for row in rows:
            question_id = row['question_id']
            if question_id not in question_groups_by_id:
                question_groups_by_id[question_id] = {
                    "question_id": question_id,
                    "question_number": row['question_number'],
                    "question_text": row['question_text'],
                    "version": row['version'],
                    "is_active": row['is_active'],
                    "choices": [],
                }

            row["severity"] = (
                row.get("severity")
                or recommendation_severity_from_score(row.get("choice_score"))
            )
            question_groups_by_id[question_id]["choices"].append(row)

        question_groups = list(question_groups_by_id.values())
    except Exception as e:
        conn.rollback()
        flash(f"Unable to load gap recommendations: {e}", "danger")
        dimensions = []
        rows = []
        question_groups = []
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'super_gap_recommendations.html',
        dimensions=dimensions,
        selected_dimension=selected_dimension,
        selected_question_status=selected_question_status,
        question_groups=question_groups
    )


@super_admin_bp.route('/super-admin/question/<int:question_id>/activate', methods=['POST'])
def activate_question(question_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, version_group_id
            FROM question_bank
            WHERE id = %s
        """, (question_id,))
        question = cursor.fetchone()

        if not question:
            flash("Question version not found.", "danger")
            return redirect(url_for('super_admin.assessment_questions'))

        version_group_id = question['version_group_id'] or question['id']

        cursor.execute("""
            UPDATE question_bank
            SET is_active = 0
            WHERE COALESCE(version_group_id, id) = %s
        """, (version_group_id,))
        cursor.execute("""
            UPDATE question_bank
            SET is_active = 1,
                version_group_id = %s
            WHERE id = %s
        """, (version_group_id, question_id))

        conn.commit()
        flash("Question version activated. This version will be shown in assessments.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to activate question version: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(request.referrer or url_for('super_admin.assessment_questions'))


@super_admin_bp.route('/super-admin/question/<int:question_id>/deactivate', methods=['POST'])
def deactivate_question(question_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE question_bank
            SET is_active = 0,
                version_group_id = COALESCE(version_group_id, id)
            WHERE id = %s
        """, (question_id,))
        conn.commit()
        flash("Question version deactivated. It will no longer appear in assessments.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to deactivate question version: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(request.referrer or url_for('super_admin.assessment_questions'))

@super_admin_bp.route('/super-admin/question/<int:question_id>/edit', methods=['POST'])
def edit_question(question_id):
    if session.get('role') != 'super_admin':
        return {"error": "Unauthorized"}, 403

    question_text = (request.form.get('question_text') or '').strip()
    edit_mode = request.form.get('edit_mode') or 'new_version'

    if not question_text:
        return {"error": "Question text is required."}, 400
    if edit_mode not in {'same_version', 'new_version'}:
        return {"error": "Question edit mode is invalid."}, 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, dimension_id, version, is_active, version_group_id
            FROM question_bank
            WHERE id = %s
        """, (question_id,))
        current_question = cursor.fetchone()

        if not current_question:
            return {"error": "Question not found."}, 404

        if edit_mode == 'same_version':
            cursor.execute("""
                UPDATE question_bank
                SET question_text = %s
                WHERE id = %s
            """, (question_text, question_id))
            conn.commit()

            return {
                "success": True,
                "question_id": question_id,
                "old_question_id": question_id,
                "question_text": question_text,
                "version": current_question['version'] or 1,
                "is_active": current_question['is_active'],
                "created_new_version": False
            }

        version_group_id = current_question['version_group_id'] or current_question['id']

        cursor.execute("""
            SELECT COALESCE(MAX(version), 0) + 1 AS next_version
            FROM question_bank
            WHERE COALESCE(version_group_id, id) = %s
        """, (version_group_id,))
        new_version = cursor.fetchone()['next_version']

        cursor.execute("""
            UPDATE question_bank
            SET is_active = 0
            WHERE COALESCE(version_group_id, id) = %s
        """, (version_group_id,))

        cursor.execute("""
            INSERT INTO question_bank (
                dimension_id,
                question_text,
                version,
                is_active,
                version_group_id,
                created_by
            )
            VALUES (%s, %s, %s, 1, %s, %s)
        """, (
            current_question['dimension_id'],
            question_text,
            new_version,
            version_group_id,
            session.get('user_id')
        ))
        new_question_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO question_choices (
                question_id,
                choice_letter,
                choice_text,
                choice_score
            )
            SELECT
                %s,
                choice_letter,
                choice_text,
                choice_score
            FROM question_choices
            WHERE question_id = %s
            ORDER BY choice_letter ASC
        """, (new_question_id, question_id))

        cursor.execute("""
            INSERT INTO question_choice_recommendations (
                choice_id,
                severity,
                gap_definition,
                recommendation_text
            )
            SELECT
                new_choice.id,
                qcr.severity,
                qcr.gap_definition,
                qcr.recommendation_text
            FROM question_choices old_choice
            JOIN question_choices new_choice
                ON new_choice.question_id = %s
                AND new_choice.choice_letter = old_choice.choice_letter
            JOIN question_choice_recommendations qcr
                ON qcr.choice_id = old_choice.id
            WHERE old_choice.question_id = %s
        """, (new_question_id, question_id))

        conn.commit()

        return {
            "success": True,
            "question_id": new_question_id,
            "old_question_id": question_id,
            "question_text": question_text,
            "version": new_version,
            "is_active": 1,
            "created_new_version": True
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500
    finally:
        cursor.close()
        conn.close()



@super_admin_bp.route('/super-admin/user/<int:user_id>')
def view_user(user_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'view_user.html',
        user=user
    )



@super_admin_bp.route('/super-admin/users')
def users():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    selected_role = request.args.get('role')
    selected_status = request.args.get('status')

    if selected_role == 'inactive':
        selected_status = 'inactive'
        selected_role = ''

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    user_roles = load_user_roles(cursor, active_only=True)

    base_query = """
        SELECT
            u.*,
            o.company_name AS organization_name,
            COALESCE(ur.role_label, u.role) AS role_label,
            COALESCE(ur.access_role, u.role) AS access_role
        FROM users u
        LEFT JOIN organizations o
            ON u.organization_id = o.id
        LEFT JOIN user_roles ur
            ON u.role = ur.role_key
    """

    filters = []
    params = []

    if selected_role == 'internal':
        filters.append("COALESCE(ur.access_role, u.role) IN ('super_admin', 'vhan_admin')")
    elif selected_role == 'organization':
        filters.append("COALESCE(ur.access_role, u.role) = 'org_admin'")
    elif selected_role:
        filters.append("u.role = %s")
        params.append(selected_role)

    if selected_status:
        filters.append("u.status = %s")
        params.append(selected_status)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    cursor.execute(base_query + f"""
        {where_clause}
        ORDER BY u.id DESC
    """, params)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'super_users.html',
        users=users,
        selected_role=selected_role,
        selected_status=selected_status,
        user_roles=user_roles
    )


@super_admin_bp.route('/super-admin/users/add', methods=['POST'])
def add_user():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    contact_person = request.form['contact_person']
    work_email = request.form['work_email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    role = request.form['role']
    position_title = request.form.get('position_title') or None

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('super_admin.users'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        min_password_length = get_int_setting(cursor, "password_min_length", 8)
        if len(password) < min_password_length:
            flash(f"Password must be at least {min_password_length} characters long.", "danger")
            return redirect(url_for('super_admin.users'))

        active_roles = {
            row['role_key']
            for row in load_user_roles(cursor, active_only=True)
        }
        if role not in active_roles:
            flash("Please choose an active user role.", "danger")
            return redirect(url_for('super_admin.users'))

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (
                organization_id,
                contact_person,
                work_email,
                password_hash,
                role,
                status,
                position_title
            )
            VALUES (NULL, %s, %s, %s, %s, 'approved', %s)
        """, (
            contact_person,
            work_email,
            password_hash,
            role,
            position_title
        ))
        conn.commit()
        flash("User added successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to add user: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.users'))


@super_admin_bp.route('/super-admin/users/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    contact_person = request.form['contact_person']
    work_email = request.form['work_email']
    role = request.form['role']
    status = request.form['status']
    position_title = request.form.get('position_title') or None
    contact_number = request.form.get('contact_number') or None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        active_roles = {
            row['role_key']
            for row in load_user_roles(cursor, active_only=True)
        }
        if role not in active_roles:
            flash("Please choose an active user role.", "danger")
            return redirect(url_for('super_admin.users'))

        cursor.execute("""
            UPDATE users
            SET contact_person = %s,
                work_email = %s,
                role = %s,
                status = %s,
                position_title = %s,
                contact_number = %s
            WHERE id = %s
        """, (
            contact_person,
            work_email,
            role,
            status,
            position_title,
            contact_number,
            user_id
        ))
        conn.commit()
        flash("User updated successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to update user: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.users'))


@super_admin_bp.route('/super-admin/users/deactivate/<int:user_id>', methods=['POST'])
def deactivate_user(user_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    if user_id == session.get('user_id'):
        flash("You cannot deactivate your own account while logged in.", "warning")
        return redirect(url_for('super_admin.users'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE users
            SET status = 'inactive'
            WHERE id = %s
        """, (user_id,))
        conn.commit()
        flash("User deactivated successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to deactivate user: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.users'))


@super_admin_bp.route('/super-admin/users/reactivate/<int:user_id>', methods=['POST'])
def reactivate_user(user_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE users
            SET status = 'approved'
            WHERE id = %s
        """, (user_id,))
        conn.commit()
        flash("User reactivated successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to reactivate user: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.users'))


@super_admin_bp.route('/email-logs', methods=['GET', 'POST'])
def email_logs():

    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email')
        company_name = (request.form.get('company_name') or '').strip()
        settings = load_system_settings(cursor)
        template_values = {
            **settings,
            "company_name": company_name,
            "registration_url": url_for('register.register', _external=True),
        }
        subject = render_email_template(
            request.form.get('subject') or settings["email_invitation_subject"],
            **template_values
        )
        message_body = render_email_template(
            request.form.get('message_body') or settings["email_invitation_body"],
            **template_values
        )
        existing_registration = find_existing_registration(cursor, recipient_email)
        if existing_registration:
            cursor.close()
            conn.close()
            flash("Invitation not sent. This email is already registered or has an access request.", "warning")
            return redirect(url_for('super_admin.email_logs'))

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
            flash("Invitation email sent successfully.", "success")

        except Exception as e:
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
            flash("Invitation email failed to send. The failure was saved in email logs.", "danger")

        cursor.close()
        conn.close()
        return redirect(url_for('super_admin.email_logs'))

    query = """
        SELECT 
            en.*,
            u.contact_person AS triggered_by_name
        FROM email_notifications en
        LEFT JOIN users u
        ON en.triggered_by = u.id
        ORDER BY en.created_at DESC
    """

    cursor.execute(query)
    email_logs = cursor.fetchall()
    settings = load_system_settings(cursor)

    cursor.close()
    conn.close()

    return render_template(
        'email_logs.html',
        email_logs=email_logs,
        settings=settings
    )


@super_admin_bp.route('/super-admin/reports')
def reports():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    selected_org_id = request.args.get('organization_id', type=int)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    report_settings = load_system_settings(cursor)
    hide_suspended_reports = report_settings.get("suspend_hide_reports") == "on"
    report_org_statuses = ("approved",) if hide_suspended_reports else ("approved", "suspended")
    report_org_status_placeholders = ", ".join(["%s"] * len(report_org_statuses))

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM reports
    """)
    total_reports = cursor.fetchone()['total']

    cursor.execute(f"""
        SELECT COUNT(DISTINCT a.organization_id) AS total
        FROM assessments a
        JOIN organizations o
            ON o.id = a.organization_id
        WHERE o.status IN ({report_org_status_placeholders})
          AND a.status IN ('submitted', 'completed')
          AND a.overall_score IS NOT NULL
          AND a.maturity_level IS NOT NULL
          AND (
              SELECT COUNT(DISTINCT ds.dimension_id)
              FROM dimension_scores ds
              WHERE ds.assessment_id = a.id
          ) >= (
              SELECT COUNT(*)
              FROM assessment_dimensions
          )
    """, report_org_statuses)
    organizations_with_results = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM organizations
        WHERE status = 'approved'
    """)
    approved_organizations = cursor.fetchone()['total']

    cursor.execute(f"""
        SELECT
            o.id,
            o.company_name,
            o.industry,
            o.company_size,
            o.company_number,
            o.status,
            o.created_at,
            u.contact_person,
            u.work_email,
            u.position_title,
            u.contact_number
        FROM organizations o
        LEFT JOIN users u
            ON o.id = u.organization_id
            AND u.role = 'org_admin'
        WHERE o.status IN ({report_org_status_placeholders})
        ORDER BY o.company_name ASC
    """, report_org_statuses)
    organizations = cursor.fetchall()

    if not selected_org_id and organizations:
        selected_org_id = organizations[0]['id']

    selected_org = None
    latest_assessment = None
    dimension_scores = []
    gap_flags = []
    dimension_gap_analysis = []

    if selected_org_id:
        selected_org = next((org for org in organizations if org['id'] == selected_org_id), None)
        if not selected_org:
            selected_org_id = organizations[0]['id'] if organizations else None
            selected_org = organizations[0] if organizations else None

    if selected_org_id and selected_org:
        cursor.execute("""
            SELECT id, assessment_type, status, cycle_number, overall_score,
                   maturity_level, started_at, submitted_at
            FROM assessments
            WHERE organization_id = %s
              AND status IN ('submitted', 'completed')
              AND overall_score IS NOT NULL
              AND maturity_level IS NOT NULL
              AND (
                  SELECT COUNT(DISTINCT ds.dimension_id)
                  FROM dimension_scores ds
                  WHERE ds.assessment_id = assessments.id
              ) >= (
                  SELECT COUNT(*)
                  FROM assessment_dimensions
              )
            ORDER BY COALESCE(submitted_at, started_at) DESC, id DESC
            LIMIT 1
        """, (selected_org_id,))
        latest_assessment = cursor.fetchone()

        if latest_assessment:
            cursor.execute("""
                SELECT ad.name AS dimension, ds.score, ds.raw_score, ds.severity_flag
                FROM dimension_scores ds
                JOIN assessment_dimensions ad ON ds.dimension_id = ad.id
                WHERE ds.assessment_id = %s
                ORDER BY ad.id
            """, (latest_assessment['id'],))
            dimension_scores = cursor.fetchall()

            cursor.execute("""
                SELECT
                    ad.name AS dimension,
                    gf.severity,
                    gf.description,
                    gf.question_id,
                    gf.score_value,
                    gf.recommendation_text,
                    qc.choice_letter,
                    qc.choice_text
                FROM gap_flags gf
                JOIN assessment_dimensions ad ON gf.dimension_id = ad.id
                LEFT JOIN question_choices qc ON gf.selected_choice_id = qc.id
                WHERE gf.assessment_id = %s
                ORDER BY FIELD(gf.severity, 'critical', 'moderate', 'low'), ad.id
            """, (latest_assessment['id'],))
            gap_flags = cursor.fetchall()

            for gap in gap_flags:
                gap['recommendation'] = gap.get('recommendation_text') or ""

            dimension_gap_analysis = build_dimension_gap_analysis(dimension_scores, gap_flags)

    cursor.close()
    conn.close()

    return render_template(
        'super_reports.html',
        total_reports=total_reports,
        organizations_with_results=organizations_with_results,
        approved_organizations=approved_organizations,
        organizations=organizations,
        selected_org_id=selected_org_id,
        selected_org=selected_org,
        latest_assessment=latest_assessment,
        dimension_scores=dimension_scores,
        gap_flags=gap_flags,
        dimension_gap_analysis=dimension_gap_analysis,
        settings=report_settings,
        generated_at=datetime.now()
    )


@super_admin_bp.route('/super-admin/settings', methods=['GET', 'POST'])
def system_settings():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            settings = save_system_settings(cursor, request.form, session.get('user_id'))
            conn.commit()
            flash("System settings saved successfully.", "success")
        else:
            settings = load_system_settings(cursor)
    except Exception as e:
        conn.rollback()
        settings = load_system_settings(cursor)
        flash(f"Unable to save system settings: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        user_roles = load_user_roles(cursor, active_only=False)
    finally:
        cursor.close()
        conn.close()

    return render_template('super_settings.html', settings=settings, user_roles=user_roles)


@super_admin_bp.route('/super-admin/settings/roles/add', methods=['POST'])
def add_user_role():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    role_label = (request.form.get('role_label') or '').strip()
    access_role = request.form.get('access_role') or 'org_admin'
    role_key = make_role_key(role_label)

    if not role_label or not role_key:
        flash("Role name is required.", "danger")
        return redirect(url_for('super_admin.system_settings'))

    if access_role not in {"org_admin", "vhan_admin", "super_admin"}:
        flash("Role access type is invalid.", "danger")
        return redirect(url_for('super_admin.system_settings'))

    if role_key in {"org_admin", "vhan_admin", "super_admin"}:
        flash("Built-in role names already exist.", "warning")
        return redirect(url_for('super_admin.system_settings'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        load_user_roles(cursor, active_only=False)
        cursor.execute("""
            INSERT INTO user_roles (
                role_key,
                role_label,
                access_role,
                is_builtin,
                is_active
            )
            VALUES (%s, %s, %s, 0, 1)
            ON DUPLICATE KEY UPDATE
                role_label = VALUES(role_label),
                access_role = VALUES(access_role),
                is_active = 1
        """, (role_key, role_label, access_role))
        conn.commit()
        flash("User role saved successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to save user role: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.system_settings'))


@super_admin_bp.route('/super-admin/settings/roles/<role_key>/deactivate', methods=['POST'])
def deactivate_user_role(role_key):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        load_user_roles(cursor, active_only=False)
        cursor.execute("""
            SELECT is_builtin
            FROM user_roles
            WHERE role_key = %s
        """, (role_key,))
        role = cursor.fetchone()

        if not role:
            flash("User role not found.", "danger")
        elif role['is_builtin']:
            flash("Built-in roles cannot be deactivated.", "warning")
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role = %s", (role_key,))
            assigned_count = cursor.fetchone()['total']
            if assigned_count:
                flash("This role is assigned to users. Reassign them before deactivating it.", "warning")
            else:
                cursor.execute("""
                    UPDATE user_roles
                    SET is_active = 0
                    WHERE role_key = %s
                """, (role_key,))
                conn.commit()
                flash("User role deactivated.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Unable to deactivate user role: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.system_settings'))




