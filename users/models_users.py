from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class RegistrationUser(db.Model):
    __tablename__ = "registration_users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_master = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    PROFILE_PIC_FOLDER = "kots/profile_pics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("registration_users.id"), unique=True, nullable=False)

    username = db.Column(db.String(80), unique=True, nullable=True)
    primary_email = db.Column(db.String(120), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=True)

    profile_pic_folder = db.Column(db.String(255), nullable=False, default=PROFILE_PIC_FOLDER)
    profile_pic_url = db.Column(db.String(512), nullable=True)
    profile_pic_public_id = db.Column(db.String(255), nullable=True)

    bio = db.Column(db.String(500), nullable=True)
    date_of_birth = db.Column(db.DateTime, nullable=True)

    city = db.Column(db.String(80), nullable=True)
    state = db.Column(db.String(80), nullable=True)
    country = db.Column(db.String(80), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("RegistrationUser", back_populates="profile")

    def set_primary_email_from_user(self):
        if self.user:
            self.primary_email = self.user.email


class RevokedToken(db.Model):
    __tablename__ = "revoked_tokens"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("registration_users.id"), nullable=True)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
