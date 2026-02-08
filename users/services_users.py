from flask_jwt_extended import create_access_token
from uuid import uuid4
from extensions import db
from users.models_users import RegistrationUser, UserProfile
from users.schemas_users import (
    validate_registration_payload,
    validate_login_payload,
    validate_update_payload,
    serialize_registration_response,
    serialize_login_response,
    serialize_me_response,
    serialize_update_response,
    serialize_delete_response,
    serialize_user_profile,
    serialize_users_health,
    serialize_logout_response,
)



def _error(status_code, message, user_message):
    return {
        "status_code": status_code,
        "message": message,
        "user_message": user_message,
    }


def _role_for_user(user):
    if user.is_master:
        return "master"
    if user.is_admin:
        return "admin"
    return "user"


def _get_user_by_identity(identity):
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None
    return RegistrationUser.query.get(user_id)


def register_user(payload):
    user = RegistrationUser(
        email=payload["email"],
        is_admin=payload["is_admin"],
        is_master=payload["is_master"],
        created_at=payload["created_at"],
    )
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={"nonce": str(uuid4())})
    role = _role_for_user(user)

    return {
        "user": user,
        "role": role,
        "token": token,
    }


def login_user(payload):
    user = RegistrationUser.query.filter_by(email=payload["email"]).first()
    if not user or not user.check_password(payload["password"]):
        return None, None

    token = create_access_token(identity=str(user.id), additional_claims={"nonce": str(uuid4())})
    role = _role_for_user(user)
    return user, {"role": role, "token": token}


def get_user_profile(identity):
    user = _get_user_by_identity(identity)
    if not user:
        return None, None
    role = _role_for_user(user)
    return user, role


def get_user_profile_details(identity):
    user = _get_user_by_identity(identity)
    if not user:
        return None, None
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    return user, profile


def update_user(identity, payload):
    user = _get_user_by_identity(identity)
    if not user:
        return None, None

    if payload.get("email"):
        user.email = payload["email"]
    if payload.get("password"):
        user.set_password(payload["password"])

    db.session.commit()
    role = _role_for_user(user)
    return user, role


def delete_user(identity):
    user = _get_user_by_identity(identity)
    if not user:
        return None
    db.session.delete(user)
    db.session.commit()
    return user


# High-level handlers for routes

def users_health_service():
    return {
        "status_code": 200,
        "message": "Users service healthy",
        "data": serialize_users_health(),
    }, None


def register_user_service(payload):
    payload, errors = validate_registration_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    if RegistrationUser.query.filter_by(email=payload["email"]).first():
        return None, _error(409, "Conflict", "Email already registered.")

    result = register_user(payload)
    user = result["user"]
    role = result["role"]
    token = result["token"]

    return {
        "status_code": 201,
        "message": f"Account created for {user.email} with role {role}.",
        "data": serialize_registration_response(user, role, token),
    }, None


def login_user_service(payload):
    payload, errors = validate_login_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    user, result = login_user(payload)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid email or password.")

    return {
        "status_code": 200,
        "message": "Login successful",
        "data": serialize_login_response(user, result["role"], result["token"]),
    }, None


def me_service(identity):
    user, role = get_user_profile(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "Profile fetched",
        "data": serialize_me_response(user, role),
    }, None


def profile_service(identity):
    user, profile = get_user_profile_details(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "User profile fetched",
        "data": serialize_user_profile(user, profile),
    }, None


def update_me_service(identity, payload):
    payload, errors = validate_update_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    user, role = update_user(identity, payload)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "Account updated",
        "data": serialize_update_response(user, role),
    }, None


def delete_me_service(identity):
    user = delete_user(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "Logged out and account deleted permanently.",
        "data": serialize_delete_response(user),
    }, None


def logout_service():
    return {
        "status_code": 200,
        "message": "Logout successful",
        "data": serialize_logout_response(),
    }, None
