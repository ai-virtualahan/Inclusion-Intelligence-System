ALTER TABLE contact_inquiries
  ADD COLUMN category VARCHAR(50) DEFAULT NULL AFTER status,
  ADD COLUMN admin_notes TEXT DEFAULT NULL AFTER category,
  ADD COLUMN resolution_message TEXT DEFAULT NULL AFTER admin_notes,
  ADD COLUMN resolved_at TIMESTAMP NULL DEFAULT NULL AFTER resolution_message,
  ADD COLUMN resolved_by INT DEFAULT NULL AFTER resolved_at,
  ADD COLUMN last_response_at TIMESTAMP NULL DEFAULT NULL AFTER resolved_by,
  ADD KEY idx_contact_inquiries_category (category),
  ADD KEY fk_contact_inquiries_resolved_by (resolved_by),
  ADD CONSTRAINT fk_contact_inquiries_resolved_by
    FOREIGN KEY (resolved_by) REFERENCES users (id)
    ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE email_notifications
  MODIFY notification_type ENUM(
    'email_verification',
    'registration_invitation',
    'account_approval',
    'account_rejection',
    'password_reset',
    'assessment_reminder',
    'report_ready',
    'support_response'
  ) NOT NULL;
