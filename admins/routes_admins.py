from flask import Blueprint
from common.response import success_response, error_response
from common.permissions import role_required
from admins.services_admins import admins_health_service, admins_dashboard_service

admins_bp = Blueprint("admins", __name__, url_prefix="/admins")

@admins_bp.route("/health")
def health():
    result, err = admins_health_service()
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])


@admins_bp.route("/dashboard")
@role_required("admin", "master")
def dashboard():
    result, err = admins_dashboard_service()
    if err:
        return error_response(**err)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"])
