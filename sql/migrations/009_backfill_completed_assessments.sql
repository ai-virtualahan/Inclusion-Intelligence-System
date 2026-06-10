UPDATE assessments a
JOIN (
  SELECT assessment_id, COUNT(DISTINCT dimension_id) AS dimension_count
  FROM dimension_scores
  GROUP BY assessment_id
) scored
  ON scored.assessment_id = a.id
SET
  a.status = 'completed',
  a.submitted_at = COALESCE(a.submitted_at, a.started_at, CURRENT_TIMESTAMP)
WHERE a.id > 0
  AND a.status = 'submitted'
  AND a.overall_score IS NOT NULL
  AND a.maturity_level IS NOT NULL
  AND scored.dimension_count >= (
    SELECT COUNT(*)
    FROM assessment_dimensions
  );

UPDATE gap_flags gf
JOIN assessments a
  ON a.id = gf.assessment_id
JOIN assessment_answers aa
  ON aa.assessment_id = gf.assessment_id
  AND aa.question_id = gf.question_id
JOIN question_bank qb
  ON qb.id = aa.question_id
JOIN system_settings critical_setting
  ON critical_setting.setting_key = 'gap_critical_score_max'
JOIN system_settings moderate_setting
  ON moderate_setting.setting_key = 'gap_moderate_score_max'
LEFT JOIN question_choice_recommendations qcr
  ON qcr.choice_id = aa.selected_choice_id
  AND qcr.severity = CASE
    WHEN aa.score_value <= CAST(critical_setting.setting_value AS DECIMAL(5,2)) THEN 'critical'
    WHEN aa.score_value <= CAST(moderate_setting.setting_value AS DECIMAL(5,2)) THEN 'moderate'
    ELSE 'low'
  END
SET
  gf.dimension_id = qb.dimension_id,
  gf.selected_choice_id = aa.selected_choice_id,
  gf.score_value = aa.score_value,
  gf.severity = CASE
    WHEN aa.score_value <= CAST(critical_setting.setting_value AS DECIMAL(5,2)) THEN 'critical'
    WHEN aa.score_value <= CAST(moderate_setting.setting_value AS DECIMAL(5,2)) THEN 'moderate'
    ELSE 'low'
  END,
  gf.description = qb.question_text,
  gf.recommendation_text = qcr.recommendation_text
WHERE gf.id > 0
  AND a.status = 'completed';

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
SELECT
  aa.assessment_id,
  qb.dimension_id,
  aa.question_id,
  aa.selected_choice_id,
  aa.score_value,
  CASE
    WHEN aa.score_value <= CAST(critical_setting.setting_value AS DECIMAL(5,2)) THEN 'critical'
    WHEN aa.score_value <= CAST(moderate_setting.setting_value AS DECIMAL(5,2)) THEN 'moderate'
    ELSE 'low'
  END,
  qb.question_text,
  qcr.recommendation_text
FROM assessment_answers aa
JOIN assessments a
  ON a.id = aa.assessment_id
JOIN question_bank qb
  ON qb.id = aa.question_id
JOIN system_settings critical_setting
  ON critical_setting.setting_key = 'gap_critical_score_max'
JOIN system_settings moderate_setting
  ON moderate_setting.setting_key = 'gap_moderate_score_max'
JOIN system_settings low_setting
  ON low_setting.setting_key = 'gap_low_score_max'
LEFT JOIN question_choice_recommendations qcr
  ON qcr.choice_id = aa.selected_choice_id
  AND qcr.severity = CASE
    WHEN aa.score_value <= CAST(critical_setting.setting_value AS DECIMAL(5,2)) THEN 'critical'
    WHEN aa.score_value <= CAST(moderate_setting.setting_value AS DECIMAL(5,2)) THEN 'moderate'
    ELSE 'low'
  END
WHERE a.status = 'completed'
  AND aa.score_value <= CAST(low_setting.setting_value AS DECIMAL(5,2))
  AND NOT EXISTS (
    SELECT 1
    FROM gap_flags existing
    WHERE existing.assessment_id = aa.assessment_id
      AND existing.question_id = aa.question_id
  );
