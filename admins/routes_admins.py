from flask import Blueprint
from response import success_response
from permissions import role_required

admins_bp = Blueprint("admins", __name__, url_prefix="/admins")

@admins_bp.route("/health")
def health():
    return success_response(message="Admins service healthy", data={"service": "admins"})


@admins_bp.route("/dashboard")
@role_required("admin", "master")
def dashboard():
    return success_response(message="Admins dashboard", data={"scope": "admin"})

