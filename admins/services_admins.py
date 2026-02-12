import os
import cloudinary
import cloudinary.uploader
from extensions import db
from admins.models_admins import Building, Tower, Flat, Amenity, Booking
from admins.schemas_admins import (
    serialize_admins_health,
    serialize_admins_dashboard,
    validate_building_create_payload,
    validate_building_update_payload,
    serialize_building,
    validate_tower_create_payload,
    validate_tower_update_payload,
    serialize_tower,
    serialize_tower_with_building,
    validate_flat_create_payload,
    serialize_flat,
    validate_flat_update_payload,
    validate_amenity_create_payload,
    serialize_amenity,
    serialize_booking_admin,
    validate_booking_status_payload,
)




# Helper functions for error handling, input parsing, Cloudinary image management, and ownership checks.
def _error(status_code, message, user_message):
    return {
        "status_code": status_code,
        "message": message,
        "user_message": user_message,
    }

def _parse_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
    
def _require_admin_id(admin_id):
    try:
        return int(admin_id), None
    except (TypeError, ValueError):
        return None, _error(401, "Unauthorized", "Invalid token.")
    
def _require_cloudinary_config():
    if not (os.getenv("CLOUDINARY_URL") or cloudinary.config().cloud_name):
        return _error(500, "Configuration Error", "Cloudinary is not configured.")
    return None

def _upload_image(file, folder, default_folder, upload_error_message):
    if not file:
        return None, None, None, None

    err = _require_cloudinary_config()
    if err:
        return None, None, None, err

    target_folder = folder or default_folder
    try:
        upload_result = cloudinary.uploader.upload(
            file,
            folder=target_folder,
            resource_type="image",
        )
    except Exception:
        return None, None, None, _error(502, "Upload Error", upload_error_message)

    picture_url = upload_result.get("secure_url") or upload_result.get("url")
    picture_public_id = upload_result.get("public_id")
    return picture_url, picture_public_id, target_folder, None

def _destroy_cloudinary_assets(public_ids):
    if not public_ids:
        return
    if not (os.getenv("CLOUDINARY_URL") or cloudinary.config().cloud_name):
        return
    for public_id in public_ids:
        if not public_id:
            continue
        try:
            cloudinary.uploader.destroy(public_id, resource_type="image")
        except Exception:
            pass

def _maybe_destroy_old_image(old_public_id, new_public_id, should_delete):
    if should_delete and old_public_id and old_public_id != new_public_id:
        _destroy_cloudinary_assets([old_public_id])




# Admins module services for admin servicehealth check
def admins_health_service():
    # Service: Return static health payload for the admins module.
    return {
        "status_code": 200,
        "message": "Admins service healthy",
        "data": serialize_admins_health(),
    }, None




# Admins module service for dashboard data (currently static, can be expanded later).
def admins_dashboard_service():
    # Service: Return static admin dashboard payload.
    return {
        "status_code": 200,
        "message": "Admins dashboard",
        "data": serialize_admins_dashboard(),
    }, None




#create building with admin id, payload, file and folder(form data) and return building details or error
def create_building_service(admin_id, payload, file, folder):
    # Service: Create a building (optionally with image upload) for a given admin.
    payload, errors = validate_building_create_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    building = Building(
        admin_id=admin_id,
        name=payload["name"],
        address=payload["address"],
        city=payload["city"],
        state=payload["state"],
        pincode=payload["pincode"],
        total_towers=_parse_int(payload.get("total_towers")) or 0,
    )

    picture_url, public_id, target_folder, err = _upload_image(
        file,
        folder,
        Building.ASSET_PIC_FOLDER,
        "Failed to upload building picture.",
    )
    if err:
        return None, err
    if file:
        building.picture_url = picture_url
        building.picture_public_id = public_id
        building.picture_folder = target_folder

    db.session.add(building)
    db.session.commit()

    return {
        "status_code": 201,
        "message": "Building created",
        "data": serialize_building(building),
    }, None




#update building with building id, payload, file and folder(form data) and return updated building details or error
def update_building_service(building_id, payload, file, folder):
    # Service: Update building fields and optionally replace its image.
    payload, errors = validate_building_update_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    building = Building.query.get(building_id)
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    if "name" in payload and payload.get("name"):
        building.name = payload["name"]
    if "address" in payload and payload.get("address"):
        building.address = payload["address"]
    if "city" in payload and payload.get("city"):
        building.city = payload["city"]
    if "state" in payload and payload.get("state"):
        building.state = payload["state"]
    if "pincode" in payload and payload.get("pincode"):
        building.pincode = payload["pincode"]
    if "total_towers" in payload:
        parsed = _parse_int(payload.get("total_towers"))
        if parsed is None:
            return None, _error(400, "Validation Error", "total_towers must be an integer.")
        building.total_towers = parsed

    old_public_id = building.picture_public_id
    picture_url, public_id, target_folder, err = _upload_image(
        file,
        folder,
        building.picture_folder or Building.ASSET_PIC_FOLDER,
        "Failed to upload building picture.",
    )
    if err:
        return None, err
    if file:
        building.picture_url = picture_url
        building.picture_public_id = public_id
        building.picture_folder = target_folder

    db.session.commit()

    _maybe_destroy_old_image(old_public_id, building.picture_public_id, bool(file))

    return {
        "status_code": 200,
        "message": "Building updated",
        "data": serialize_building(building),
    }, None





#delete building with building id and return deleted building details or error(deletes all related towers, flats, amenities and images)
def delete_building_service(admin_id, building_id):
    # Service: Delete a building and all related towers, flats, amenities, and images.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    building = Building.query.get(building_id)
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    if building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only delete your own buildings.")

    asset_public_ids = []
    asset_public_ids.append(building.picture_public_id)
    amenities = Amenity.query.filter_by(building_id=building.id).all()
    for amenity in amenities:
        asset_public_ids.append(amenity.picture_public_id)

    towers = Tower.query.filter_by(building_id=building.id).all()
    for tower in towers:
        asset_public_ids.append(tower.picture_public_id)
        flats = Flat.query.filter_by(tower_id=tower.id).all()
        for flat in flats:
            asset_public_ids.append(flat.picture_public_id)

    building_name = building.name
    db.session.delete(building)
    db.session.commit()

    _destroy_cloudinary_assets(asset_public_ids)

    return {
        "status_code": 200,
        "message": "Building deleted",
        "data": {"id": building_id, "name": building_name},
    }, None





# List buildings with admin id and return list of buildings created by the admin or error
def list_admin_buildings_service(admin_id):
    # Service: List all buildings created by the given admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    buildings = Building.query.filter_by(admin_id=admin_id).order_by(Building.id.desc()).all()
    return {
        "status_code": 200,
        "message": "Admin buildings fetched",
        "data": [serialize_building(building) for building in buildings],
    }, None




# Fetch a single building with admin id and building id, return building details if owned by admin or error
def get_building_service(admin_id, building_id):
    # Service: Fetch a single building owned by the given admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    building = Building.query.get(building_id)
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    if building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only access your own buildings.")

    return {
        "status_code": 200,
        "message": "Building fetched",
        "data": serialize_building(building),
    }, None





# Create a flat with admin id, tower id, payload, file and folder(form data) and return flat details or error
def create_flat_service(admin_id, tower_id, payload, file, folder):
    # Service: Create a flat for a tower owned by the given admin (optional image upload).
    payload, errors = validate_flat_create_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    tower = Tower.query.get(tower_id)
    if not tower:
        return None, _error(404, "Not Found", "Tower not found.")

    if not tower.building or tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only create flats for your own buildings.")

    floor_number = _parse_int(payload.get("floor_number"))
    area_sqft = _parse_int(payload.get("area_sqft"))
    if floor_number is None:
        return None, _error(400, "Validation Error", "floor_number must be an integer.")
    if area_sqft is None:
        return None, _error(400, "Validation Error", "area_sqft must be an integer.")

    try:
        rent_amount = float(payload.get("rent_amount"))
        security_deposit = float(payload.get("security_deposit"))
    except (TypeError, ValueError):
        return None, _error(400, "Validation Error", "rent_amount and security_deposit must be numbers.")

    is_available = payload.get("is_available")
    if isinstance(is_available, str):
        is_available = is_available.lower() in ("true", "1", "t", "yes")
    if is_available is None:
        is_available = True

    flat = Flat(
        flat_number=payload["flat_number"],
        floor_number=floor_number,
        bhk_type=payload["bhk_type"],
        area_sqft=area_sqft,
        rent_amount=rent_amount,
        security_deposit=security_deposit,
        is_available=is_available,
        tower_id=tower.id,
    )

    picture_url, public_id, target_folder, err = _upload_image(
        file,
        folder,
        Flat.ASSET_PIC_FOLDER,
        "Failed to upload flat picture.",
    )
    if err:
        return None, err
    if file:
        flat.picture_url = picture_url
        flat.picture_public_id = public_id
        flat.picture_folder = target_folder

    db.session.add(flat)
    db.session.commit()

    return {
        "status_code": 201,
        "message": "Flat created",
        "data": serialize_flat(flat),
    }, None





# Update a flat with admin id, flat id, payload, file and folder(form data) and return updated flat details or error
def update_flat_service(admin_id, flat_id, payload, file, folder):
    # Service: Update flat fields and optionally replace its image.
    payload, errors = validate_flat_update_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    flat = Flat.query.get(flat_id)
    if not flat:
        return None, _error(404, "Not Found", "Flat not found.")

    if not flat.tower or not flat.tower.building or flat.tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only update flats for your own buildings.")

    if "flat_number" in payload and payload.get("flat_number"):
        flat.flat_number = payload["flat_number"]
    if "floor_number" in payload:
        floor_number = _parse_int(payload.get("floor_number"))
        if floor_number is None:
            return None, _error(400, "Validation Error", "floor_number must be an integer.")
        flat.floor_number = floor_number
    if "bhk_type" in payload and payload.get("bhk_type"):
        flat.bhk_type = payload["bhk_type"]
    if "area_sqft" in payload:
        area_sqft = _parse_int(payload.get("area_sqft"))
        if area_sqft is None:
            return None, _error(400, "Validation Error", "area_sqft must be an integer.")
        flat.area_sqft = area_sqft
    if "rent_amount" in payload:
        try:
            flat.rent_amount = float(payload.get("rent_amount"))
        except (TypeError, ValueError):
            return None, _error(400, "Validation Error", "rent_amount must be a number.")
    if "security_deposit" in payload:
        try:
            flat.security_deposit = float(payload.get("security_deposit"))
        except (TypeError, ValueError):
            return None, _error(400, "Validation Error", "security_deposit must be a number.")
    if "is_available" in payload:
        is_available = payload.get("is_available")
        if isinstance(is_available, str):
            is_available = is_available.lower() in ("true", "1", "t", "yes")
        flat.is_available = bool(is_available)

    old_public_id = flat.picture_public_id
    picture_url, public_id, target_folder, err = _upload_image(
        file,
        folder,
        flat.picture_folder or Flat.ASSET_PIC_FOLDER,
        "Failed to upload flat picture.",
    )
    if err:
        return None, err
    if file:
        flat.picture_url = picture_url
        flat.picture_public_id = public_id
        flat.picture_folder = target_folder

    db.session.commit()

    _maybe_destroy_old_image(old_public_id, flat.picture_public_id, bool(file))

    return {
        "status_code": 200,
        "message": "Flat updated",
        "data": serialize_flat(flat),
    }, None





# List all flats for a tower owned by the given admin, return list of flats or error
def list_tower_flats_service(admin_id, tower_id):
    # Service: List all flats for a tower owned by the given admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    tower = Tower.query.get(tower_id)
    if not tower:
        return None, _error(404, "Not Found", "Tower not found.")

    if not tower.building or tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only access flats for your own buildings.")

    flats = Flat.query.filter_by(tower_id=tower.id).order_by(Flat.id.desc()).all()

    return {
        "status_code": 200,
        "message": "Flats fetched",
        "data": [serialize_flat(flat) for flat in flats],
    }, None





# Fetch a single flat with admin id, tower id and flat id, return flat details if owned by admin or error
def get_flat_service(admin_id, tower_id, flat_id):
    # Service: Fetch a single flat by tower, restricted to the owning admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    flat = Flat.query.get(flat_id)
    if not flat:
        return None, _error(404, "Not Found", "Flat not found.")

    if flat.tower_id != tower_id:
        return None, _error(404, "Not Found", "Flat not found for this tower.")

    if not flat.tower or not flat.tower.building or flat.tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only access flats for your own buildings.")

    return {
        "status_code": 200,
        "message": "Flat fetched",
        "data": serialize_flat(flat),
    }, None





# Create an amenity with admin id, building id, payload, file and folder(form data) and return amenity details or error
def create_amenity_service(admin_id, building_id, payload, file, folder):
    # Service: Create an amenity for a building owned by the given admin (optional image upload).
    payload, errors = validate_amenity_create_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    building = Building.query.get(building_id)
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    if building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only manage amenities for your own buildings.")

    amenity = Amenity(
        building_id=building.id,
        name=payload["name"],
        description=payload.get("description"),
    )

    picture_url, public_id, target_folder, err = _upload_image(
        file,
        folder,
        Amenity.ASSET_PIC_FOLDER,
        "Failed to upload amenity picture.",
    )
    if err:
        return None, err
    if file:
        amenity.picture_url = picture_url
        amenity.picture_public_id = public_id
        amenity.picture_folder = target_folder

    db.session.add(amenity)
    db.session.commit()

    return {
        "status_code": 201,
        "message": "Amenity created",
        "data": serialize_amenity(amenity),
    }, None





# List amenities for a building owned by the given admin, return list of amenities or error
def list_building_amenities_service(admin_id, building_id):
    # Service: List amenities for a building owned by the given admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    building = Building.query.get(building_id)
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    if building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only access amenities for your own buildings.")

    amenities = Amenity.query.filter_by(building_id=building.id).order_by(Amenity.id.desc()).all()

    return {
        "status_code": 200,
        "message": "Amenities fetched",
        "data": [serialize_amenity(amenity) for amenity in amenities],
    }, None





# Replace a flat's amenities with a validated set from the same building, return updated amenity list or error
def set_flat_amenities_service(admin_id, flat_id, payload):
    # Service: Replace a flat's amenities with a validated set from the same building.
    payload = payload or {}
    amenity_ids = payload.get("amenity_ids")
    if not isinstance(amenity_ids, list) or not amenity_ids:
        return None, _error(400, "Validation Error", "amenity_ids must be a non-empty list.")

    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    flat = Flat.query.get(flat_id)
    if not flat:
        return None, _error(404, "Not Found", "Flat not found.")

    if not flat.tower or not flat.tower.building or flat.tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only update amenities for your own buildings.")

    amenities = Amenity.query.filter(
        Amenity.id.in_(amenity_ids),
        Amenity.building_id == flat.tower.building_id,
    ).all()

    if len(amenities) != len(set(amenity_ids)):
        return None, _error(400, "Validation Error", "One or more amenities are invalid for this building.")

    flat.amenities = amenities
    db.session.commit()

    return {
        "status_code": 200,
        "message": "Flat amenities updated",
        "data": {
            "flat_id": flat.id,
            "amenity_ids": [amenity.id for amenity in amenities],
        },
    }, None





# Delete an amenity with admin id and amenity id, return deleted amenity details or error(deletes related image)
def delete_amenity_service(admin_id, amenity_id):
    # Service: Delete an amenity owned by the admin and remove its image.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    amenity = Amenity.query.get(amenity_id)
    if not amenity:
        return None, _error(404, "Not Found", "Amenity not found.")

    if not amenity.building or amenity.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only delete amenities for your own buildings.")

    old_public_id = amenity.picture_public_id
    amenity_id_value = amenity.id
    amenity_name = amenity.name

    db.session.delete(amenity)
    db.session.commit()

    _destroy_cloudinary_assets([old_public_id])

    return {
        "status_code": 200,
        "message": "Amenity deleted",
        "data": {"id": amenity_id_value, "name": amenity_name},
    }, None





# Delete a tower with admin id and tower id, return deleted tower details or error(deletes all related flats and images)
def delete_tower_service(admin_id, tower_id):
    # Service: Delete a tower (and its flats) owned by the admin and remove images.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    tower = Tower.query.get(tower_id)
    if not tower:
        return None, _error(404, "Not Found", "Tower not found.")

    if not tower.building or tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only delete towers for your own buildings.")

    asset_public_ids = [tower.picture_public_id]
    flats = Flat.query.filter_by(tower_id=tower.id).all()
    for flat in flats:
        asset_public_ids.append(flat.picture_public_id)

    tower_id_value = tower.id
    db.session.delete(tower)
    db.session.commit()

    _destroy_cloudinary_assets(asset_public_ids)

    return {
        "status_code": 200,
        "message": "Tower deleted",
        "data": {"id": tower_id_value},
    }, None





# Delete a flat with admin id and flat id, return deleted flat details or error(deletes related image)
def delete_flat_service(admin_id, flat_id):
    # Service: Delete a flat owned by the admin and remove its image.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    flat = Flat.query.get(flat_id)
    if not flat:
        return None, _error(404, "Not Found", "Flat not found.")

    if not flat.tower or not flat.tower.building or flat.tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only delete flats for your own buildings.")

    old_public_id = flat.picture_public_id
    flat_id_value = flat.id
    db.session.delete(flat)
    db.session.commit()

    _destroy_cloudinary_assets([old_public_id])

    return {
        "status_code": 200,
        "message": "Flat deleted",
        "data": {"id": flat_id_value},
    }, None





# Create a tower with admin id, building id, payload, file and folder(form data) and return tower details or error
def create_tower_service(admin_id, building_id, payload, file, folder):
    # Service: Create a tower for a building owned by the admin (optional image upload).
    payload, errors = validate_tower_create_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    building = Building.query.get(building_id)
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    if building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only create towers for your own buildings.")

    floors = _parse_int(payload.get("floors"))
    if floors is None:
        return None, _error(400, "Validation Error", "floors must be an integer.")

    total_flats = _parse_int(payload.get("total_flats")) or 0

    tower = Tower(
        name=payload["name"],
        floors=floors,
        total_flats=total_flats,
        building_id=building.id,
    )

    picture_url, public_id, target_folder, err = _upload_image(
        file,
        folder,
        Tower.ASSET_PIC_FOLDER,
        "Failed to upload tower picture.",
    )
    if err:
        return None, err
    if file:
        tower.picture_url = picture_url
        tower.picture_public_id = public_id
        tower.picture_folder = target_folder

    db.session.add(tower)
    db.session.commit()

    return {
        "status_code": 201,
        "message": "Tower created",
        "data": serialize_tower(tower),
    }, None





# Update a tower with admin id, tower id, payload, file and folder(form data) and return updated tower details or error
def update_tower_service(admin_id, tower_id, payload, file, folder):
    # Service: Update tower fields and optionally replace its image.
    payload, errors = validate_tower_update_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    tower = Tower.query.get(tower_id)
    if not tower:
        return None, _error(404, "Not Found", "Tower not found.")

    if not tower.building or tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only update towers for your own buildings.")

    if "name" in payload and payload.get("name"):
        tower.name = payload["name"]
    if "floors" in payload:
        floors = _parse_int(payload.get("floors"))
        if floors is None:
            return None, _error(400, "Validation Error", "floors must be an integer.")
        tower.floors = floors
    if "total_flats" in payload:
        total_flats = _parse_int(payload.get("total_flats"))
        if total_flats is None:
            return None, _error(400, "Validation Error", "total_flats must be an integer.")
        tower.total_flats = total_flats

    old_public_id = tower.picture_public_id
    picture_url, public_id, target_folder, err = _upload_image(
        file,
        folder,
        tower.picture_folder or Tower.ASSET_PIC_FOLDER,
        "Failed to upload tower picture.",
    )
    if err:
        return None, err
    if file:
        tower.picture_url = picture_url
        tower.picture_public_id = public_id
        tower.picture_folder = target_folder

    db.session.commit()

    _maybe_destroy_old_image(old_public_id, tower.picture_public_id, bool(file))

    return {
        "status_code": 200,
        "message": "Tower updated",
        "data": serialize_tower(tower),
    }, None





# List all towers for a building owned by the given admin, return list of towers or error
def list_building_towers_service(admin_id, building_id):
    # Service: List towers for a building owned by the given admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    building = Building.query.get(building_id)
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    if building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only access towers for your own buildings.")

    towers = Tower.query.filter_by(building_id=building.id).order_by(Tower.id.desc()).all()

    return {
        "status_code": 200,
        "message": "Towers fetched",
        "data": [serialize_tower_with_building(tower) for tower in towers],
    }, None






# Fetch a single tower with admin id, building id and tower id, return tower details if owned by admin or error
def get_tower_service(admin_id, building_id, tower_id):
    # Service: Fetch a single tower by building, restricted to the owning admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    tower = Tower.query.get(tower_id)
    if not tower:
        return None, _error(404, "Not Found", "Tower not found.")

    if tower.building_id != building_id:
        return None, _error(404, "Not Found", "Tower not found for this building.")

    if not tower.building or tower.building.admin_id != admin_id:
        return None, _error(403, "Forbidden", "You can only access towers for your own buildings.")

    return {
        "status_code": 200,
        "message": "Tower fetched",
        "data": serialize_tower_with_building(tower),
    }, None


def list_admin_bookings_service(admin_id):
    # Service: List all bookings for buildings owned by the admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    rows = (
        db.session.query(Booking, Building, Tower, Flat)
        .join(Building, Booking.building_id == Building.id)
        .join(Tower, Booking.tower_id == Tower.id)
        .join(Flat, Booking.flat_id == Flat.id)
        .filter(Building.admin_id == admin_id)
        .order_by(Booking.id.desc())
        .all()
    )

    return {
        "status_code": 200,
        "message": "Bookings fetched",
        "data": [serialize_booking_admin(b, bd, t, f) for (b, bd, t, f) in rows],
    }, None


def get_admin_booking_service(admin_id, booking_id):
    # Service: Fetch a single booking for buildings owned by the admin.
    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    row = (
        db.session.query(Booking, Building, Tower, Flat)
        .join(Building, Booking.building_id == Building.id)
        .join(Tower, Booking.tower_id == Tower.id)
        .join(Flat, Booking.flat_id == Flat.id)
        .filter(Building.admin_id == admin_id, Booking.id == booking_id)
        .first()
    )

    if not row:
        return None, _error(404, "Not Found", "Booking not found.")

    booking, building, tower, flat = row
    return {
        "status_code": 200,
        "message": "Booking fetched",
        "data": serialize_booking_admin(booking, building, tower, flat),
    }, None


def update_admin_booking_status_service(admin_id, booking_id, payload):
    # Service: Update booking status for bookings owned by the admin.
    payload, errors = validate_booking_status_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    admin_id, err = _require_admin_id(admin_id)
    if err:
        return None, err

    booking = (
        db.session.query(Booking)
        .join(Building, Booking.building_id == Building.id)
        .filter(Building.admin_id == admin_id, Booking.id == booking_id)
        .first()
    )
    if not booking:
        return None, _error(404, "Not Found", "Booking not found.")

    status = payload["status"]
    if status not in ("PENDING", "APPROVED", "DECLINED"):
        return None, _error(400, "Validation Error", "status must be PENDING, APPROVED, or DECLINED.")

    booking.status = status
    db.session.commit()

    return {
        "status_code": 200,
        "message": "Booking status updated",
        "data": {"id": booking.id, "status": booking.status},
    }, None
