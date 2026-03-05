from flask_jwt_extended import create_access_token
from uuid import uuid4
from flask import current_app, has_app_context
from extensions import db
import cloudinary
import cloudinary.uploader
import os
from users.models_users import RegistrationUser, UserProfile, RevokedToken
from admins.models_admins import Building, Tower, Flat, FlatPicture, Booking, Amenity
from sqlalchemy.orm import selectinload
from sqlalchemy import func, literal, or_
from common.image_compression import compress_image_to_100kb
from users.schemas_users import (
    validate_registration_payload,
    validate_login_payload,
    validate_update_payload,
    validate_update_profile_payload,
    validate_flat_search_params,
    validate_building_search_params,
    serialize_registration_response,
    serialize_login_response,
    serialize_me_response,
    serialize_update_response,
    serialize_delete_response,
    serialize_user_profile,
    serialize_users_health,
    serialize_logout_response,
    serialize_building_with_stats,
    serialize_building_detail,
    serialize_amenity_summary,
    serialize_tower_detail_with_building,
    serialize_flat_summary,
    serialize_flats_response,
    serialize_flat_search_response,
    serialize_building_search_response,
    serialize_flat_detail,
    serialize_flat_picture,
    serialize_tower_summary,
    serialize_booking,
    serialize_public_flat_listing,
)



def _error(status_code, message, user_message):
    return {
        "status_code": status_code,
        "message": message,
        "user_message": user_message,
    }


def _search_tuning():
    cfg = current_app.config if has_app_context() else {}
    return {
        "min_similarity": float(cfg.get("ADDRESS_TRIGRAM_MIN_SIMILARITY", 0.12)),
        "min_word_similarity": float(cfg.get("ADDRESS_TRIGRAM_MIN_WORD_SIMILARITY", 0.52)),
    }


def _normalized_search_text(search_text):
    return func.lower(literal((search_text or "").strip()))


def _address_rank_and_filter(search_text, include_name=False):
    tuning = _search_tuning()
    query_text = _normalized_search_text(search_text)
    address_text = func.lower(func.coalesce(Building.address, ""))
    city_text = func.lower(func.coalesce(Building.city, ""))
    state_text = func.lower(func.coalesce(Building.state, ""))
    pincode_text = func.lower(func.coalesce(Building.pincode, ""))
    full_address = func.concat_ws(" ", address_text, city_text, state_text, pincode_text)

    similarity_score = func.greatest(
        func.similarity(address_text, query_text),
        func.similarity(city_text, query_text),
        func.similarity(state_text, query_text),
        func.similarity(pincode_text, query_text),
        func.similarity(full_address, query_text),
    )
    word_similarity_score = func.greatest(
        func.word_similarity(query_text, address_text),
        func.word_similarity(query_text, city_text),
        func.word_similarity(query_text, state_text),
        func.word_similarity(query_text, pincode_text),
        func.word_similarity(query_text, full_address),
    )
    rank = (similarity_score * 0.35) + (word_similarity_score * 0.65)

    if include_name:
        building_name = func.lower(func.coalesce(Building.name, ""))
        name_word_similarity = func.word_similarity(query_text, building_name)
        name_similarity = func.similarity(building_name, query_text)
        rank = func.greatest(rank, (name_word_similarity * 0.9), (name_similarity * 0.8))

    min_similarity = tuning["min_similarity"]
    min_word_similarity = tuning["min_word_similarity"]
    trigram_ops = [
        address_text.bool_op("%")(query_text),
        city_text.bool_op("%")(query_text),
        state_text.bool_op("%")(query_text),
        pincode_text.bool_op("%")(query_text),
    ]
    if include_name:
        trigram_ops.append(func.lower(func.coalesce(Building.name, "")).bool_op("%")(query_text))
    include_filter = or_(*trigram_ops, similarity_score >= min_similarity, word_similarity_score >= min_word_similarity)

    return rank, include_filter


def _serialize_manager(admin_user, admin_profile):
    name = None
    phone = None
    if admin_profile:
        name = admin_profile.username or None
        phone = admin_profile.mobile_number or None
    if not name and admin_user:
        name = admin_user.email
    return {
        "name": name,
        "phone": phone,
    }


def _role_for_user(user):
    if user.is_master:
        return "master"
    if user.is_admin:
        return "admin"
    return "user"


def _get_user_by_identity(identity):
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None
    return RegistrationUser.query.get(user_id)


def register_user(payload):
    user = RegistrationUser(
        email=payload["email"],
        is_admin=payload["is_admin"],
        is_master=payload["is_master"],
        created_at=payload["created_at"],
    )
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={"nonce": str(uuid4())})
    role = _role_for_user(user)

    return {
        "user": user,
        "role": role,
        "token": token,
    }


def login_user(payload):
    user = RegistrationUser.query.filter_by(email=payload["email"]).first()
    if not user or not user.check_password(payload["password"]):
        return None, None

    token = create_access_token(identity=str(user.id), additional_claims={"nonce": str(uuid4())})
    role = _role_for_user(user)
    return user, {"role": role, "token": token}


def get_user_profile(identity):
    user = _get_user_by_identity(identity)
    if not user:
        return None, None
    role = _role_for_user(user)
    return user, role


def get_user_profile_details(identity):
    user = _get_user_by_identity(identity)
    if not user:
        return None, None
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    return user, profile


def update_user_profile(identity, payload):
    user = _get_user_by_identity(identity)
    if not user:
        return None, None, None

    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id, primary_email=user.email)
        db.session.add(profile)

    if "username" in payload:
        username = payload.get("username")
        if username:
            with db.session.no_autoflush:
                existing = UserProfile.query.filter(
                    UserProfile.username == username,
                    UserProfile.user_id != user.id,
                ).first()
            if existing:
                return user, profile, _error(409, "Conflict", "Username already taken.")
        profile.username = username

    if "mobile_number" in payload:
        profile.mobile_number = payload.get("mobile_number")
    if "profile_pic_url" in payload:
        profile.profile_pic_url = payload.get("profile_pic_url")
    if "profile_pic_public_id" in payload:
        profile.profile_pic_public_id = payload.get("profile_pic_public_id")
    if "profile_pic_folder" in payload:
        profile.profile_pic_folder = payload.get("profile_pic_folder") or UserProfile.PROFILE_PIC_FOLDER
    if "bio" in payload:
        profile.bio = payload.get("bio")
    if "date_of_birth" in payload:
        profile.date_of_birth = payload.get("date_of_birth")
    if "city" in payload:
        profile.city = payload.get("city")
    if "state" in payload:
        profile.state = payload.get("state")
    if "country" in payload:
        profile.country = payload.get("country")

    profile.primary_email = user.email

    db.session.commit()
    return user, profile, None


def update_user(identity, payload):
    user = _get_user_by_identity(identity)
    if not user:
        return None, None

    if payload.get("email"):
        user.email = payload["email"]
    if payload.get("password"):
        user.set_password(payload["password"])

    db.session.commit()
    role = _role_for_user(user)
    return user, role


def delete_user(identity):
    user = _get_user_by_identity(identity)
    if not user:
        return None
    db.session.delete(user)
    db.session.commit()
    return user


# High-level handlers for routes

def users_health_service():
    # Service: Return static health payload for the users module.
    return {
        "status_code": 200,
        "message": "Users service healthy",
        "data": serialize_users_health(),
    }, None


def register_user_service(payload):
    # Service: Validate and register a new user account.
    payload, errors = validate_registration_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    if RegistrationUser.query.filter_by(email=payload["email"]).first():
        return None, _error(409, "Conflict", "Email already registered.")

    result = register_user(payload)
    user = result["user"]
    role = result["role"]
    token = result["token"]

    return {
        "status_code": 201,
        "message": f"Account created for {user.email} with role {role}.",
        "data": serialize_registration_response(user, role, token),
    }, None


def login_user_service(payload):
    # Service: Validate login and issue a JWT for the user.
    payload, errors = validate_login_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    user, result = login_user(payload)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid email or password.")

    return {
        "status_code": 200,
        "message": "Login successful",
        "data": serialize_login_response(user, result["role"], result["token"]),
    }, None


def me_service(identity):
    # Service: Fetch basic profile data for the logged-in user.
    user, role = get_user_profile(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "Profile fetched",
        "data": serialize_me_response(user, role),
    }, None


def profile_service(identity):
    # Service: Fetch full user profile details for the logged-in user.
    user, profile = get_user_profile_details(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "User profile fetched",
        "data": serialize_user_profile(user, profile),
    }, None


def update_me_service(identity, payload):
    # Service: Update logged-in user's account fields (email/password).
    payload, errors = validate_update_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    user, role = update_user(identity, payload)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "Account updated",
        "data": serialize_update_response(user, role),
    }, None


def update_profile_service(identity, payload):
    payload, errors = validate_update_profile_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    user, profile, err = update_user_profile(identity, payload)
    if err:
        return None, err
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "User profile updated",
        "data": serialize_user_profile(user, profile),
    }, None


def upload_profile_picture_service(identity, file, folder):
    if not file:
        return None, _error(400, "Validation Error", "Profile picture file is required.")

    if not (os.getenv("CLOUDINARY_URL") or cloudinary.config().cloud_name):
        return None, _error(500, "Configuration Error", "Cloudinary is not configured.")

    user = _get_user_by_identity(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id, primary_email=user.email)
        db.session.add(profile)

    target_folder = folder or profile.profile_pic_folder or UserProfile.PROFILE_PIC_FOLDER
    old_public_id = profile.profile_pic_public_id
    compressed_file, compression_error = compress_image_to_100kb(file)
    if compression_error:
        return None, _error(400, "Validation Error", compression_error)

    try:
        upload_result = cloudinary.uploader.upload(
            compressed_file,
            folder=target_folder,
            resource_type="image",
        )
    except Exception:
        return None, _error(502, "Upload Error", "Failed to upload profile picture.")

    profile.profile_pic_url = upload_result.get("secure_url") or upload_result.get("url")
    profile.profile_pic_public_id = upload_result.get("public_id")
    profile.profile_pic_folder = target_folder
    profile.primary_email = user.email

    db.session.commit()

    if old_public_id and old_public_id != profile.profile_pic_public_id:
        try:
            cloudinary.uploader.destroy(old_public_id, resource_type="image")
        except Exception:
            pass

    return {
        "status_code": 200,
        "message": "Profile picture uploaded",
        "data": serialize_user_profile(user, profile),
    }, None


def remove_profile_picture_service(identity):
    user = _get_user_by_identity(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile or not profile.profile_pic_public_id:
        return {
            "status_code": 200,
            "message": "Profile picture removed",
            "data": serialize_user_profile(user, profile),
        }, None

    old_public_id = profile.profile_pic_public_id
    profile.profile_pic_url = None
    profile.profile_pic_public_id = None
    profile.profile_pic_folder = UserProfile.PROFILE_PIC_FOLDER
    profile.primary_email = user.email

    db.session.commit()

    try:
        cloudinary.uploader.destroy(old_public_id, resource_type="image")
    except Exception:
        pass

    return {
        "status_code": 200,
        "message": "Profile picture removed",
        "data": serialize_user_profile(user, profile),
    }, None


def delete_me_service(identity):
    # Service: Delete the logged-in user's account.
    user = delete_user(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    return {
        "status_code": 200,
        "message": "Logged out and account deleted permanently.",
        "data": serialize_delete_response(user),
    }, None


def logout_service(identity, jwt_payload):
    # Service: Revoke the current JWT so it cannot be used again.
    user = _get_user_by_identity(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    jti = (jwt_payload or {}).get("jti")
    if not jti:
        return None, _error(401, "Unauthorized", "Invalid token.")

    existing = RevokedToken.query.filter_by(jti=jti).first()
    if not existing:
        db.session.add(RevokedToken(jti=jti, user_id=user.id))
        db.session.commit()

    return {
        "status_code": 200,
        "message": "Logout successful",
        "data": serialize_logout_response(),
    }, None


def list_buildings_service():
    # Service: List all buildings with tower/flat counts and amenities.
    buildings = (
        Building.query.options(
            selectinload(Building.towers).selectinload(Tower.flats),
            selectinload(Building.amenities),
        )
        .order_by(Building.id.desc())
        .all()
    )

    return {
        "status_code": 200,
        "message": "Buildings fetched",
        "data": [serialize_building_with_stats(building) for building in buildings],
    }, None


def get_building_detail_service(building_id):
    # Service: Fetch a single building with towers and amenities.
    building = (
        Building.query.options(
            selectinload(Building.towers).selectinload(Tower.flats),
            selectinload(Building.amenities),
        )
        .filter_by(id=building_id)
        .first()
    )
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    return {
        "status_code": 200,
        "message": "Building fetched",
        "data": serialize_building_detail(building),
    }, None


def get_building_amenities_service(building_id):
    # Service: Fetch all amenities for a single building.
    building = (
        Building.query.options(
            selectinload(Building.amenities),
        )
        .filter_by(id=building_id)
        .first()
    )
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    return {
        "status_code": 200,
        "message": "Building amenities fetched",
        "data": {
            "building": {"name": building.name},
            "amenities": [serialize_amenity_summary(amenity) for amenity in (building.amenities or [])],
        },
    }, None


def get_building_amenity_service(building_id, amenity_id):
    # Service: Fetch a single amenity for a building.
    building = Building.query.filter_by(id=building_id).first()
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    amenity = Amenity.query.filter_by(id=amenity_id, building_id=building_id).first()
    if not amenity:
        return None, _error(404, "Not Found", "Amenity not found for this building.")

    return {
        "status_code": 200,
        "message": "Building amenity fetched",
        "data": {
            "building": {"name": building.name},
            "amenity": serialize_amenity_summary(amenity),
        },
    }, None


def get_tower_detail_service(building_id, tower_id):
    # Service: Fetch a tower by building with flat counts and building address.
    building = (
        Building.query.options(
            selectinload(Building.towers).selectinload(Tower.flats),
        )
        .filter_by(id=building_id)
        .first()
    )
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    tower = next((t for t in (building.towers or []) if t.id == tower_id), None)
    if not tower:
        return None, _error(404, "Not Found", "Tower not found for this building.")

    return {
        "status_code": 200,
        "message": "Tower fetched",
        "data": serialize_tower_detail_with_building(tower, building),
    }, None


def list_tower_flats_service(building_id, tower_id, status, page):
    # Service: List flats for a tower with status filter and pagination.
    try:
        page = int(page or 1)
    except (TypeError, ValueError):
        return None, _error(400, "Validation Error", "page must be an integer.")

    if page < 1:
        return None, _error(400, "Validation Error", "page must be >= 1.")

    if status not in (None, "", "all", "available", "true", "false"):
        return None, _error(400, "Validation Error", "status must be 'all', 'available', 'true', or 'false'.")

    building = Building.query.filter_by(id=building_id).first()
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    tower = Tower.query.filter_by(id=tower_id, building_id=building_id).first()
    if not tower:
        return None, _error(404, "Not Found", "Tower not found for this building.")

    per_page = 10
    query = Flat.query.filter_by(tower_id=tower_id)
    if status in ("available", "true"):
        query = query.filter_by(is_available=True)
    elif status == "false":
        query = query.filter_by(is_available=False)

    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(Flat.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "status_code": 200,
        "message": "Flats fetched",
        "data": serialize_flats_response(items, tower, building, page, per_page, total, total_pages),
    }, None


def search_flats_service(args):
    # Service: Search flats across buildings by address, city, state, flat type, and rent range.
    params, errors = validate_flat_search_params(args)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    page = params["page"]
    per_page = params["per_page"]

    base_query = (
        db.session.query(Flat, Tower, Building)
        .join(Tower, Flat.tower_id == Tower.id)
        .join(Building, Tower.building_id == Building.id)
    )

    if params["city"]:
        base_query = base_query.filter(Building.city.ilike(f"%{params['city']}%"))
    if params["state"]:
        base_query = base_query.filter(Building.state.ilike(f"%{params['state']}%"))
    if params["flat_type"]:
        base_query = base_query.filter(Flat.bhk_type.ilike(f"%{params['flat_type']}%"))

    if params["min_rent"] is not None:
        base_query = base_query.filter(Flat.rent_amount >= params["min_rent"])
    if params["max_rent"] is not None:
        base_query = base_query.filter(Flat.rent_amount <= params["max_rent"])

    if params["address"]:
        rank, include_filter = _address_rank_and_filter(params["address"])
        rank_score = rank.label("rank_score")
        ranked_base_query = base_query.add_columns(rank_score).filter(include_filter)

        all_count = ranked_base_query.order_by(None).count()
        available_count = ranked_base_query.filter(Flat.is_available.is_(True)).order_by(None).count()
        unavailable_count = ranked_base_query.filter(Flat.is_available.is_(False)).order_by(None).count()

        selected_query = ranked_base_query
        if params["status"] == "available":
            selected_query = selected_query.filter(Flat.is_available.is_(True))
        elif params["status"] == "unavailable":
            selected_query = selected_query.filter(Flat.is_available.is_(False))

        total = selected_query.order_by(None).count()
        total_pages = (total + per_page - 1) // per_page if total else 0
        raw_rows = (
            selected_query
            .order_by(rank_score.desc(), Flat.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        paged_rows = [(flat, tower, building) for flat, tower, building, _ in raw_rows]
    else:
        all_count = base_query.count()
        available_count = base_query.filter(Flat.is_available.is_(True)).count()
        unavailable_count = base_query.filter(Flat.is_available.is_(False)).count()

        query = base_query
        if params["status"] == "available":
            query = query.filter(Flat.is_available.is_(True))
        elif params["status"] == "unavailable":
            query = query.filter(Flat.is_available.is_(False))

        total = query.count()
        total_pages = (total + per_page - 1) // per_page
        paged_rows = (
            query.order_by(Flat.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

    response_data = serialize_flat_search_response(paged_rows, page, per_page, total, total_pages)
    response_data["status_counts"] = {
        "all": all_count,
        "available": available_count,
        "unavailable": unavailable_count,
    }

    return {
        "status_code": 200,
        "message": "Flat search results fetched",
        "data": response_data,
    }, None


def search_buildings_service(args):
    # Service: Search buildings by name/address/city/state with pagination.
    params, errors = validate_building_search_params(args)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    page = params["page"]
    per_page = params["per_page"]

    base_query = Building.query
    if params["name"]:
        base_query = base_query.filter(Building.name.ilike(f"%{params['name']}%"))
    if params["city"]:
        base_query = base_query.filter(Building.city.ilike(f"%{params['city']}%"))
    if params["state"]:
        base_query = base_query.filter(Building.state.ilike(f"%{params['state']}%"))

    if params["address"]:
        rank, include_filter = _address_rank_and_filter(params["address"], include_name=True)
        rank_score = rank.label("rank_score")
        ranked_query = base_query.add_columns(rank_score).filter(include_filter)
        total = ranked_query.order_by(None).count()
        total_pages = (total + per_page - 1) // per_page if total else 0
        rows = (
            ranked_query.options(
                selectinload(Building.towers).selectinload(Tower.flats),
                selectinload(Building.amenities),
            )
            .order_by(rank_score.desc(), Building.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        page_buildings = [building for building, _ in rows]
    else:
        total = base_query.count()
        total_pages = (total + per_page - 1) // per_page
        page_buildings = (
            base_query.options(
                selectinload(Building.towers).selectinload(Tower.flats),
                selectinload(Building.amenities),
            )
            .order_by(Building.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

    return {
        "status_code": 200,
        "message": "Building search results fetched",
        "data": serialize_building_search_response(page_buildings, page, per_page, total, total_pages),
    }, None


def get_flat_detail_service(building_id, tower_id, flat_id):
    # Service: Fetch a single flat with tower, building, and amenities info.
    building = Building.query.filter_by(id=building_id).first()
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    tower = Tower.query.filter_by(id=tower_id, building_id=building_id).first()
    if not tower:
        return None, _error(404, "Not Found", "Tower not found for this building.")

    flat = Flat.query.filter_by(id=flat_id, tower_id=tower_id).first()
    if not flat:
        return None, _error(404, "Not Found", "Flat not found for this tower.")

    admin_user = RegistrationUser.query.filter_by(id=building.admin_id).first()
    admin_profile = UserProfile.query.filter_by(user_id=building.admin_id).first()

    return {
        "status_code": 200,
        "message": "Flat fetched",
        "data": serialize_flat_detail(flat, tower, building, admin_user, admin_profile),
    }, None


def list_user_flat_pictures_service(building_id, tower_id, flat_id):
    building = Building.query.filter_by(id=building_id).first()
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    tower = Tower.query.filter_by(id=tower_id, building_id=building_id).first()
    if not tower:
        return None, _error(404, "Not Found", "Tower not found for this building.")

    flat = Flat.query.filter_by(id=flat_id, tower_id=tower_id).first()
    if not flat:
        return None, _error(404, "Not Found", "Flat not found for this tower.")

    pictures = FlatPicture.query.filter_by(flat_id=flat.id).order_by(FlatPicture.id.asc()).all()

    return {
        "status_code": 200,
        "message": "Flat pictures fetched",
        "data": [serialize_flat_picture(picture) for picture in pictures],
    }, None


def list_building_towers_service(building_id):
    # Service: List towers for a building with flat counts.
    building = (
        Building.query.options(
            selectinload(Building.towers).selectinload(Tower.flats),
        )
        .filter_by(id=building_id)
        .first()
    )
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    towers = building.towers or []
    return {
        "status_code": 200,
        "message": "Towers fetched",
        "data": [serialize_tower_summary(tower) for tower in towers],
    }, None


def list_building_flats_service(building_id, status, page, per_page):
    # Service: List all flats in a building with optional status filter and pagination.
    try:
        page = int(page or 1)
    except (TypeError, ValueError):
        return None, _error(400, "Validation Error", "page must be an integer.")

    try:
        per_page = int(per_page or 20)
    except (TypeError, ValueError):
        return None, _error(400, "Validation Error", "per_page must be an integer.")

    if page < 1:
        return None, _error(400, "Validation Error", "page must be >= 1.")
    if per_page < 1 or per_page > 100:
        return None, _error(400, "Validation Error", "per_page must be between 1 and 100.")

    if status not in (None, "", "all", "available", "true", "false", "unavailable"):
        return None, _error(
            400,
            "Validation Error",
            "status must be 'all', 'available', 'unavailable', 'true', or 'false'.",
        )

    building = Building.query.filter_by(id=building_id).first()
    if not building:
        return None, _error(404, "Not Found", "Building not found.")

    query = (
        db.session.query(Flat, Tower, Building)
        .join(Tower, Flat.tower_id == Tower.id)
        .join(Building, Tower.building_id == Building.id)
        .filter(Building.id == building_id)
    )

    if status in ("available", "true"):
        query = query.filter(Flat.is_available.is_(True))
    elif status in ("unavailable", "false"):
        query = query.filter(Flat.is_available.is_(False))

    total = query.order_by(None).count()
    total_pages = (total + per_page - 1) // per_page if total else 0
    rows = (
        query.order_by(Tower.id.asc(), Flat.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "status_code": 200,
        "message": "Building flats fetched",
        "data": serialize_flat_search_response(rows, page, per_page, total, total_pages),
    }, None


def list_all_flats_service(page, per_page, status):
    # Service: List all flats across all buildings with essential display details.
    try:
        page = int(page or 1)
    except (TypeError, ValueError):
        return None, _error(400, "Validation Error", "page must be an integer.")

    try:
        per_page = int(per_page or 9)
    except (TypeError, ValueError):
        return None, _error(400, "Validation Error", "per_page must be an integer.")

    if page < 1:
        return None, _error(400, "Validation Error", "page must be >= 1.")
    if per_page < 1 or per_page > 100:
        return None, _error(400, "Validation Error", "per_page must be between 1 and 100.")

    normalized_status = (status or "").strip().lower()
    if normalized_status not in ("", "all", "available", "unavailable", "true", "false"):
        return None, _error(
            400,
            "Validation Error",
            "status must be 'all', 'available', 'unavailable', 'true', or 'false'.",
        )

    base_query = (
        db.session.query(Flat, Building)
        .join(Tower, Flat.tower_id == Tower.id)
        .join(Building, Tower.building_id == Building.id)
    )
    all_count = base_query.order_by(None).count()
    available_count = base_query.filter(Flat.is_available.is_(True)).order_by(None).count()
    unavailable_count = base_query.filter(Flat.is_available.is_(False)).order_by(None).count()

    query = base_query
    if normalized_status in ("available", "true"):
        query = query.filter(Flat.is_available.is_(True))
    elif normalized_status in ("unavailable", "false"):
        query = query.filter(Flat.is_available.is_(False))

    total = query.order_by(None).count()
    total_pages = (total + per_page - 1) // per_page if total else 0
    rows = (
        query.order_by(Flat.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "status_code": 200,
        "message": "All flats fetched",
        "data": {
            "items": [serialize_public_flat_listing(flat, building) for flat, building in rows],
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "status_counts": {
                "all": all_count,
                "available": available_count,
                "unavailable": unavailable_count,
            },
        },
    }, None


def create_security_deposit_booking_service(identity, flat_id):
    # Service: Create a booking by paying security deposit for a flat.
    user = _get_user_by_identity(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    flat = Flat.query.get(flat_id)
    if not flat:
        return None, _error(404, "Not Found", "Flat not found.")

    tower = Tower.query.get(flat.tower_id) if flat.tower_id else None
    building = Building.query.get(tower.building_id) if tower else None
    if not tower or not building:
        return None, _error(404, "Not Found", "Building or tower not found for this flat.")

    existing_booking = Booking.query.filter_by(user_id=user.id, flat_id=flat.id).first()
    if existing_booking:
        return None, _error(409, "Conflict", "You have already booked this flat.")

    profile = UserProfile.query.filter_by(user_id=user.id).first()
    user_name = profile.username if profile and profile.username else None

    full_address = ", ".join(
        part for part in [building.address, building.city, building.state, building.pincode] if part
    )

    booking = Booking(
        user_id=user.id,
        flat_id=flat.id,
        tower_id=tower.id,
        building_id=building.id,
        status="PENDING",
        security_deposit=flat.security_deposit,
        paid=True,
        building_full_address=full_address,
        user_name=user_name,
    )

    db.session.add(booking)
    db.session.commit()

    return {
        "status_code": 201,
        "message": "Security deposit paid and booking created",
        "data": serialize_booking(booking),
    }, None


def list_user_bookings_service(identity):
    # Service: List all bookings for the logged-in user.
    user = _get_user_by_identity(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    rows = (
        db.session.query(Booking, Building, Tower, Flat, RegistrationUser, UserProfile)
        .join(Building, Booking.building_id == Building.id)
        .join(Tower, Booking.tower_id == Tower.id)
        .join(Flat, Booking.flat_id == Flat.id)
        .join(RegistrationUser, Building.admin_id == RegistrationUser.id)
        .outerjoin(UserProfile, UserProfile.user_id == RegistrationUser.id)
        .filter(Booking.user_id == user.id)
        .order_by(Booking.id.desc())
        .all()
    )

    data = []
    for booking, building, tower, flat, manager_user, manager_profile in rows:
        data.append(
            {
                **serialize_booking(booking),
                "building": {"name": building.name},
                "tower": {"name": tower.name},
                "flat": {"flat_number": flat.flat_number},
                "manager": _serialize_manager(manager_user, manager_profile),
            }
        )

    return {
        "status_code": 200,
        "message": "Bookings fetched",
        "data": data,
    }, None


def get_user_booking_service(identity, booking_id):
    # Service: Fetch a single booking for the logged-in user.
    user = _get_user_by_identity(identity)
    if not user:
        return None, _error(401, "Unauthorized", "Invalid token.")

    row = (
        db.session.query(Booking, Building, Tower, Flat, RegistrationUser, UserProfile)
        .join(Building, Booking.building_id == Building.id)
        .join(Tower, Booking.tower_id == Tower.id)
        .join(Flat, Booking.flat_id == Flat.id)
        .join(RegistrationUser, Building.admin_id == RegistrationUser.id)
        .outerjoin(UserProfile, UserProfile.user_id == RegistrationUser.id)
        .filter(Booking.user_id == user.id, Booking.id == booking_id)
        .first()
    )

    if not row:
        return None, _error(404, "Not Found", "Booking not found.")

    booking, building, tower, flat, manager_user, manager_profile = row
    data = {
        **serialize_booking(booking),
        "building": {"name": building.name},
        "tower": {"name": tower.name},
        "flat": {"flat_number": flat.flat_number},
        "manager": _serialize_manager(manager_user, manager_profile),
    }

    return {
        "status_code": 200,
        "message": "Booking fetched",
        "data": data,
    }, None
