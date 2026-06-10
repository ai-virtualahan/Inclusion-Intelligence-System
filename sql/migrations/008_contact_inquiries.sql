CREATE TABLE IF NOT EXISTS contact_inquiries (
  id INT NOT NULL AUTO_INCREMENT,
  source ENUM('public', 'organization') NOT NULL,
  user_id INT DEFAULT NULL,
  organization_id INT DEFAULT NULL,
  contact_name VARCHAR(150) NOT NULL,
  contact_email VARCHAR(150) NOT NULL,
  inquiry_type VARCHAR(50) NOT NULL,
  subject VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  status ENUM('new', 'in_progress', 'resolved') NOT NULL DEFAULT 'new',
  email_status ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
  email_error TEXT,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_contact_inquiries_source (source),
  KEY idx_contact_inquiries_status (status),
  KEY idx_contact_inquiries_user (user_id),
  KEY idx_contact_inquiries_organization (organization_id),
  CONSTRAINT fk_contact_inquiries_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_contact_inquiries_organization
    FOREIGN KEY (organization_id) REFERENCES organizations (id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
