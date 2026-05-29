ALTER TABLE access_requests
  MODIFY status ENUM('email_unverified','pending','approved','rejected') NOT NULL DEFAULT 'email_unverified';

ALTER TABLE access_requests
  ADD COLUMN email_verified_at TIMESTAMP NULL DEFAULT NULL AFTER password_hash,
  ADD COLUMN verification_token_hash VARCHAR(64) DEFAULT NULL AFTER email_verified_at,
  ADD COLUMN verification_token_expiry TIMESTAMP NULL DEFAULT NULL AFTER verification_token_hash;

UPDATE access_requests
SET email_verified_at = COALESCE(email_verified_at, created_at)
WHERE status IN ('pending', 'approved');

ALTER TABLE email_notifications
  MODIFY notification_type ENUM(
    'email_verification',
    'registration_invitation',
    'account_approval',
    'account_rejection',
    'password_reset',
    'assessment_reminder',
    'report_ready'
  ) NOT NULL;
