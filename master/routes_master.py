from flask import Blueprint, request
from common.response import success_response, error_response
from common.permissions import role_required
from flask_jwt_extended import get_jwt_identity
from master.services_master import (
    master_health_service,
    master_control_service,
    master_create_admin_service,
    master_list_admins_service,
    master_get_single_admin_service,
)

master_bp = Blueprint("master", __name__, url_prefix="/master")

@master_bp.route("/health")
def health():
    result, err = master_health_service()
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@master_bp.route("/control")
@role_required("master")
def control_panel():
    result, err = master_control_service()
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@master_bp.route("/create-admin", methods=["POST"])
@role_required("master")
def create_admin():
    result, err = master_create_admin_service(request.get_json(silent=True))
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@master_bp.route("/admins", methods=["GET"])
@role_required("master")
def get_admins():
    result, err = master_list_admins_service(request.args, get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@master_bp.route("/admins/<int:admin_id>", methods=["GET"])
@role_required("master")
def get_admin(admin_id):
    result, err = master_get_single_admin_service(admin_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)
