from flask import jsonify


def success_response(status_code=200, message="OK", data=None, add_size=False):
    payload = {
        "status_code": status_code,
        "data": data,
    }
    return jsonify(payload), status_code


def error_response(status_code=400, message="Error", user_message="Something went wrong.", add_size=False):
    error_message = user_message or message
    payload = {
        "status_code": status_code,
        "error": error_message,
    }
    return jsonify(payload), status_code
