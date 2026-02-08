from extensions import db
from users.models_users import RegistrationUser
from master.schemas_master import (
    validate_admin_create_payload,
    validate_pagination_params,
    serialize_master_health,
    serialize_master_control,
    serialize_admin_created,
    serialize_admins_list,
)


def _error(status_code, message, user_message):
    return {
        "status_code": status_code,
        "message": message,
        "user_message": user_message,
    }


def create_admin_user(payload):
    if RegistrationUser.query.filter_by(email=payload["email"]).first():
        return None, "Email already registered."

    user = RegistrationUser(
        email=payload["email"],
        is_admin=True,
        is_master=False,
    )
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()
    return user, None


def list_admins(exclude_user_id, page, per_page):
    query = RegistrationUser.query.filter_by(is_admin=True)
    if exclude_user_id:
        query = query.filter(RegistrationUser.id != exclude_user_id)

    pagination = query.order_by(RegistrationUser.id.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    items = [
        {
            "id": user.id,
            "email": user.email,
            "role": "master" if user.is_master else "admin",
            "created_at": user.created_at.isoformat(),
        }
        for user in pagination.items
    ]

    return {
        "items": items,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


# High-level handlers for routes

def master_health_service():
    return {
        "status_code": 200,
        "message": "Master service healthy",
        "data": serialize_master_health(),
    }, None


def master_control_service():
    return {
        "status_code": 200,
        "message": "Master control panel",
        "data": serialize_master_control(),
    }, None


def master_create_admin_service(payload):
    payload, errors = validate_admin_create_payload(payload)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    user, err = create_admin_user(payload)
    if err:
        return None, _error(409, "Conflict", err)

    return {
        "status_code": 201,
        "message": f"Admin account created for {user.email}.",
        "data": serialize_admin_created(user),
    }, None


def master_list_admins_service(args, identity):
    params, errors = validate_pagination_params(args)
    if errors:
        return None, _error(400, "Validation Error", " ".join(errors))

    data = list_admins(
        exclude_user_id=int(identity),
        page=params["page"],
        per_page=params["per_page"],
    )
    return {
        "status_code": 200,
        "message": "Admins fetched",
        "data": serialize_admins_list(data),
    }, None
