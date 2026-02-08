from flask import Flask
from config import Config
from extensions import db, migrate, jwt
#from models import User
# Import models so Alembic sees them for migrations
from admins import models_admins  # noqa: F401
from users import models_users  # noqa: F401
from master.routes_master import master_bp
from admins.routes_admins import admins_bp
from users.routes_users import users_bp
from common.error_handlers import register_error_handlers
from common.response import success_response

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

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
