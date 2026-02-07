from datetime import datetime


def validate_registration_payload(payload):
    errors = []
    email = (payload or {}).get("email")
    password = (payload or {}).get("password")
    is_admin = bool((payload or {}).get("is_admin", False))
    is_master = bool((payload or {}).get("is_master", False))

    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Password is required.")

    if errors:
        return None, errors

    return {
        "email": email.strip().lower(),
        "password": password,
        "is_admin": is_admin,
        "is_master": is_master,
        "created_at": datetime.utcnow(),
    }, None


def validate_login_payload(payload):
    errors = []
    email = (payload or {}).get("email")
    password = (payload or {}).get("password")

    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Password is required.")

    if errors:
        return None, errors

    return {
        "email": email.strip().lower(),
        "password": password,
    }, None


def validate_update_payload(payload):
    errors = []
    email = (payload or {}).get("email")
    password = (payload or {}).get("password")

    if not email and not password:
        errors.append("Email or password is required.")

    if errors:
        return None, errors

    return {
        "email": email.strip().lower() if email else None,
        "password": password if password else None,
    }, None
