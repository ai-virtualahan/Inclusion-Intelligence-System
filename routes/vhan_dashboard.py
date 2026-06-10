from datetime import datetime

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
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
    load_system_settings,
    render_email_template,
)

vhan_bp = Blueprint('vhan', __name__)


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
        SELECT id, status, contact_person, company_name, work_email
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

    saved_reason = rejection_reason or 'Rejected by VHAN admin.'
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
    cursor.close()
    conn.close()

    if email_sent is False:
        flash("Access request rejected, but the rejection email failed. Check email logs.", "warning")
    elif email_sent:
        flash("Access request rejected and notification email sent.", "success")
    else:
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


@vhan_bp.route('/vhan/organizations')
def organizations():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    selected_status = request.args.get('status', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    filters = []
    params = []
    if selected_status:
        filters.append("o.status = %s")
        params.append(selected_status)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    cursor.execute(f"""
        SELECT
            o.id,
            o.company_name,
            o.industry,
            o.company_size,
            o.company_number,
            o.status,
            o.created_at,
            o.approved_at,
            reviewer.contact_person AS approved_by,
            admin.contact_person,
            admin.work_email,
            admin.position_title,
            admin.contact_number,
            latest.id AS latest_assessment_id,
            latest.status AS latest_assessment_status,
            latest.overall_score,
            latest.maturity_level
        FROM organizations o
        LEFT JOIN users admin
            ON o.id = admin.organization_id
            AND admin.role = 'org_admin'
        LEFT JOIN users reviewer
            ON o.approved_by = reviewer.id
        LEFT JOIN (
            SELECT a1.*
            FROM assessments a1
            INNER JOIN (
                SELECT organization_id, MAX(id) AS latest_id
                FROM assessments
                GROUP BY organization_id
            ) a2 ON a1.id = a2.latest_id
        ) latest ON latest.organization_id = o.id
        {where_clause}
        ORDER BY o.created_at DESC, o.id DESC
    """, params)
    organizations = cursor.fetchall()

    cursor.execute("SELECT status, COUNT(*) AS total FROM organizations GROUP BY status")
    status_rows = cursor.fetchall()
    status_counts = {row['status']: row['total'] for row in status_rows}

    cursor.close()
    conn.close()

    return render_template(
        'vhan_organizations.html',
        organizations=organizations,
        selected_status=selected_status,
        status_counts=status_counts
    )


@vhan_bp.route('/vhan/questionnaires')
def questionnaires():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    selected_dimension = request.args.get('dimension_id')
    selected_question_status = request.args.get('question_status', 'active')

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
    elif selected_question_status == 'all':
        pass

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
            ) AS question_number,
            (
                SELECT COUNT(*)
                FROM question_choices qc
                WHERE qc.question_id = qb.id
            ) AS choice_count
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
        'vhan_questionnaires.html',
        questions=questions,
        dimensions=dimensions,
        selected_dimension=selected_dimension,
        selected_question_status=selected_question_status
    )


@vhan_bp.route('/vhan/reports')
def reports():
    if session.get('role') != 'vhan_admin':
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
            admin.contact_person,
            admin.work_email,
            admin.position_title,
            admin.contact_number
        FROM organizations o
        LEFT JOIN users admin
            ON o.id = admin.organization_id
            AND admin.role = 'org_admin'
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
        'vhan_reports.html',
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


@vhan_bp.route('/vhan/email-logs', methods=['GET', 'POST'])
def email_logs():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        company_name = request.form.get('company_name')
        recipient_email = request.form.get('recipient_email')
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
    settings = load_system_settings(cursor)

    cursor.close()
    conn.close()

    return render_template(
        'vhan_email.html',
        email_logs=email_logs,
        settings=settings
    )
