print("TOP LOADED")

from datetime import datetime, timedelta

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

print("RECOMMENDATIONS LOADED")

DIMENSION_NAMES = ["Hiring", "Onboarding", "Accommodation", "Retention", "Culture"]
MAX_PER_QUESTION = 4
QUESTIONS_PER_DIM = 10
MAX_RAW = MAX_PER_QUESTION * QUESTIONS_PER_DIM  # 40


def maturity_level(score):
    if score <= 25:   return "Emerging"
    if score <= 50:   return "Developing"
    if score <= 75:   return "Advancing"
    if score <= 90:   return "Leading"
    return "Exemplar"


def compute_assessment_scores(cursor, assessment_id):
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
            ROUND((SUM(aa.score_value) / %s) * 100, 2)             AS score,
            CASE
                WHEN ROUND((SUM(aa.score_value) / %s) * 100, 2) <= 25 THEN 'critical'
                WHEN ROUND((SUM(aa.score_value) / %s) * 100, 2) <= 50 THEN 'moderate'
                ELSE 'none'
            END AS severity_flag
        FROM assessment_answers aa
        JOIN question_bank qb ON aa.question_id = qb.id
        WHERE aa.assessment_id = %s
        GROUP BY aa.assessment_id, qb.dimension_id
    """, (MAX_RAW, MAX_RAW, MAX_RAW, assessment_id))

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