from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from common.response import success_response, error_response
from common.permissions import role_required
from admins.services_admins import (
    admins_health_service,
    admins_dashboard_service,
    create_building_service,
    update_building_service,
    delete_building_service,
    list_admin_buildings_service,
    create_tower_service,
    update_tower_service,
    list_building_towers_service,
    get_tower_service,
    get_building_service,
    create_flat_service,
    update_flat_service,
    update_tower_flat_service,
    list_tower_flats_service,
    get_flat_service,
    delete_tower_service,
    delete_flat_service,
    create_amenity_service,
    update_amenity_service,
    list_building_amenities_service,
    set_flat_amenities_service,
    delete_amenity_service,
    list_admin_bookings_service,
    get_admin_booking_service,
    update_admin_booking_status_service,
)

admins_bp = Blueprint("admins", __name__, url_prefix="/admins")

@admins_bp.route("/health")
def health():
    result, err = admins_health_service()
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/dashboard")
@role_required("admin", "master")
def dashboard():
    result, err = admins_dashboard_service()
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings", methods=["POST"])
@role_required("admin", "master")
def create_building():
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = create_building_service(
        get_jwt_identity(),
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>", methods=["PUT"])
@role_required("admin", "master")
def update_building(building_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = update_building_service(
        building_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings", methods=["PUT"])
@role_required("admin", "master")
def update_building_by_body():
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    building_id = (payload or {}).get("id") or (payload or {}).get("building_id")
    try:
        building_id = int(building_id)
    except (TypeError, ValueError):
        return error_response(
            status_code=400,
            message="Validation Error",
            user_message="Building id is required.",
        )

    result, err = update_building_service(
        building_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>", methods=["DELETE"])
@role_required("admin", "master")
def delete_building(building_id):
    result, err = delete_building_service(get_jwt_identity(), building_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/my", methods=["GET"])
@role_required("admin", "master")
def list_my_buildings():
    result, err = list_admin_buildings_service(get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>", methods=["GET"])
@role_required("admin", "master")
def get_building(building_id):
    result, err = get_building_service(get_jwt_identity(), building_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/towers/<int:tower_id>/flats", methods=["POST"])
@role_required("admin", "master")
def create_flat(tower_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = create_flat_service(
        get_jwt_identity(),
        tower_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/flats/<int:flat_id>", methods=["PUT"])
@role_required("admin", "master")
def update_flat(flat_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = update_flat_service(
        get_jwt_identity(),
        flat_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/towers/<int:tower_id>/flats/<int:flat_id>", methods=["PUT"])
@role_required("admin", "master")
def update_tower_flat(tower_id, flat_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = update_tower_flat_service(
        get_jwt_identity(),
        tower_id,
        flat_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/towers/<int:tower_id>/flats", methods=["GET"])
@role_required("admin", "master")
def list_tower_flats(tower_id):
    result, err = list_tower_flats_service(get_jwt_identity(), tower_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/towers/<int:tower_id>/flats/<int:flat_id>", methods=["GET"])
@role_required("admin", "master")
def get_flat(tower_id, flat_id):
    result, err = get_flat_service(get_jwt_identity(), tower_id, flat_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/towers/<int:tower_id>", methods=["DELETE"])
@role_required("admin", "master")
def delete_tower(tower_id):
    result, err = delete_tower_service(get_jwt_identity(), tower_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/flats/<int:flat_id>", methods=["DELETE"])
@role_required("admin", "master")
def delete_flat(flat_id):
    result, err = delete_flat_service(get_jwt_identity(), flat_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>/amenities", methods=["POST"])
@role_required("admin", "master")
def create_amenity(building_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = create_amenity_service(
        get_jwt_identity(),
        building_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>/amenities", methods=["GET"])
@role_required("admin", "master")
def list_building_amenities(building_id):
    result, err = list_building_amenities_service(get_jwt_identity(), building_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/amenities/<int:amenity_id>", methods=["PUT"])
@role_required("admin", "master")
def update_amenity(amenity_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = update_amenity_service(
        get_jwt_identity(),
        amenity_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/flats/<int:flat_id>/amenities", methods=["PUT"])
@role_required("admin", "master")
def set_flat_amenities(flat_id):
    payload = request.get_json(silent=True)
    result, err = set_flat_amenities_service(get_jwt_identity(), flat_id, payload)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/amenities/<int:amenity_id>", methods=["DELETE"])
@role_required("admin", "master")
def delete_amenity(amenity_id):
    result, err = delete_amenity_service(get_jwt_identity(), amenity_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/bookings", methods=["GET"])
@role_required("admin", "master")
def list_bookings():
    result, err = list_admin_bookings_service(get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/bookings/<int:booking_id>", methods=["GET"])
@role_required("admin", "master")
def get_booking(booking_id):
    result, err = get_admin_booking_service(get_jwt_identity(), booking_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/bookings/<int:booking_id>/status", methods=["PUT"])
@role_required("admin", "master")
def update_booking_status(booking_id):
    result, err = update_admin_booking_status_service(get_jwt_identity(), booking_id, request.get_json(silent=True))
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>/towers", methods=["POST"])
@role_required("admin", "master")
def create_tower(building_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = create_tower_service(
        get_jwt_identity(),
        building_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/towers/<int:tower_id>", methods=["PUT"])
@role_required("admin", "master")
def update_tower(tower_id):
    payload = request.form.to_dict() if request.form else request.get_json(silent=True)
    result, err = update_tower_service(
        get_jwt_identity(),
        tower_id,
        payload,
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>/towers", methods=["GET"])
@role_required("admin", "master")
def list_building_towers(building_id):
    result, err = list_building_towers_service(get_jwt_identity(), building_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@admins_bp.route("/buildings/<int:building_id>/towers/<int:tower_id>", methods=["GET"])
@role_required("admin", "master")
def get_tower(building_id, tower_id):
    result, err = get_tower_service(get_jwt_identity(), building_id, tower_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)
