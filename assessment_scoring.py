from settings_utils import load_system_settings

# ─────────────────────────────────────────────
#  GAP RECOMMENDATIONS  (per question index)
# ─────────────────────────────────────────────
RECOMMENDATIONS = {
    "Hiring": [
        "Update all job postings to explicitly welcome candidates with disabilities and list available accommodations.",
        "Audit job descriptions to remove non-essential criteria that may screen out qualified PWD candidates.",
        "Commission a WCAG 2.1 accessibility audit of the online application platform.",
        "Test all recruiting communications with common assistive technologies (screen readers, magnifiers).",
        "Set formal, measurable PWD hiring targets and report progress to leadership quarterly.",
        "Set formal, measurable PWD hiring targets and report progress to leadership quarterly.",
        "Conduct a workforce gap analysis to identify roles underrepresented by persons with disabilities.",
        "Establish at least two active partnerships with disability-focused organizations or job boards.",
        "Review all pre-employment assessments for accessibility compliance before use.",
        "Embed explicit disability inclusion language in all EEO statements and diversity policies.",
    ],
    "Onboarding": [
        "Formally add disability inclusion and accessibility training to the onboarding curriculum.",
        "Brief all new employees on the accommodation request process on Day 1.",
        "Convert all onboarding materials to accessible formats (WCAG-compliant, screen-reader ready).",
        "Add a dedicated section to onboarding covering the organization's accessibility policy.",
        "Connect new hires with disabilities to ERGs or designated accessibility support contacts.",
        "Add a workstation and tools accessibility check to the pre-boarding workflow.",
        "Publish career development paths in accessible formats and include them in onboarding.",
        "Train new employees on available assistive technology and internal accessibility tools.",
        "Provide managers with written guidance on supporting employees with disclosed disabilities.",
        "Establish a periodic review process to evaluate and improve onboarding for PWD employees.",
    ],
    "Accommodation": [
        "Develop and publish a written accommodation policy accessible to all employees.",
        "Document the accommodation request process and communicate it clearly to the workforce.",
        "Implement a tracking system for accommodation requests with defined SLA timelines.",
        "Provide funding and support for assistive technology required to perform job functions.",
        "Broaden accommodation options to cover physical, digital, communication, and scheduling needs.",
        "Train all managers on handling accommodation requests lawfully and without bias.",
        "Create a documented exception process for cases where accommodations cannot be immediately fulfilled.",
        "Schedule periodic accommodation reviews, especially when roles or needs change.",
        "Implement a feedback mechanism for employees to rate their accommodation experience.",
        "Allocate a dedicated budget line item for accommodations and assistive technology.",
    ],
    "Retention": [
        "Audit role distribution data to ensure PWD employees are represented at all levels.",
        "Establish or revitalize a disability-focused ERG with executive sponsorship.",
        "Incorporate accessibility responsibilities into performance criteria where role-relevant.",
        "Ensure mentoring programs are accessible and actively recruit PWD participants.",
        "Track PWD retention rates and build an action plan to close any gap vs. overall retention.",
        "Audit promotion and advancement processes to remove systemic barriers for PWD employees.",
        "Actively include employees with disabilities in product development and accessibility audits.",
        "Add disability inclusion and accessibility questions to employee engagement surveys.",
        "Establish a clear, retaliation-free channel for employees to raise accessibility concerns.",
        "Form a disability inclusion working group or community of practice to drive improvement.",
    ],
    "Culture": [
        "Have a senior executive make a public, visible statement of commitment to disability inclusion.",
        "Assign clear accountability for the disability inclusion program to an executive sponsor.",
        "Embed disability inclusion language into the organization's core values and code of conduct.",
        "Set measurable, strategy-level goals for accessibility and disability inclusion.",
        "Roll out role-relevant disability awareness and accessibility training for all employees.",
        "Formally integrate disability inclusion into the organization's DEI strategy.",
        "Establish metrics to measure accessibility program effectiveness and report results.",
        "Build a dedicated budget and financial roadmap to advance accessibility maturity.",
        "Tie digital accessibility performance to employee and officer performance objectives.",
        "Create a regular feedback loop with employees on disability inclusion culture and act on findings.",
    ],
}

DIMENSION_NAMES = ["Hiring", "Onboarding", "Accommodation", "Retention", "Culture"]
MAX_PER_QUESTION = 4
QUESTIONS_PER_DIM = 10
MAX_RAW = MAX_PER_QUESTION * QUESTIONS_PER_DIM  # 40

DIMENSION_WEIGHT_KEYS = {
    "Hiring": "weight_hiring",
    "Onboarding": "weight_onboarding",
    "Accommodation": "weight_accommodation",
    "Retention": "weight_retention",
    "Culture": "weight_culture",
}


def setting_number(settings, key, default):
    try:
        return float(settings.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def scoring_thresholds(settings):
    emerging = setting_number(settings, "score_emerging_max", 25)
    developing = max(emerging, setting_number(settings, "score_developing_max", 50))
    advancing = max(developing, setting_number(settings, "score_advancing_max", 75))
    leading = max(advancing, setting_number(settings, "score_leading_max", 90))
    return emerging, developing, advancing, leading


def maturity_level(score, settings=None):
    settings = settings or {}
    emerging, developing, advancing, leading = scoring_thresholds(settings)

    if score <= emerging:   return "Emerging"
    if score <= developing:   return "Developing"
    if score <= advancing:   return "Advancing"
    if score <= leading:   return "Leading"
    return "Exemplar"


def row_value(row, key, index):
    return row[key] if isinstance(row, dict) else row[index]


def recommendation_for_question(cursor, dimension_name, question_id):
    """Return the recommendation mapped to a question's position in its dimension."""
    cursor.execute("""
        SELECT dimension_id, COALESCE(version_group_id, id) AS version_group_id
        FROM question_bank
        WHERE id = %s
    """, (question_id,))
    question = cursor.fetchone()
    if not question:
        return ""

    dimension_id = question['dimension_id'] if isinstance(question, dict) else question[0]
    version_group_id = question['version_group_id'] if isinstance(question, dict) else question[1]

    cursor.execute("""
        SELECT DISTINCT COALESCE(version_group_id, id) AS version_group_id
        FROM question_bank
        WHERE dimension_id = %s
        ORDER BY version_group_id
    """, (dimension_id,))

    group_ids = [row['version_group_id'] if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
    question_index = group_ids.index(version_group_id) if version_group_id in group_ids else 0

    recommendations = RECOMMENDATIONS.get(dimension_name, [])
    return recommendations[question_index] if question_index < len(recommendations) else ""


def choice_recommendation_for_answer(cursor, choice_id, severity=None):
    """Return the recommendation attached to the selected answer choice."""
    params = [choice_id]
    severity_filter = ""
    if severity:
        severity_filter = "AND severity = %s"
        params.append(severity)

    cursor.execute(f"""
        SELECT recommendation_text
        FROM question_choice_recommendations
        WHERE choice_id = %s
          {severity_filter}
          AND recommendation_text IS NOT NULL
          AND TRIM(recommendation_text) <> ''
        ORDER BY id ASC
        LIMIT 1
    """, tuple(params))
    row = cursor.fetchone()
    if not row:
        return ""
    return row_value(row, "recommendation_text", 0) or ""


def compute_assessment_scores_legacy(cursor, assessment_id):
    """
    Full scoring pipeline:
      1. Delete old computed results
      2. Compute per-dimension scores (each dimension = 20% of overall)
      3. Update overall score + maturity level on assessments table
      4. Insert gap_flags for low-scoring answers (score 1 or 2)
      5. Mark assessment completed
    """

    # 1. Clear previous results
    cursor.execute("DELETE FROM dimension_scores WHERE assessment_id = %s", (assessment_id,))
    cursor.execute("DELETE FROM gap_flags WHERE assessment_id = %s", (assessment_id,))

    # 2. Compute per-dimension scores
    #    Each dimension contributes equally (20%) to the overall score.
    #    dim_score = (SUM of raw scores in that dimension / MAX_RAW) * 100
    cursor.execute("""
        INSERT INTO dimension_scores (
            assessment_id,
            dimension_id,
            raw_score,
            score,
            severity_flag
        )
        SELECT
            aa.assessment_id,
            qb.dimension_id,
            SUM(aa.score_value)                                     AS raw_score,
            ROUND((SUM(aa.score_value) / (COUNT(*) * %s)) * 100, 2) AS score,
            CASE
                WHEN ROUND((SUM(aa.score_value) / (COUNT(*) * %s)) * 100, 2) <= 25 THEN 'critical'
                WHEN ROUND((SUM(aa.score_value) / (COUNT(*) * %s)) * 100, 2) <= 50 THEN 'moderate'
                ELSE 'none'
            END AS severity_flag
        FROM assessment_answers aa
        JOIN question_bank qb ON aa.question_id = qb.id
        WHERE aa.assessment_id = %s
        GROUP BY aa.assessment_id, qb.dimension_id
    """, (MAX_PER_QUESTION, MAX_PER_QUESTION, MAX_PER_QUESTION, assessment_id))

    # 3. Overall score = average of all dimension scores (equal 20% weight each)
    #    Maturity level assigned by threshold
    cursor.execute("""
        UPDATE assessments a
        SET
            overall_score = (
                SELECT ROUND(AVG(ds.score), 2)
                FROM dimension_scores ds
                WHERE ds.assessment_id = a.id
            ),
            maturity_level = CASE
                WHEN (SELECT ROUND(AVG(ds.score),2) FROM dimension_scores ds WHERE ds.assessment_id = a.id) <= 25  THEN 'Emerging'
                WHEN (SELECT ROUND(AVG(ds.score),2) FROM dimension_scores ds WHERE ds.assessment_id = a.id) <= 50  THEN 'Developing'
                WHEN (SELECT ROUND(AVG(ds.score),2) FROM dimension_scores ds WHERE ds.assessment_id = a.id) <= 75  THEN 'Advancing'
                WHEN (SELECT ROUND(AVG(ds.score),2) FROM dimension_scores ds WHERE ds.assessment_id = a.id) <= 90  THEN 'Leading'
                ELSE 'Exemplar'
            END
        WHERE a.id = %s
    """, (assessment_id,))

    # 4. Gap flags — any answer scored 1 (Not in Place) or 2 (Planned)
    cursor.execute("""
        INSERT INTO gap_flags (
            assessment_id,
            dimension_id,
            question_id,
            severity,
            description
        )
        SELECT
            aa.assessment_id,
            qb.dimension_id,
            aa.question_id,
            CASE
                WHEN aa.score_value = 1 THEN 'critical'
                WHEN aa.score_value = 2 THEN 'moderate'
            END AS severity,
            qb.question_text AS description
        FROM assessment_answers aa
        JOIN question_bank qb ON aa.question_id = qb.id
        WHERE aa.assessment_id = %s
          AND aa.score_value IN (1, 2)
    """, (assessment_id,))

    # 5. Mark completed
    cursor.execute("""
        UPDATE assessments
        SET status = 'completed',
            submitted_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (assessment_id,))


def compute_assessment_scores(cursor, assessment_id):
    """
    Compute assessment results using configurable scoring settings.
    """
    settings = load_system_settings(cursor)
    emerging_max, developing_max, _, _ = scoring_thresholds(settings)
    critical_score_max = setting_number(settings, "gap_critical_score_max", 1)
    moderate_score_max = max(
        critical_score_max,
        setting_number(settings, "gap_moderate_score_max", 2)
    )
    low_score_max = max(
        moderate_score_max,
        setting_number(settings, "gap_low_score_max", 3)
    )

    cursor.execute("DELETE FROM dimension_scores WHERE assessment_id = %s", (assessment_id,))
    cursor.execute("DELETE FROM gap_flags WHERE assessment_id = %s", (assessment_id,))

    cursor.execute("""
        SELECT
            qb.dimension_id,
            ad.name AS dimension_name,
            SUM(aa.score_value) AS raw_score,
            COUNT(*) AS answer_count
        FROM assessment_answers aa
        JOIN question_bank qb
            ON aa.question_id = qb.id
        JOIN assessment_dimensions ad
            ON qb.dimension_id = ad.id
        WHERE aa.assessment_id = %s
        GROUP BY qb.dimension_id, ad.name
        ORDER BY ad.id
    """, (assessment_id,))
    dimension_rows = cursor.fetchall()

    weighted_total = 0
    weight_total = 0

    for row in dimension_rows:
        dimension_id = row_value(row, "dimension_id", 0)
        dimension_name = row_value(row, "dimension_name", 1)
        raw_score = float(row_value(row, "raw_score", 2) or 0)
        answer_count = float(row_value(row, "answer_count", 3) or 0)
        max_score = answer_count * MAX_PER_QUESTION
        score = round((raw_score / max_score) * 100, 2) if max_score else 0

        if score <= emerging_max:
            severity_flag = "critical"
        elif score <= developing_max:
            severity_flag = "moderate"
        else:
            severity_flag = "none"

        cursor.execute("""
            INSERT INTO dimension_scores (
                assessment_id,
                dimension_id,
                raw_score,
                score,
                severity_flag
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (assessment_id, dimension_id, raw_score, score, severity_flag))

        weight_key = DIMENSION_WEIGHT_KEYS.get(dimension_name)
        dimension_weight = setting_number(settings, weight_key, 20) if weight_key else 20
        if dimension_weight > 0:
            weighted_total += score * dimension_weight
            weight_total += dimension_weight

    overall_score = round(weighted_total / weight_total, 2) if weight_total else 0
    overall_maturity = maturity_level(overall_score, settings)

    cursor.execute("""
        UPDATE assessments
        SET overall_score = %s,
            maturity_level = %s
        WHERE id = %s
    """, (overall_score, overall_maturity, assessment_id))

    cursor.execute("""
        SELECT
            aa.question_id,
            aa.selected_choice_id,
            aa.score_value,
            qb.dimension_id,
            qb.question_text,
            ad.name AS dimension_name
        FROM assessment_answers aa
        JOIN question_bank qb
            ON aa.question_id = qb.id
        JOIN assessment_dimensions ad
            ON qb.dimension_id = ad.id
        WHERE aa.assessment_id = %s
    """, (assessment_id,))
    answer_rows = cursor.fetchall()

    for row in answer_rows:
        question_id = row_value(row, "question_id", 0)
        selected_choice_id = row_value(row, "selected_choice_id", 1)
        score_value = float(row_value(row, "score_value", 2) or 0)
        dimension_id = row_value(row, "dimension_id", 3)
        question_text = row_value(row, "question_text", 4)
        dimension_name = row_value(row, "dimension_name", 5)

        if score_value <= critical_score_max:
            severity = "critical"
        elif score_value <= moderate_score_max:
            severity = "moderate"
        elif score_value <= low_score_max:
            severity = "low"
        else:
            continue

        recommendation = choice_recommendation_for_answer(cursor, selected_choice_id, severity)
        if not recommendation:
            recommendation = recommendation_for_question(cursor, dimension_name, question_id)

        cursor.execute("""
            INSERT INTO gap_flags (
                assessment_id,
                dimension_id,
                question_id,
                selected_choice_id,
                score_value,
                severity,
                description,
                recommendation_text
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            assessment_id,
            dimension_id,
            question_id,
            selected_choice_id,
            score_value,
            severity,
            question_text,
            recommendation
        ))

    cursor.execute("""
        UPDATE assessments
        SET status = 'completed',
            submitted_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (assessment_id,))
