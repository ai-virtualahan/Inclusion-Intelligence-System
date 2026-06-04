CREATE TABLE IF NOT EXISTS `user_roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_key` varchar(50) NOT NULL,
  `role_label` varchar(100) NOT NULL,
  `access_role` varchar(50) NOT NULL DEFAULT 'org_admin',
  `is_builtin` tinyint(1) NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_roles_key` (`role_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `user_roles` (
  `role_key`,
  `role_label`,
  `access_role`,
  `is_builtin`,
  `is_active`
)
VALUES
  ('super_admin', 'Super Admin', 'super_admin', 1, 1),
  ('vhan_admin', 'VHAN Admin', 'vhan_admin', 1, 1),
  ('org_admin', 'Org Admin', 'org_admin', 1, 1)
ON DUPLICATE KEY UPDATE
  `role_label` = VALUES(`role_label`),
  `access_role` = VALUES(`access_role`),
  `is_builtin` = VALUES(`is_builtin`),
  `is_active` = 1;

ALTER TABLE `users`
  MODIFY COLUMN `role` varchar(50) NOT NULL DEFAULT 'org_admin';
