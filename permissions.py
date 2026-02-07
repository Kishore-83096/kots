from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from response import error_response
from users.models_users import RegistrationUser


def role_required(*allowed_roles):
    allowed = {role.lower() for role in allowed_roles}

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = RegistrationUser.query.get(user_id)
            if not user:
                return error_response(status_code=401, message="Unauthorized", user_message="Invalid token.")

            if user.is_master:
                role = "master"
            elif user.is_admin:
                role = "admin"
            else:
                role = "user"

            if role not in allowed:
                return error_response(
                    status_code=403,
                    message="Forbidden",
                    user_message="You do not have permission to access this resource.",
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
