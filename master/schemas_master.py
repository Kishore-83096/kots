from users.models_users import RegistrationUser


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


def validate_pagination_params(args):
    errors = []
    try:
        page = int(args.get("page", 1))
        per_page = int(args.get("per_page", 10))
    except ValueError:
        return None, ["Invalid pagination values."]

    if page < 1 or per_page < 1 or per_page > 100:
        errors.append("Invalid pagination range.")

    if errors:
        return None, errors

    return {"page": page, "per_page": per_page}, None


def serialize_master_health():
    return {"service": "master"}


def serialize_master_control():
    return {"scope": "master"}


def serialize_admin_created(user: RegistrationUser):
    role = "master" if user.is_master else "admin"
    return {
        "id": user.id,
        "email": user.email,
        "role": role,
    }


def serialize_admin_detail(user: RegistrationUser):
    role = "master" if user.is_master else "admin"
    return {
        "id": user.id,
        "email": user.email,
        "role": role,
        "created_at": user.created_at.isoformat(),
    }


def serialize_admins_list(data):
    return data
