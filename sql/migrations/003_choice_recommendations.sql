CREATE TABLE IF NOT EXISTS `question_choice_recommendations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `choice_id` int NOT NULL,
  `severity` enum('none','optional','moderate','critical') NOT NULL DEFAULT 'none',
  `recommendation_text` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_choice_recommendation_choice` (`choice_id`),
  KEY `idx_choice_recommendation_severity` (`severity`),
  CONSTRAINT `fk_choice_recommendation_choice`
    FOREIGN KEY (`choice_id`) REFERENCES `question_choices` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `question_choice_recommendations` (
  `choice_id`,
  `severity`,
  `recommendation_text`
)
SELECT
  qc.id,
  CASE
    WHEN qc.choice_score <= 1 THEN 'critical'
    WHEN qc.choice_score <= 2 THEN 'moderate'
    WHEN qc.choice_score <= 3 THEN 'optional'
    ELSE 'none'
  END AS severity,
  CONCAT(
    CASE
      WHEN qc.choice_score <= 1 THEN 'Critical action: '
      WHEN qc.choice_score <= 2 THEN 'Moderate action: '
      ELSE 'Optional improvement: '
    END,
    qb.question_text
  ) AS recommendation_text
FROM question_choices qc
JOIN question_bank qb
  ON qc.question_id = qb.id
WHERE qc.choice_score <= 3
  AND NOT EXISTS (
    SELECT 1
    FROM question_choice_recommendations existing
    WHERE existing.choice_id = qc.id
  );

ALTER TABLE `gap_flags`
  ADD COLUMN `selected_choice_id` int DEFAULT NULL AFTER `question_id`,
  ADD COLUMN `score_value` decimal(5,2) DEFAULT NULL AFTER `selected_choice_id`,
  ADD COLUMN `recommendation_text` text AFTER `description`,
  ADD KEY `idx_gap_selected_choice` (`selected_choice_id`),
  ADD CONSTRAINT `fk_gap_selected_choice`
    FOREIGN KEY (`selected_choice_id`) REFERENCES `question_choices` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE;

UPDATE gap_flags gf
JOIN assessment_answers aa
  ON aa.assessment_id = gf.assessment_id
  AND aa.question_id = gf.question_id
SET
  gf.selected_choice_id = aa.selected_choice_id,
  gf.score_value = aa.score_value
WHERE gf.selected_choice_id IS NULL;

UPDATE gap_flags gf
JOIN question_choice_recommendations qcr
  ON qcr.choice_id = gf.selected_choice_id
  AND qcr.severity = gf.severity
SET gf.recommendation_text = qcr.recommendation_text
WHERE gf.recommendation_text IS NULL;
