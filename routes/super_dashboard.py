from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from db import get_db_connection
from flask_mail import Message
from extensions import mail

super_admin_bp = Blueprint('super_admin', __name__)

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
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE organizations
            SET status = 'suspended'
            WHERE id = %s
        """, (org_id,))
        cursor.execute("""
            UPDATE users
            SET status = 'inactive'
            WHERE organization_id = %s
              AND role = 'org_admin'
        """, (org_id,))
        conn.commit()
        flash("Organization suspended and linked organization admins were deactivated.", "success")
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
    cursor = conn.cursor()

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

            if not choice_id or not choice_text:
                return {"error": "Each choice must include text."}, 400

            try:
                choice_score = float(choice_score)
            except (TypeError, ValueError):
                return {"error": "Each choice score must be a number."}, 400

            cursor.execute("""
                UPDATE question_choices
                SET choice_text = %s,
                    choice_score = %s
                WHERE id = %s
                  AND question_id = %s
            """, (choice_text, choice_score, choice_id, question_id))

        conn.commit()

        cursor.execute("""
            SELECT id, choice_letter, choice_text, choice_score
            FROM question_choices
            WHERE question_id = %s
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
    cursor = conn.cursor()

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

    if not question_text:
        return {"error": "Question text is required."}, 400

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

        new_version = (current_question['version'] or 1) + 1
        version_group_id = current_question['version_group_id'] or current_question['id']

        cursor.execute("""
            UPDATE question_bank
            SET is_active = 0
            WHERE id = %s
        """, (question_id,))

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

        conn.commit()

        return {
            "success": True,
            "question_id": new_question_id,
            "old_question_id": question_id,
            "question_text": question_text,
            "version": new_version,
            "is_active": 1
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

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if selected_role == 'internal':
        cursor.execute("""
            SELECT *
            FROM users
            WHERE role IN ('super_admin', 'vhan_admin')
            ORDER BY id DESC
        """)
    elif selected_role == 'organization':
        cursor.execute("""
            SELECT *
            FROM users
            WHERE role = 'org_admin'
            ORDER BY id DESC
        """)
    elif selected_role == 'inactive':
        cursor.execute("""
            SELECT *
            FROM users
            WHERE status = 'inactive'
            ORDER BY id DESC
        """)
    elif selected_role:
        cursor.execute("""
            SELECT *
            FROM users
            WHERE role = %s
            ORDER BY id DESC
        """, (selected_role,))
    else:
        cursor.execute("""
            SELECT *
            FROM users
            ORDER BY id DESC
        """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'super_users.html',
        users=users,
        selected_role=selected_role
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

    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
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
    cursor = conn.cursor()

    try:
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

    cursor.close()
    conn.close()

    return render_template(
        'email_logs.html',
        email_logs=email_logs
    )


@super_admin_bp.route('/super-admin/reports')
def reports():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    selected_org_id = request.args.get('organization_id', type=int)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM reports
    """)
    total_reports = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM assessments
        WHERE status IN ('submitted', 'completed')
    """)
    completed_assessments = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM organizations
        WHERE status = 'approved'
    """)
    approved_organizations = cursor.fetchone()['total']

    cursor.execute("""
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
        WHERE o.status = 'approved'
        ORDER BY o.company_name ASC
    """)
    organizations = cursor.fetchall()

    if not selected_org_id and organizations:
        selected_org_id = organizations[0]['id']

    selected_org = None
    latest_assessment = None
    dimension_scores = []
    gap_flags = []

    if selected_org_id:
        selected_org = next((org for org in organizations if org['id'] == selected_org_id), None)

        cursor.execute("""
            SELECT id, assessment_type, status, cycle_number, overall_score,
                   maturity_level, started_at, submitted_at
            FROM assessments
            WHERE organization_id = %s
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
                SELECT ad.name AS dimension, gf.severity, gf.description
                FROM gap_flags gf
                JOIN assessment_dimensions ad ON gf.dimension_id = ad.id
                WHERE gf.assessment_id = %s
                ORDER BY FIELD(gf.severity, 'critical', 'moderate'), ad.id
            """, (latest_assessment['id'],))
            gap_flags = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'super_reports.html',
        total_reports=total_reports,
        completed_assessments=completed_assessments,
        approved_organizations=approved_organizations,
        organizations=organizations,
        selected_org_id=selected_org_id,
        selected_org=selected_org,
        latest_assessment=latest_assessment,
        dimension_scores=dimension_scores,
        gap_flags=gap_flags
    )


@super_admin_bp.route('/super-admin/settings')
def system_settings():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    return render_template('super_settings.html')




