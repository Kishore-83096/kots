from admins.schemas_admins import serialize_admins_health, serialize_admins_dashboard


def admins_health_service():
    return {
        "status_code": 200,
        "message": "Admins service healthy",
        "data": serialize_admins_health(),
    }, None


def admins_dashboard_service():
    return {
        "status_code": 200,
        "message": "Admins dashboard",
        "data": serialize_admins_dashboard(),
    }, None
