from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from collections import OrderedDict
from db import get_db_connection
from assessment_scoring import compute_assessment_scores
from datetime import datetime, timedelta

from routes.login import login_bp
from routes.super_dashboard import super_admin_bp
from routes.vhan_dashboard import vhan_bp
from routes.register import register_bp
from routes.org_dashboard import org_dashboard_bp

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

    cursor.close()
    conn.close()
    return render_template('home.html', users_assessed=users_assessed, progress_tracked=progress_tracked)


@app.route('/assessment')
def assessment():
    user_id = session.get('user_id')
    profile = {k: '' for k in ['full_name','position','work_email','contact_number',
                                'company_name','company_size','industry','company_number']}
    active_exams = OrderedDict()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if user_id:
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

    return render_template('assessment.html', profile=profile, active_exams=active_exams)


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
        unlock_date = last_date + timedelta(days=182)
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

    cursor.close()
    conn.close()
    return render_template('assessment_result.html', assessment=assessment, scores=scores)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
