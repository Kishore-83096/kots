from flask import jsonify


def success_response(status_code=200, message="OK", data=None):
    payload = {
        "status_code": status_code,
        "success": True,
        "message": message,
        "data": data,
    }
    return jsonify(payload), status_code


def error_response(status_code=400, message="Error", user_message="Something went wrong."):
    payload = {
        "status_code": status_code,
        "success": False,
        "message": message,
        "error": {
            "detail": "Data is not available because of an error.",
            "user_message": user_message,
        },
        "data": None,
    }
    return jsonify(payload), status_code
