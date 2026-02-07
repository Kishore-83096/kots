from flask_jwt_extended import create_access_token
from uuid import uuid4
from extensions import db
from users.models_users import RegistrationUser



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
