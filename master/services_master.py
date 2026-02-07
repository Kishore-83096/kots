from extensions import db
from users.models_users import RegistrationUser


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
