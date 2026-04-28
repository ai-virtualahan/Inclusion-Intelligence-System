from flask import Flask, render_template, request, redirect
from config import SECRET_KEY
from db import get_db_connection
from assessment_scoring import compute_assessment_scores



app = Flask(__name__)
app.secret_key = SECRET_KEY


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

    cursor.execute("""
        SELECT COUNT(*) AS progress_tracked
        FROM assessments
    """)
    progress_tracked = cursor.fetchone()['progress_tracked']

    print("Users Assessed:", users_assessed)
    print("Progress Tracked:", progress_tracked)

    cursor.close()
    conn.close()

    return render_template(
        'home.html',
        users_assessed=users_assessed,
        progress_tracked=progress_tracked
    )


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/assessment')
def assessment():
    return render_template('assessment.html')


from routes.register import register_bp
app.register_blueprint(register_bp)

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        organization_id = 1  # temporary

        # 1. create assessment
        cursor.execute("""
            INSERT INTO assessments (
                organization_id,
                assessment_type,
                status,
                cycle_number,
                started_at
            )
            VALUES (%s, 'baseline', 'submitted', 1, CURRENT_TIMESTAMP)
        """, (organization_id,))

        assessment_id = cursor.lastrowid

        # 2. save answers
        for question_id, selected_choice_id in request.form.items():
            if question_id.startswith("answer_"):
                q_id = question_id.replace("answer_", "")

                cursor.execute("""
                    SELECT choice_score
                    FROM question_choices
                    WHERE id = %s
                """, (selected_choice_id,))

                score_value = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO assessment_answers (
                        assessment_id,
                        question_id,
                        selected_choice_id,
                        score_value,
                        saved_at
                    )
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (assessment_id, q_id, selected_choice_id, score_value))

        # 3. AUTO COMPUTE 🔥
        compute_assessment_scores(cursor, assessment_id)

        # 4. save tanan changes
        conn.commit()

        return redirect(f'/assessment_result/{assessment_id}')

    except Exception as e:
        conn.rollback()
        return f"Error: {e}"

    finally:
        cursor.close()
        conn.close()


@app.route('/assessment_result/<int:assessment_id>')
def assessment_result(assessment_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # assessment summary
    cursor.execute("""
        SELECT overall_score, maturity_level
        FROM assessments
        WHERE id = %s
    """, (assessment_id,))
    assessment = cursor.fetchone()

    # dimension scores
    cursor.execute("""
        SELECT ds.score, ds.raw_score, ad.name
        FROM dimension_scores ds
        JOIN assessment_dimensions ad ON ds.dimension_id = ad.id
        WHERE ds.assessment_id = %s
    """, (assessment_id,))
    scores = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'assessment_result.html',
        assessment=assessment,
        scores=scores
    )


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)