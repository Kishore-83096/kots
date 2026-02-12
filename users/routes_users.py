from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from common.response import success_response, error_response
from users.services_users import (
    users_health_service,
    register_user_service,
    login_user_service,
    me_service,
    profile_service,
    update_profile_service,
    upload_profile_picture_service,
    remove_profile_picture_service,
    update_me_service,
    delete_me_service,
    logout_service,
    list_buildings_service,
    get_building_detail_service,
    get_tower_detail_service,
    list_tower_flats_service,
    get_flat_detail_service,
    list_building_towers_service,
    create_security_deposit_booking_service,
    list_user_bookings_service,
    get_user_booking_service,
)

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/health")
def health():
    result, err = users_health_service()
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)

@users_bp.route("/register", methods=["POST"])
def register():
    result, err = register_user_service(request.get_json(silent=True))
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/login", methods=["POST"])
def login():
    result, err = login_user_service(request.get_json(silent=True))
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    result, err = me_service(get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    result, err = profile_service(get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    result, err = update_profile_service(get_jwt_identity(), request.get_json(silent=True))
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/profile/picture", methods=["POST"])
@jwt_required()
def upload_profile_picture():
    result, err = upload_profile_picture_service(
        get_jwt_identity(),
        request.files.get("file"),
        request.form.get("folder"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/profile/picture", methods=["DELETE"])
@jwt_required()
def remove_profile_picture():
    result, err = remove_profile_picture_service(get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_me():
    result, err = update_me_service(get_jwt_identity(), request.get_json(silent=True))
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/me", methods=["DELETE"])
@jwt_required()
def delete_me():
    result, err = delete_me_service(get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    result, err = logout_service(get_jwt_identity(), get_jwt())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/buildings", methods=["GET"])
@jwt_required()
def list_buildings():
    result, err = list_buildings_service()
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/buildings/<int:building_id>", methods=["GET"])
@jwt_required()
def get_building_detail(building_id):
    result, err = get_building_detail_service(building_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/buildings/<int:building_id>/towers/<int:tower_id>", methods=["GET"])
@jwt_required()
def get_tower_detail(building_id, tower_id):
    result, err = get_tower_detail_service(building_id, tower_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/buildings/<int:building_id>/towers/<int:tower_id>/flats", methods=["GET"])
@jwt_required()
def list_tower_flats(building_id, tower_id):
    result, err = list_tower_flats_service(
        building_id,
        tower_id,
        request.args.get("status"),
        request.args.get("page"),
    )
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/buildings/<int:building_id>/towers/<int:tower_id>/flats/<int:flat_id>", methods=["GET"])
@jwt_required()
def get_flat_detail(building_id, tower_id, flat_id):
    result, err = get_flat_detail_service(building_id, tower_id, flat_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/buildings/<int:building_id>/towers", methods=["GET"])
@jwt_required()
def list_building_towers(building_id):
    result, err = list_building_towers_service(building_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/flats/<int:flat_id>/bookings", methods=["POST"])
@jwt_required()
def create_security_deposit_booking(flat_id):
    result, err = create_security_deposit_booking_service(get_jwt_identity(), flat_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/bookings", methods=["GET"])
@jwt_required()
def list_user_bookings():
    result, err = list_user_bookings_service(get_jwt_identity())
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)


@users_bp.route("/bookings/<int:booking_id>", methods=["GET"])
@jwt_required()
def get_user_booking(booking_id):
    result, err = get_user_booking_service(get_jwt_identity(), booking_id)
    if err:
        return error_response(**err, add_size=True)
    return success_response(status_code=result["status_code"], message=result["message"], data=result["data"], add_size=True)
