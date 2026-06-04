from db import get_db_connection


BUILTIN_USER_ROLES = [
    {
        "role_key": "super_admin",
        "role_label": "Super Admin",
        "access_role": "super_admin",
        "is_builtin": 1,
        "is_active": 1,
    },
    {
        "role_key": "vhan_admin",
        "role_label": "VHAN Admin",
        "access_role": "vhan_admin",
        "is_builtin": 1,
        "is_active": 1,
    },
    {
        "role_key": "org_admin",
        "role_label": "Org Admin",
        "access_role": "org_admin",
        "is_builtin": 1,
        "is_active": 1,
    },
]

DEFAULT_SYSTEM_SETTINGS = {
    "system_name": "Inclusion Intelligence System",
    "support_email": "iis@virtualahan.com",
    "primary_contact": "Virtualahan Admin Team",
    "reassessment_lock_days": "182",
    "score_emerging_max": "25",
    "score_developing_max": "50",
    "score_advancing_max": "75",
    "score_leading_max": "90",
    "gap_critical_score_max": "1",
    "gap_moderate_score_max": "2",
    "weight_hiring": "20",
    "weight_onboarding": "20",
    "weight_accommodation": "20",
    "weight_retention": "20",
    "weight_culture": "20",
    "approval_reviewer": "both",
    "require_rejection_reason": "on",
    "auto_send_approval_email": "on",
    "auto_send_rejection_email": "",
    "report_footer_text": "Prepared by Inclusion Intelligence System",
    "report_show_gap_analysis": "on",
    "report_show_recommendations": "on",
    "report_include_generated_date": "on",
    "password_min_length": "8",
    "session_timeout_minutes": "60",
    "suspend_deactivate_admins": "on",
    "suspend_lock_assessments": "on",
    "suspend_hide_reports": "on",
}

CHECKBOX_SETTINGS = {
    "require_rejection_reason",
    "auto_send_approval_email",
    "auto_send_rejection_email",
    "report_show_gap_analysis",
    "report_show_recommendations",
    "report_include_generated_date",
    "suspend_deactivate_admins",
    "suspend_lock_assessments",
    "suspend_hide_reports",
}


def ensure_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key VARCHAR(100) NOT NULL,
            setting_value TEXT,
            updated_by INT DEFAULT NULL,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (setting_key)
        )
    """)


def ensure_user_roles_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            id INT NOT NULL AUTO_INCREMENT,
            role_key VARCHAR(50) NOT NULL,
            role_label VARCHAR(100) NOT NULL,
            access_role VARCHAR(50) NOT NULL DEFAULT 'org_admin',
            is_builtin TINYINT(1) NOT NULL DEFAULT 0,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_user_roles_key (role_key)
        )
    """)

    for role in BUILTIN_USER_ROLES:
        cursor.execute("""
            INSERT INTO user_roles (
                role_key,
                role_label,
                access_role,
                is_builtin,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                role_label = VALUES(role_label),
                access_role = VALUES(access_role),
                is_builtin = VALUES(is_builtin),
                is_active = 1
        """, (
            role["role_key"],
            role["role_label"],
            role["access_role"],
            role["is_builtin"],
            role["is_active"],
        ))


def load_user_roles(cursor, active_only=True):
    ensure_user_roles_table(cursor)
    where_clause = "WHERE is_active = 1" if active_only else ""
    cursor.execute(f"""
        SELECT role_key, role_label, access_role, is_builtin, is_active
        FROM user_roles
        {where_clause}
        ORDER BY is_builtin DESC, role_label ASC
    """)
    return cursor.fetchall()


def get_role_access(cursor, role_key):
    ensure_user_roles_table(cursor)
    cursor.execute("""
        SELECT access_role
        FROM user_roles
        WHERE role_key = %s
          AND is_active = 1
        LIMIT 1
    """, (role_key,))
    row = cursor.fetchone()
    if not row:
        return role_key if role_key in {"super_admin", "vhan_admin", "org_admin"} else None
    return row["access_role"] if isinstance(row, dict) else row[0]


def number_from_settings(settings, key, minimum=None, maximum=None):
    try:
        value = float(settings[key])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{key.replace('_', ' ').title()} must be a number.")

    if minimum is not None and value < minimum:
        raise ValueError(f"{key.replace('_', ' ').title()} must be at least {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{key.replace('_', ' ').title()} must not exceed {maximum}.")
    return value


def validate_system_settings(settings):
    emerging = number_from_settings(settings, "score_emerging_max", 0, 100)
    developing = number_from_settings(settings, "score_developing_max", 0, 100)
    advancing = number_from_settings(settings, "score_advancing_max", 0, 100)
    leading = number_from_settings(settings, "score_leading_max", 0, 100)

    if not (emerging < developing < advancing < leading < 100):
        raise ValueError("Scoring thresholds must increase and Leading Max must be below 100.")

    critical_gap = number_from_settings(settings, "gap_critical_score_max", 1, 4)
    moderate_gap = number_from_settings(settings, "gap_moderate_score_max", 1, 4)
    if critical_gap > moderate_gap:
        raise ValueError("Critical gap score must be lower than or equal to moderate gap score.")

    weights = [
        number_from_settings(settings, "weight_hiring", 0, 100),
        number_from_settings(settings, "weight_onboarding", 0, 100),
        number_from_settings(settings, "weight_accommodation", 0, 100),
        number_from_settings(settings, "weight_retention", 0, 100),
        number_from_settings(settings, "weight_culture", 0, 100),
    ]
    if round(sum(weights), 2) != 100:
        raise ValueError("Dimension weights must total 100.")

    number_from_settings(settings, "reassessment_lock_days", 1, 3650)
    number_from_settings(settings, "password_min_length", 6, 32)
    number_from_settings(settings, "session_timeout_minutes", 5, 480)


def load_system_settings(cursor):
    ensure_settings_table(cursor)
    settings = DEFAULT_SYSTEM_SETTINGS.copy()

    cursor.execute("""
        SELECT setting_key, setting_value
        FROM system_settings
    """)
    for row in cursor.fetchall():
        key = row["setting_key"] if isinstance(row, dict) else row[0]
        value = row["setting_value"] if isinstance(row, dict) else row[1]
        if key in settings and value is not None:
            settings[key] = value

    return settings


def save_system_settings(cursor, form_data, updated_by):
    ensure_settings_table(cursor)
    settings = {}

    for key, default_value in DEFAULT_SYSTEM_SETTINGS.items():
        if key in CHECKBOX_SETTINGS:
            settings[key] = "on" if form_data.get(key) else ""
        else:
            settings[key] = (form_data.get(key) or default_value).strip()

    validate_system_settings(settings)

    for key, value in settings.items():
        cursor.execute("""
            INSERT INTO system_settings (setting_key, setting_value, updated_by)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                setting_value = VALUES(setting_value),
                updated_by = VALUES(updated_by),
                updated_at = CURRENT_TIMESTAMP
        """, (key, value, updated_by))

    return settings


def setting_is_enabled(settings, key):
    return settings.get(key) == "on"


def get_bool_setting(cursor, key, default=False):
    settings = load_system_settings(cursor)
    if key not in settings:
        return default
    return setting_is_enabled(settings, key)


def get_int_setting(cursor, key, default):
    settings = load_system_settings(cursor)
    try:
        return int(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def can_role_approve_access_requests(cursor, role):
    settings = load_system_settings(cursor)
    reviewer = settings.get("approval_reviewer", "both")
    return reviewer == "both" or reviewer == role


def get_int_setting_from_db(key, default):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        return get_int_setting(cursor, key, default)
    finally:
        cursor.close()
        conn.close()
