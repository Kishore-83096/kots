from flask import Blueprint, request
from response import success_response, error_response
from permissions import role_required
from master.schemas_master import validate_admin_create_payload
from master.services_master import create_admin_user

master_bp = Blueprint("master", __name__, url_prefix="/master")

@master_bp.route("/health")
def health():
    return success_response(message="Master service healthy", data={"service": "master"})


@master_bp.route("/control")
@role_required("master")
def control_panel():
    return success_response(message="Master control panel", data={"scope": "master"})


@master_bp.route("/create-admin", methods=["POST"])
@role_required("master")
def create_admin():
    payload, errors = validate_admin_create_payload(request.get_json(silent=True))
    if errors:
        return error_response(status_code=400, message="Validation Error", user_message=" ".join(errors))

    user, err = create_admin_user(payload)
    if err:
        return error_response(status_code=409, message="Conflict", user_message=err)

    return success_response(
        status_code=201,
        message=f"Admin account created for {user.email}.",
        data={"id": user.id, "email": user.email, "role": "admin"},
    )
