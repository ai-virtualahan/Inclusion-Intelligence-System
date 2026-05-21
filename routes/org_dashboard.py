from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from db import get_db_connection
from assessment_scoring import RECOMMENDATIONS, DIMENSION_NAMES, maturity_level
from datetime import datetime, timedelta

org_dashboard_bp = Blueprint('org_dashboard', __name__)


def _get_org_id():
    """Return the organization_id for the currently logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT organization_id FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row['organization_id'] if row else None


@org_dashboard_bp.route('/api/dashboard-data')
def dashboard_data():
    """
    Returns JSON used by the front-end Inclusion Maturity Dashboard:
      - latest assessment summary
      - per-dimension scores
      - gap flags with recommendations
      - score history (all completed assessments, ordered by date)
      - reassessment eligibility (locked for 6 months after last submission)
    """
    org_id = _get_org_id()
    if not org_id:
        return jsonify({"error": "not_logged_in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ── Latest completed assessment ──────────────────────────────────────
    cursor.execute("""
        SELECT id, overall_score, maturity_level, submitted_at, cycle_number, assessment_type
        FROM assessments
        WHERE organization_id = %s
          AND status = 'completed'
        ORDER BY submitted_at DESC
        LIMIT 1
    """, (org_id,))
    latest = cursor.fetchone()

    # ── Reassessment lock logic ──────────────────────────────────────────
    can_reassess = True
    next_eligible = None
    if latest and latest['submitted_at']:
        last_date = latest['submitted_at']
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date)
        unlock_date = last_date + timedelta(days=182)  # ~6 months
        if datetime.now() < unlock_date:
            can_reassess = False
            next_eligible = unlock_date.strftime("%B %d, %Y")

    if not latest:
        cursor.close()
        conn.close()
        return jsonify({
            "has_data": False,
            "can_reassess": True,
            "next_eligible": None
        })

    assessment_id = latest['id']

    # ── Per-dimension scores ─────────────────────────────────────────────
    cursor.execute("""
        SELECT ad.name AS dimension, ds.score, ds.raw_score, ds.severity_flag
        FROM dimension_scores ds
        JOIN assessment_dimensions ad ON ds.dimension_id = ad.id
        WHERE ds.assessment_id = %s
        ORDER BY ad.id
    """, (assessment_id,))
    dim_rows = cursor.fetchall()

    dimensions = []
    for row in dim_rows:
        score = float(row['score'])
        dimensions.append({
            "name": row['dimension'],
            "score": score,
            "raw_score": row['raw_score'],
            "severity": row['severity_flag'],
            "maturity": maturity_level(score)
        })

    # ── Gap flags + recommendations ──────────────────────────────────────
    cursor.execute("""
        SELECT
            gf.severity,
            gf.description        AS question_text,
            ad.name               AS dimension,
            gf.question_id,
            qb.dimension_id
        FROM gap_flags gf
        JOIN assessment_dimensions ad ON gf.dimension_id = ad.id
        JOIN question_bank qb ON gf.question_id = qb.id
        WHERE gf.assessment_id = %s
        ORDER BY gf.severity DESC, ad.id
    """, (assessment_id,))
    gap_rows = cursor.fetchall()

    gaps = []
    for row in gap_rows:
        dim_name = row['dimension']
        # Find 0-based question index within its dimension
        q_id = row['question_id']
        cursor.execute("""
            SELECT id FROM question_bank
            WHERE dimension_id = (SELECT dimension_id FROM question_bank WHERE id = %s)
            ORDER BY id
        """, (q_id,))
        sibling_ids = [r['id'] for r in cursor.fetchall()]
        q_index = sibling_ids.index(q_id) if q_id in sibling_ids else 0
        rec = ""
        if dim_name in RECOMMENDATIONS and q_index < len(RECOMMENDATIONS[dim_name]):
            rec = RECOMMENDATIONS[dim_name][q_index]

        gaps.append({
            "dimension": dim_name,
            "severity": row['severity'],
            "question": row['question_text'],
            "recommendation": rec
        })

    # ── Score history (timeline) ─────────────────────────────────────────
    cursor.execute("""
        SELECT id, overall_score, maturity_level, submitted_at, cycle_number, assessment_type
        FROM assessments
        WHERE organization_id = %s
          AND status = 'completed'
        ORDER BY submitted_at ASC
    """, (org_id,))
    history_rows = cursor.fetchall()

    history = []
    for h in history_rows:
        # Also fetch per-dimension scores for this cycle
        cursor.execute("""
            SELECT ad.name AS dimension, ds.score
            FROM dimension_scores ds
            JOIN assessment_dimensions ad ON ds.dimension_id = ad.id
            WHERE ds.assessment_id = %s
            ORDER BY ad.id
        """, (h['id'],))
        h_dims = {r['dimension']: float(r['score']) for r in cursor.fetchall()}

        sub_at = h['submitted_at']
        if hasattr(sub_at, 'strftime'):
            sub_at = sub_at.strftime("%Y-%m-%d")

        history.append({
            "cycle": h['cycle_number'],
            "type": h['assessment_type'],
            "date": sub_at,
            "overall": float(h['overall_score']) if h['overall_score'] else 0,
            "maturity": h['maturity_level'],
            "dimensions": h_dims
        })

    cursor.close()
    conn.close()

    return jsonify({
        "has_data": True,
        "can_reassess": can_reassess,
        "next_eligible": next_eligible,
        "latest": {
            "overall": float(latest['overall_score']) if latest['overall_score'] else 0,
            "maturity": latest['maturity_level'],
            "date": latest['submitted_at'].strftime("%B %d, %Y") if hasattr(latest['submitted_at'], 'strftime') else str(latest['submitted_at']),
            "cycle": latest['cycle_number'],
            "type": latest['assessment_type']
        },
        "dimensions": dimensions,
        "gaps": gaps,
        "history": history
    })