from datetime import datetime
from users.models_users import UserProfile


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


def serialize_users_health():
    return {"service": "users"}


def serialize_registration_response(user, role, token):
    return {
        "id": user.id,
        "email": user.email,
        "role": role,
        "token": token,
    }


def serialize_login_response(user, role, token):
    return {
        "email": user.email,
        "role": role,
        "token": token,
    }


def serialize_me_response(user, role):
    return {
        "email": user.email,
        "role": role,
        "created_at": user.created_at.isoformat(),
    }


def serialize_update_response(user, role):
    return {
        "email": user.email,
        "role": role,
    }


def serialize_delete_response(user):
    return {
        "email": user.email,
    }


def serialize_logout_response():
    return None


def serialize_user_profile(user, profile):
    if profile:
        return {
            "username": profile.username,
            "primary_email": user.email,
            "mobile_number": profile.mobile_number,
            "profile_pic_url": profile.profile_pic_url,
            "profile_pic_public_id": profile.profile_pic_public_id,
            "profile_pic_folder": profile.profile_pic_folder,
            "bio": profile.bio,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "city": profile.city,
            "state": profile.state,
            "country": profile.country,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }

    return {
        "username": None,
        "primary_email": user.email,
        "mobile_number": None,
        "profile_pic_url": None,
        "profile_pic_public_id": None,
        "profile_pic_folder": UserProfile.PROFILE_PIC_FOLDER,
        "bio": None,
        "date_of_birth": None,
        "city": None,
        "state": None,
        "country": None,
        "created_at": None,
        "updated_at": None,
    }
