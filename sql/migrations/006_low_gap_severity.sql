INSERT INTO system_settings (setting_key, setting_value, updated_by)
VALUES ('gap_low_score_max', '3', NULL)
ON DUPLICATE KEY UPDATE setting_value = setting_value;

ALTER TABLE gap_flags
  MODIFY severity ENUM('low', 'moderate', 'critical') NOT NULL;

ALTER TABLE question_choice_recommendations
  MODIFY severity ENUM('none', 'optional', 'low', 'moderate', 'critical')
  NOT NULL DEFAULT 'none';

UPDATE question_choice_recommendations
SET severity = 'low'
WHERE severity = 'optional';

ALTER TABLE question_choice_recommendations
  MODIFY severity ENUM('none', 'low', 'moderate', 'critical')
  NOT NULL DEFAULT 'none';
