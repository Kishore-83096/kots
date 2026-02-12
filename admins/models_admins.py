from datetime import datetime
from extensions import db


class Building(db.Model):
    __tablename__ = "buildings"

    ASSET_PIC_FOLDER = "kots/assets"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("registration_users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    total_towers = db.Column(db.Integer, nullable=False, default=0)
    picture_url = db.Column(db.String(512), nullable=True)
    picture_public_id = db.Column(db.String(255), nullable=True)
    picture_folder = db.Column(db.String(255), nullable=False, default=ASSET_PIC_FOLDER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    towers = db.relationship("Tower", backref="building", lazy=True, cascade="all, delete-orphan")
    amenities = db.relationship("Amenity", backref="building", lazy=True, cascade="all, delete-orphan")


class Tower(db.Model):
    __tablename__ = "towers"

    ASSET_PIC_FOLDER = "kots/assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    floors = db.Column(db.Integer, nullable=False)
    total_flats = db.Column(db.Integer, nullable=False, default=0)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False)
    picture_url = db.Column(db.String(512), nullable=True)
    picture_public_id = db.Column(db.String(255), nullable=True)
    picture_folder = db.Column(db.String(255), nullable=False, default=ASSET_PIC_FOLDER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    flats = db.relationship("Flat", backref="tower", lazy=True, cascade="all, delete-orphan")


flat_amenities = db.Table(
    "flat_amenities",
    db.Column("flat_id", db.Integer, db.ForeignKey("flats.id"), primary_key=True),
    db.Column("amenity_id", db.Integer, db.ForeignKey("amenities.id"), primary_key=True),
)


class Flat(db.Model):
    __tablename__ = "flats"
    __table_args__ = (
        db.UniqueConstraint("tower_id", "flat_number", name="uq_tower_flat"),
    )

    ASSET_PIC_FOLDER = "kots/assets"

    id = db.Column(db.Integer, primary_key=True)
    flat_number = db.Column(db.String(20), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False)
    bhk_type = db.Column(db.String(10), nullable=False)
    area_sqft = db.Column(db.Integer, nullable=False)
    rent_amount = db.Column(db.Numeric(10, 2), nullable=False)
    security_deposit = db.Column(db.Numeric(10, 2), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    tower_id = db.Column(db.Integer, db.ForeignKey("towers.id"), nullable=False)
    picture_url = db.Column(db.String(512), nullable=True)
    picture_public_id = db.Column(db.String(255), nullable=True)
    picture_folder = db.Column(db.String(255), nullable=False, default=ASSET_PIC_FOLDER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    amenities = db.relationship(
        "Amenity",
        secondary=flat_amenities,
        backref=db.backref("flats", lazy="dynamic"),
    )
    bookings = db.relationship("Booking", backref="flat", lazy=True, cascade="all, delete-orphan")


class Amenity(db.Model):
    __tablename__ = "amenities"

    ASSET_PIC_FOLDER = "kots/assets"

    id = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    picture_url = db.Column(db.String(512), nullable=True)
    picture_public_id = db.Column(db.String(255), nullable=True)
    picture_folder = db.Column(db.String(255), nullable=False, default=ASSET_PIC_FOLDER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("registration_users.id"), nullable=False)
    flat_id = db.Column(db.Integer, db.ForeignKey("flats.id"), nullable=False)
    tower_id = db.Column(db.Integer, db.ForeignKey("towers.id"), nullable=True)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=True)
    status = db.Column(
        db.Enum("PENDING", "APPROVED", "DECLINED", name="booking_status"),
        nullable=False,
        default="PENDING",
    )
    security_deposit = db.Column(db.Numeric(10, 2), nullable=True)
    paid = db.Column(db.Boolean, default=False, nullable=False)
    building_full_address = db.Column(db.String(255), nullable=True)
    user_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
