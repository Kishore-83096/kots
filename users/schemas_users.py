from datetime import datetime
from users.models_users import UserProfile


def validate_registration_payload(payload):
    errors = []
    email = (payload or {}).get("email")
    password = (payload or {}).get("password")
    is_admin = bool((payload or {}).get("is_admin", False))
    is_master = bool((payload or {}).get("is_master", False))

    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Password is required.")

    if errors:
        return None, errors

    return {
        "email": email.strip().lower(),
        "password": password,
        "is_admin": is_admin,
        "is_master": is_master,
        "created_at": datetime.utcnow(),
    }, None


def validate_login_payload(payload):
    errors = []
    email = (payload or {}).get("email")
    password = (payload or {}).get("password")

    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Password is required.")

    if errors:
        return None, errors

    return {
        "email": email.strip().lower(),
        "password": password,
    }, None


def validate_update_payload(payload):
    errors = []
    email = (payload or {}).get("email")
    password = (payload or {}).get("password")

    if not email and not password:
        errors.append("Email or password is required.")

    if errors:
        return None, errors

    return {
        "email": email.strip().lower() if email else None,
        "password": password if password else None,
    }, None


def _parse_date_of_birth(value, errors):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            errors.append("date_of_birth must be a valid ISO-8601 date or datetime.")
            return None
    errors.append("date_of_birth must be a valid ISO-8601 date or datetime.")
    return None


def validate_update_profile_payload(payload):
    errors = []
    payload = payload or {}

    if "primary_email" in payload:
        errors.append("Primary email cannot be updated.")

    allowed_fields = {
        "username",
        "mobile_number",
        "profile_pic_url",
        "profile_pic_public_id",
        "profile_pic_folder",
        "bio",
        "date_of_birth",
        "city",
        "state",
        "country",
    }

    data = {}
    for key in allowed_fields:
        if key in payload:
            value = payload.get(key)
            if key == "username" and isinstance(value, str):
                value = value.strip() or None
            if key == "date_of_birth":
                value = _parse_date_of_birth(value, errors)
            data[key] = value

    if not data and not errors:
        errors.append("At least one profile field is required.")

    if errors:
        return None, errors

    return data, None


def serialize_users_health():
    return {"service": "users"}


def serialize_registration_response(user, role, token):
    return {
        "id": user.id,
        "email": user.email,
        "role": role,
        "is_admin": user.is_admin,
        "is_master": user.is_master,
        "token": token,
    }


def serialize_login_response(user, role, token):
    return {
        "email": user.email,
        "role": role,
        "is_admin": user.is_admin,
        "is_master": user.is_master,
        "token": token,
    }


def serialize_me_response(user, role):
    return {
        "email": user.email,
        "role": role,
        "is_admin": user.is_admin,
        "is_master": user.is_master,
        "created_at": user.created_at.isoformat(),
    }


def serialize_update_response(user, role):
    return {
        "email": user.email,
        "role": role,
    }


def serialize_delete_response(user):
    return {
        "email": user.email,
    }


def serialize_logout_response():
    return None


def serialize_user_profile(user, profile):
    if profile:
        return {
            "username": profile.username,
            "primary_email": user.email,
            "mobile_number": profile.mobile_number,
            "profile_pic_url": profile.profile_pic_url,
            "profile_pic_public_id": profile.profile_pic_public_id,
            "profile_pic_folder": profile.profile_pic_folder,
            "bio": profile.bio,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "city": profile.city,
            "state": profile.state,
            "country": profile.country,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }

    return {
        "username": None,
        "primary_email": user.email,
        "mobile_number": None,
        "profile_pic_url": None,
        "profile_pic_public_id": None,
        "profile_pic_folder": UserProfile.PROFILE_PIC_FOLDER,
        "bio": None,
        "date_of_birth": None,
        "city": None,
        "state": None,
        "country": None,
        "created_at": None,
        "updated_at": None,
    }


def serialize_amenity_summary(amenity):
    return {
        "id": amenity.id,
        "name": amenity.name,
        "description": amenity.description,
        "picture_url": amenity.picture_url,
    }


def serialize_building_with_stats(building):
    towers = building.towers or []
    flats = []
    for tower in towers:
        flats.extend(tower.flats or [])

    available_flats = [flat for flat in flats if flat.is_available]
    amenities = building.amenities or []

    full_address = ", ".join(
        part for part in [building.address, building.city, building.state, building.pincode] if part
    )

    return {
        "id": building.id,
        "name": building.name,
        "address": building.address,
        "city": building.city,
        "state": building.state,
        "pincode": building.pincode,
        "full_address": full_address,
        "total_towers": building.total_towers,
        "picture_url": building.picture_url,
        "towers_count": len(towers),
        "flats_count": len(flats),
        "available_flats_count": len(available_flats),
        "amenities": [serialize_amenity_summary(amenity) for amenity in amenities],
    }


def serialize_tower_summary(tower):
    flats = tower.flats or []
    available_flats = [flat for flat in flats if flat.is_available]
    return {
        "id": tower.id,
        "name": tower.name,
        "floors": tower.floors,
        "total_flats": tower.total_flats,
        "picture_url": tower.picture_url,
        "flats_count": len(flats),
        "available_flats_count": len(available_flats),
    }


def serialize_building_detail(building):
    towers = building.towers or []
    amenities = building.amenities or []
    full_address = ", ".join(
        part for part in [building.address, building.city, building.state, building.pincode] if part
    )
    return {
        "id": building.id,
        "name": building.name,
        "address": building.address,
        "city": building.city,
        "state": building.state,
        "pincode": building.pincode,
        "full_address": full_address,
        "picture_url": building.picture_url,
        "towers": [serialize_tower_summary(tower) for tower in towers],
        "amenities": [serialize_amenity_summary(amenity) for amenity in amenities],
    }


def serialize_building_address(building):
    full_address = ", ".join(
        part for part in [building.address, building.city, building.state, building.pincode] if part
    )
    return {
        "address": building.address,
        "city": building.city,
        "state": building.state,
        "pincode": building.pincode,
        "full_address": full_address,
    }


def serialize_tower_detail_with_building(tower, building):
    flats = tower.flats or []
    available_flats = [flat for flat in flats if flat.is_available]
    return {
        "tower": {
            "id": tower.id,
            "name": tower.name,
            "floors": tower.floors,
            "total_flats": tower.total_flats,
            "picture_url": tower.picture_url,
            "flats_count": len(flats),
            "available_flats_count": len(available_flats),
        },
        "building": {
            "id": building.id,
            "name": building.name,
            "picture_url": building.picture_url,
            **serialize_building_address(building),
        },
    }


def serialize_flat_summary(flat):
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
    }


def serialize_flats_response(flats, tower, building, page, per_page, total, total_pages):
    return {
        "building": {
            "id": building.id,
            "name": building.name,
            "address": building.address,
            "city": building.city,
            "state": building.state,
            "pincode": building.pincode,
            "full_address": ", ".join(
                part for part in [building.address, building.city, building.state, building.pincode] if part
            ),
        },
        "tower": {
            "id": tower.id,
            "name": tower.name,
        },
        "items": [serialize_flat_summary(flat) for flat in flats],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }


def serialize_flat_detail(flat, tower, building):
    return {
        "flat": serialize_flat_summary(flat),
        "tower": {
            "id": tower.id,
            "name": tower.name,
        },
        "building": {
            "id": building.id,
            "name": building.name,
            "address": building.address,
            "city": building.city,
            "state": building.state,
            "pincode": building.pincode,
            "full_address": ", ".join(
                part for part in [building.address, building.city, building.state, building.pincode] if part
            ),
        },
        "amenities": [serialize_amenity_summary(amenity) for amenity in (flat.amenities or [])],
    }


def serialize_booking(booking):
    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "flat_id": booking.flat_id,
        "tower_id": booking.tower_id,
        "building_id": booking.building_id,
        "status": booking.status,
        "security_deposit": str(booking.security_deposit) if booking.security_deposit is not None else None,
        "paid": booking.paid,
        "building_full_address": booking.building_full_address,
        "user_name": booking.user_name,
        "created_at": booking.created_at.isoformat(),
    }
