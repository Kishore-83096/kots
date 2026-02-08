from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from common.response import success_response, error_response
from users.services_users import (
    users_health_service,
    register_user_service,
    login_user_service,
    me_service,
    profile_service,
    update_me_service,
    delete_me_service,
    logout_service,
)

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/health")
def health():
    result, err = users_health_service()
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])

@users_bp.route("/register", methods=["POST"])
def register():
    result, err = register_user_service(request.get_json(silent=True))
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])


@users_bp.route("/login", methods=["POST"])
def login():
    result, err = login_user_service(request.get_json(silent=True))
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])


@users_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    result, err = me_service(get_jwt_identity())
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])


@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    result, err = profile_service(get_jwt_identity())
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])


@users_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_me():
    result, err = update_me_service(get_jwt_identity(), request.get_json(silent=True))
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])


@users_bp.route("/me", methods=["DELETE"])
@jwt_required()
def delete_me():
    result, err = delete_me_service(get_jwt_identity())
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])


@users_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    result, err = logout_service()
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])
