def compute_assessment_scores(cursor, assessment_id):
    # 1. Delete old computed results
    cursor.execute("""
        DELETE FROM dimension_scores
        WHERE assessment_id = %s
    """, (assessment_id,))

    cursor.execute("""
        DELETE FROM gap_flags
        WHERE assessment_id = %s
    """, (assessment_id,))

    # 2. Compute dimension scores
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
            SUM(aa.score_value) AS raw_score,
            ROUND((SUM(aa.score_value) / 40) * 100, 2) AS score,
            CASE
                WHEN ROUND((SUM(aa.score_value) / 40) * 100, 2) <= 50 THEN 'critical'
                WHEN ROUND((SUM(aa.score_value) / 40) * 100, 2) <= 75 THEN 'moderate'
                ELSE 'none'
            END AS severity_flag
        FROM assessment_answers aa
        JOIN question_bank qb ON aa.question_id = qb.id
        WHERE aa.assessment_id = %s
        GROUP BY aa.assessment_id, qb.dimension_id
    """, (assessment_id,))

    # 3. Update overall score + maturity level
    cursor.execute("""
        UPDATE assessments a
        SET 
            overall_score = (
                SELECT ROUND(AVG(ds.score), 2)
                FROM dimension_scores ds
                WHERE ds.assessment_id = a.id
            ),
            maturity_level = CASE
                WHEN (
                    SELECT ROUND(AVG(ds.score), 2)
                    FROM dimension_scores ds
                    WHERE ds.assessment_id = a.id
                ) BETWEEN 0 AND 25 THEN 'Emerging'
                WHEN (
                    SELECT ROUND(AVG(ds.score), 2)
                    FROM dimension_scores ds
                    WHERE ds.assessment_id = a.id
                ) BETWEEN 26 AND 50 THEN 'Developing'
                WHEN (
                    SELECT ROUND(AVG(ds.score), 2)
                    FROM dimension_scores ds
                    WHERE ds.assessment_id = a.id
                ) BETWEEN 51 AND 75 THEN 'Advancing'
                WHEN (
                    SELECT ROUND(AVG(ds.score), 2)
                    FROM dimension_scores ds
                    WHERE ds.assessment_id = a.id
                ) BETWEEN 76 AND 90 THEN 'Leading'
                WHEN (
                    SELECT ROUND(AVG(ds.score), 2)
                    FROM dimension_scores ds
                    WHERE ds.assessment_id = a.id
                ) BETWEEN 91 AND 100 THEN 'Exemplar'
            END
        WHERE a.id = %s
    """, (assessment_id,))

    # 4. Create gap flags
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

    # 5. Mark assessment completed
    cursor.execute("""
        UPDATE assessments
        SET status = 'completed',
            submitted_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (assessment_id,))