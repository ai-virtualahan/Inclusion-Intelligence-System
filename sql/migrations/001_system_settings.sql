CREATE TABLE IF NOT EXISTS system_settings (
  setting_key VARCHAR(100) NOT NULL,
  setting_value TEXT,
  updated_by INT DEFAULT NULL,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (setting_key),
  KEY fk_system_settings_updated_by (updated_by)
);

INSERT INTO system_settings (setting_key, setting_value, updated_by)
VALUES
('approval_reviewer','both',NULL),
('auto_send_approval_email','on',NULL),
('auto_send_rejection_email','',NULL),
('gap_critical_score_max','1',NULL),
('gap_moderate_score_max','2',NULL),
('password_min_length','8',NULL),
('primary_contact','Virtualahan Admin Team',NULL),
('reassessment_lock_days','182',NULL),
('report_footer_text','Prepared by Inclusion Intelligence System',NULL),
('report_include_generated_date','on',NULL),
('report_show_gap_analysis','on',NULL),
('report_show_recommendations','on',NULL),
('require_rejection_reason','on',NULL),
('score_advancing_max','75',NULL),
('score_developing_max','50',NULL),
('score_emerging_max','25',NULL),
('score_leading_max','90',NULL),
('session_timeout_minutes','60',NULL),
('support_email','iis@virtualahan.com',NULL),
('suspend_deactivate_admins','on',NULL),
('suspend_hide_reports','on',NULL),
('suspend_lock_assessments','on',NULL),
('system_name','Inclusion Intelligence System',NULL),
('weight_accommodation','20',NULL),
('weight_culture','20',NULL),
('weight_hiring','20',NULL),
('weight_onboarding','20',NULL),
('weight_retention','20',NULL)
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value);
