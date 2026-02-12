from flask import Flask
import cloudinary
from flask_cors import CORS
from config import Config
from extensions import db, migrate, jwt
#from models import User
# Import models so Alembic sees them for migrations
from admins import models_admins  # noqa: F401
from users import models_users  # noqa: F401
from users.models_users import RevokedToken
from master.routes_master import master_bp
from admins.routes_admins import admins_bp
from users.routes_users import users_bp
from common.error_handlers import register_error_handlers
from common.response import success_response, error_response

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={r"/*": {"origins": app.config.get("ANGULAR_CORS_ORIGINS", [])}},
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    if app.config.get("CLOUDINARY_URL"):
        cloudinary.config(cloudinary_url=app.config["CLOUDINARY_URL"])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        if not jti:
            return True
        return RevokedToken.query.filter_by(jti=jti).first() is not None

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return error_response(
            status_code=401,
            message="Unauthorized",
            user_message="Token has been revoked. Please login again.",
            add_size=True,
        )

    app.register_blueprint(master_bp)
    app.register_blueprint(admins_bp)
    app.register_blueprint(users_bp)

    register_error_handlers(app)

    @app.route("/")
    def home():
        return success_response(message="Flask + Neon PostgreSQL connected")

    @app.route("/health")
    def health():
        return success_response(message="Service healthy", data={"service": "api"})

    return app

app = create_app()
