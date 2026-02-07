from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from response import success_response, error_response
from users.models_users import RegistrationUser
from users.schemas_users import (
    validate_registration_payload,
    validate_login_payload,
    validate_update_payload,
)
from users.services_users import register_user, login_user, get_user_profile, update_user, delete_user

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/health")
def health():
    return success_response(message="Users service healthy", data={"service": "users"})

@users_bp.route("/register", methods=["POST"])
def register():
    payload, errors = validate_registration_payload(request.get_json(silent=True))
    if errors:
        return error_response(status_code=400, message="Validation Error", user_message=" ".join(errors))

    if RegistrationUser.query.filter_by(email=payload["email"]).first():
        return error_response(status_code=409, message="Conflict", user_message="Email already registered.")

    result = register_user(payload)
    user = result["user"]
    role = result["role"]
    token = result["token"]

    return success_response(
        status_code=201,
        message=f"Account created for {user.email} with role {role}.",
        data={"id": user.id, "email": user.email, "role": role, "token": token},
    )


@users_bp.route("/login", methods=["POST"])
def login():
    payload, errors = validate_login_payload(request.get_json(silent=True))
    if errors:
        return error_response(status_code=400, message="Validation Error", user_message=" ".join(errors))

    user, result = login_user(payload)
    if not user:
        return error_response(status_code=401, message="Unauthorized", user_message="Invalid email or password.")

    return success_response(
        message="Login successful",
        data={"email": user.email, "role": result["role"], "token": result["token"]},
    )


@users_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user, role = get_user_profile(get_jwt_identity())
    if not user:
        return error_response(status_code=401, message="Unauthorized", user_message="Invalid token.")

    return success_response(
        message="Profile fetched",
        data={"email": user.email, "role": role, "created_at": user.created_at.isoformat()},
    )


@users_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_me():
    payload, errors = validate_update_payload(request.get_json(silent=True))
    if errors:
        return error_response(status_code=400, message="Validation Error", user_message=" ".join(errors))

    user, role = update_user(get_jwt_identity(), payload)
    if not user:
        return error_response(status_code=401, message="Unauthorized", user_message="Invalid token.")

    return success_response(
        message="Account updated",
        data={"email": user.email, "role": role},
    )


@users_bp.route("/me", methods=["DELETE"])
@jwt_required()
def delete_me():
    user = delete_user(get_jwt_identity())
    if not user:
        return error_response(status_code=401, message="Unauthorized", user_message="Invalid token.")

    return success_response(
        message="Logged out and account deleted permanently.",
        data={"email": user.email},
    )


@users_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return success_response(message="Logout successful")
