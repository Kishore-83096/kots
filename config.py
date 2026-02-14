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
    ADDRESS_MATCH_STRONG_RATIO = float(os.getenv("ADDRESS_MATCH_STRONG_RATIO", "0.8"))
    ADDRESS_MATCH_MEDIUM_RATIO = float(os.getenv("ADDRESS_MATCH_MEDIUM_RATIO", "0.5"))
    ADDRESS_SCORE_EXACT = float(os.getenv("ADDRESS_SCORE_EXACT", "100"))
    ADDRESS_SCORE_STRONG_PARTIAL = float(os.getenv("ADDRESS_SCORE_STRONG_PARTIAL", "80"))
    ADDRESS_SCORE_MEDIUM_PARTIAL = float(os.getenv("ADDRESS_SCORE_MEDIUM_PARTIAL", "55"))
    ADDRESS_SCORE_WEAK_PARTIAL = float(os.getenv("ADDRESS_SCORE_WEAK_PARTIAL", "30"))
    ADDRESS_SCORE_MIN_INCLUDE = float(os.getenv("ADDRESS_SCORE_MIN_INCLUDE", "1"))
