import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _parse_cors_origins(value):
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]

class Config:
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=5)
    CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
    ANGULAR_CORS_ORIGINS = _parse_cors_origins(os.getenv("ANGULAR_CORS_ORIGINS", ""))
    IMAGE_GET_CACHE_MAX_AGE = int(os.getenv("IMAGE_GET_CACHE_MAX_AGE", "300"))
    IMAGE_GET_CACHE_STALE_WHILE_REVALIDATE = int(
        os.getenv("IMAGE_GET_CACHE_STALE_WHILE_REVALIDATE", "120")
    )
    ADDRESS_TRIGRAM_MIN_SIMILARITY = float(os.getenv("ADDRESS_TRIGRAM_MIN_SIMILARITY", "0.12"))
    ADDRESS_TRIGRAM_MIN_WORD_SIMILARITY = float(
        os.getenv("ADDRESS_TRIGRAM_MIN_WORD_SIMILARITY", "0.52")
    )
