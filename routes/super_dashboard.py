from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from db import get_db_connection

super_admin_bp = Blueprint('super_admin', __name__)

@super_admin_bp.route('/super-admin/dashboard')
def super_dashboard():
    if session.get('role') != 'super_admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Organizations
    cursor.execute("SELECT COUNT(*) AS total FROM organizations")
    total_organizations = cursor.fetchone()['total']

    # Pending Approvals (pwede ni from users or access_requests depende sa imong flow)
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
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

    cursor.close()
    conn.close()

    return render_template(
        'super_dashboard.html',
        total_organizations=total_organizations,
        pending_approvals=pending_approvals,
        assessments_completed=assessments_completed,
        active_users=active_users
    )

@super_admin_bp.route('/super-admin/organizations')
def organizations():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            o.id,
            o.company_name,
            o.industry,
            o.company_size,
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
        ORDER BY o.id DESC
    """)
    organizations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'super_organizations.html',
        organizations=organizations
    )


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


@super_admin_bp.route('/super-admin/organizations/delete/<int:org_id>', methods=['POST'])
def delete_organization(org_id):
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('super_admin.organizations'))


@super_admin_bp.route('/super-admin/assessment-questions')
def assessment_questions():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    selected_dimension = request.args.get('dimension_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name
        FROM assessment_dimensions
        ORDER BY name ASC
    """)
    dimensions = cursor.fetchall()

    if selected_dimension:
        cursor.execute("""
            SELECT
                qb.id,
                qb.question_text,
                ad.name AS dimension_name,
                qb.version,
                qb.is_active
            FROM question_bank qb
            LEFT JOIN assessment_dimensions ad
                ON qb.dimension_id = ad.id
            WHERE qb.dimension_id = %s
            ORDER BY qb.id DESC
        """, (selected_dimension,))
    else:
        cursor.execute("""
            SELECT
                qb.id,
                qb.question_text,
                ad.name AS dimension_name,
                qb.version,
                qb.is_active
            FROM question_bank qb
            LEFT JOIN assessment_dimensions ad
                ON qb.dimension_id = ad.id
            ORDER BY qb.id DESC
        """)

    questions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'assessment_questions.html',
        questions=questions,
        dimensions=dimensions,
        selected_dimension=selected_dimension
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
            id,
            choice_letter,
            choice_text,
            choice_score
        FROM question_choices
        WHERE question_id = %s
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

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE question_choices
        SET choice_text = %s,
            choice_score = %s
        WHERE id = %s
    """, (choice_text, choice_score, choice_id))

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
            id,
            choice_letter,
            choice_text,
            choice_score
        FROM question_choices
        WHERE question_id = %s
        ORDER BY choice_letter ASC
    """, (question_id,))

    choices = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"choices": choices}

@super_admin_bp.route('/super-admin/question/<int:question_id>/edit', methods=['POST'])
def edit_question(question_id):
    if session.get('role') != 'super_admin':
        return {"error": "Unauthorized"}, 403

    question_text = request.form['question_text']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE question_bank
        SET question_text = %s
        WHERE id = %s
    """, (question_text, question_id))

    conn.commit()
    cursor.close()
    conn.close()

    return {"success": True, "question_id": question_id, "question_text": question_text}