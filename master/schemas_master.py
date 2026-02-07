def validate_admin_create_payload(payload):
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
