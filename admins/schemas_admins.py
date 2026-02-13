def serialize_admins_health():
    return {"service": "admins"}


def serialize_admins_dashboard():
    return {"scope": "admin"}


def validate_building_create_payload(payload):
    errors = []
    payload = payload or {}

    name = payload.get("name")
    address = payload.get("address")
    city = payload.get("city")
    state = payload.get("state")
    pincode = payload.get("pincode")
    total_towers = payload.get("total_towers")

    if not name:
        errors.append("Name is required.")
    if not address:
        errors.append("Address is required.")
    if not city:
        errors.append("City is required.")
    if not state:
        errors.append("State is required.")
    if not pincode:
        errors.append("Pincode is required.")

    if errors:
        return None, errors

    return {
        "name": name.strip(),
        "address": address.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "pincode": str(pincode).strip(),
        "total_towers": total_towers,
    }, None


def validate_building_update_payload(payload):
    errors = []
    payload = payload or {}

    allowed_fields = {
        "name",
        "address",
        "city",
        "state",
        "pincode",
        "total_towers",
    }

    data = {}
    for key in allowed_fields:
        if key in payload:
            value = payload.get(key)
            if key in {"name", "address", "city", "state", "pincode"} and isinstance(value, str):
                value = value.strip()
            data[key] = value

    if not data:
        errors.append("At least one field is required.")

    if errors:
        return None, errors

    return data, None


def serialize_building(building):
    return {
        "id": building.id,
        "admin_id": building.admin_id,
        "name": building.name,
        "address": building.address,
        "city": building.city,
        "state": building.state,
        "pincode": building.pincode,
        "total_towers": building.total_towers,
        "picture_url": building.picture_url,
        "picture_public_id": building.picture_public_id,
        "picture_folder": building.picture_folder,
        "created_at": building.created_at.isoformat(),
    }


def validate_tower_create_payload(payload):
    errors = []
    payload = payload or {}

    name = payload.get("name")
    floors = payload.get("floors")
    total_flats = payload.get("total_flats")

    if not name:
        errors.append("Name is required.")
    if floors is None or floors == "":
        errors.append("Floors is required.")

    if errors:
        return None, errors

    return {
        "name": name.strip(),
        "floors": floors,
        "total_flats": total_flats,
    }, None


def serialize_tower(tower):
    return {
        "id": tower.id,
        "building_id": tower.building_id,
        "name": tower.name,
        "floors": tower.floors,
        "total_flats": tower.total_flats,
        "picture_url": tower.picture_url,
        "picture_public_id": tower.picture_public_id,
        "picture_folder": tower.picture_folder,
        "created_at": tower.created_at.isoformat(),
    }


def serialize_tower_with_building(tower):
    return {
        "id": tower.id,
        "building_id": tower.building_id,
        "building_name": tower.building.name if tower.building else None,
        "name": tower.name,
        "floors": tower.floors,
        "total_flats": tower.total_flats,
        "picture_url": tower.picture_url,
        "picture_public_id": tower.picture_public_id,
        "picture_folder": tower.picture_folder,
        "created_at": tower.created_at.isoformat(),
    }


def validate_flat_create_payload(payload):
    errors = []
    payload = payload or {}

    flat_number = payload.get("flat_number")
    floor_number = payload.get("floor_number")
    bhk_type = payload.get("bhk_type")
    area_sqft = payload.get("area_sqft")
    rent_amount = payload.get("rent_amount")
    security_deposit = payload.get("security_deposit")
    is_available = payload.get("is_available")

    if not flat_number:
        errors.append("Flat number is required.")
    if floor_number is None or floor_number == "":
        errors.append("Floor number is required.")
    if not bhk_type:
        errors.append("BHK type is required.")
    if area_sqft is None or area_sqft == "":
        errors.append("Area sqft is required.")
    if rent_amount is None or rent_amount == "":
        errors.append("Rent amount is required.")
    if security_deposit is None or security_deposit == "":
        errors.append("Security deposit is required.")

    if errors:
        return None, errors

    return {
        "flat_number": str(flat_number).strip(),
        "floor_number": floor_number,
        "bhk_type": str(bhk_type).strip(),
        "area_sqft": area_sqft,
        "rent_amount": rent_amount,
        "security_deposit": security_deposit,
        "is_available": is_available,
    }, None


def serialize_flat(flat):
    return {
        "id": flat.id,
        "tower_id": flat.tower_id,
        "flat_number": flat.flat_number,
        "floor_number": flat.floor_number,
        "bhk_type": flat.bhk_type,
        "area_sqft": flat.area_sqft,
        "rent_amount": str(flat.rent_amount),
        "security_deposit": str(flat.security_deposit),
        "is_available": flat.is_available,
        "picture_url": flat.picture_url,
        "picture_public_id": flat.picture_public_id,
        "picture_folder": flat.picture_folder,
        "amenity_ids": [amenity.id for amenity in flat.amenities] if hasattr(flat, "amenities") else [],
        "created_at": flat.created_at.isoformat(),
    }


def validate_flat_update_payload(payload):
    errors = []
    payload = payload or {}

    allowed_fields = {
        "flat_number",
        "floor_number",
        "bhk_type",
        "area_sqft",
        "rent_amount",
        "security_deposit",
        "is_available",
    }

    data = {}
    for key in allowed_fields:
        if key in payload:
            value = payload.get(key)
            if key in {"flat_number", "bhk_type"} and isinstance(value, str):
                value = value.strip()
            data[key] = value

    if not data:
        errors.append("At least one field is required.")

    if errors:
        return None, errors

    return data, None


def validate_amenity_create_payload(payload):
    errors = []
    payload = payload or {}

    name = payload.get("name")
    description = payload.get("description")

    if not name:
        errors.append("Name is required.")

    if errors:
        return None, errors

    return {
        "name": str(name).strip(),
        "description": str(description).strip() if description is not None else None,
    }, None


def validate_amenity_update_payload(payload):
    errors = []
    payload = payload or {}

    allowed_fields = {"name", "description"}

    data = {}
    for key in allowed_fields:
        if key in payload:
            value = payload.get(key)
            if isinstance(value, str):
                value = value.strip()
            data[key] = value

    if not data:
        errors.append("At least one field is required.")

    if "name" in data and not data.get("name"):
        errors.append("Name cannot be empty.")

    if errors:
        return None, errors

    return data, None


def serialize_amenity(amenity):
    return {
        "id": amenity.id,
        "building_id": amenity.building_id,
        "name": amenity.name,
        "description": amenity.description,
        "picture_url": amenity.picture_url,
        "picture_public_id": amenity.picture_public_id,
        "picture_folder": amenity.picture_folder,
        "created_at": amenity.created_at.isoformat(),
    }


def serialize_booking_admin(booking, building, tower, flat):
    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "flat_id": booking.flat_id,
        "tower_id": booking.tower_id,
        "building_id": booking.building_id,
        "status": booking.status,
        "security_deposit": str(booking.security_deposit) if booking.security_deposit is not None else None,
        "paid": booking.paid,
        "building": {
            "id": building.id,
            "name": building.name,
        },
        "tower": {
            "id": tower.id,
            "name": tower.name,
        },
        "flat": {
            "id": flat.id,
            "flat_number": flat.flat_number,
        },
        "created_at": booking.created_at.isoformat(),
    }


def validate_booking_status_payload(payload):
    errors = []
    payload = payload or {}
    status = payload.get("status")

    if not status:
        errors.append("status is required.")

    if errors:
        return None, errors

    return {"status": str(status).strip().upper()}, None


def validate_tower_update_payload(payload):
    errors = []
    payload = payload or {}

    allowed_fields = {
        "name",
        "floors",
        "total_flats",
    }

    data = {}
    for key in allowed_fields:
        if key in payload:
            value = payload.get(key)
            if key == "name" and isinstance(value, str):
                value = value.strip()
            data[key] = value

    if not data:
        errors.append("At least one field is required.")

    if errors:
        return None, errors

    return data, None
