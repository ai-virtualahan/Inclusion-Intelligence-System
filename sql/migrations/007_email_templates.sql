INSERT INTO system_settings (setting_key, setting_value, updated_by)
VALUES
('email_invitation_subject', 'Registration Invitation - Inclusion Intelligence', NULL),
('email_invitation_body', 'Hello,

You are invited to register in the {system_name}.

Please complete your organization registration using this link:
{registration_url}

Thank you,
{primary_contact}', NULL),
('email_verification_subject', 'Verify Your Email - {system_name}', NULL),
('email_verification_body', 'Hello {contact_person},

Please verify your email address to continue your {system_name} registration.

Verification link:
{verification_url}

This link will expire in 24 hours. Once verified, your access request will be sent to the administrator for approval.

Thank you,
{primary_contact}', NULL),
('email_approval_subject', 'Account Approved - {system_name}', NULL),
('email_approval_body', 'Hello {contact_person},

Your organization, {company_name}, has been approved for the {system_name}.

You may now log in using your registered work email:
{work_email}

Login page:
{login_url}

Thank you,
{primary_contact}', NULL),
('email_rejection_subject', 'Access Request Update - {system_name}', NULL),
('email_rejection_body', 'Hello {contact_person},

Your access request for {company_name} was not approved.

Reason:
{rejection_reason}

For questions, please contact {support_email}.

Thank you,
{primary_contact}', NULL),
('email_password_reset_subject', 'Reset Your Password - {system_name}', NULL),
('email_password_reset_body', 'Hello {contact_person},

We received a request to reset the password associated with your {system_name} account.

Please use the link below to create a new password:
{reset_url}

For security purposes, this link will expire in 15 minutes.

If you did not request a password reset, you may safely ignore this email.

Thank you,
{primary_contact}', NULL)
ON DUPLICATE KEY UPDATE setting_value = setting_value;
