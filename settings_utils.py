from db import get_db_connection


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
