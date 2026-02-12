import json
from flask import jsonify


def _format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes}b"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f}kb"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f}mb"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f}gb"


def _with_size(payload):
    size_payload = dict(payload)
    size_payload.pop("size", None)
    encoded = json.dumps(size_payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload["size"] = _format_size(len(encoded))
    return payload


def success_response(status_code=200, message="OK", data=None, add_size=False):
    payload = {
        "status_code": status_code,
        "success": True,
        "message": message,
        "data": data,
    }
    if add_size:
        payload = _with_size(payload)
    return jsonify(payload), status_code


def error_response(status_code=400, message="Error", user_message="Something went wrong.", add_size=False):
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
    if add_size:
        payload = _with_size(payload)
    return jsonify(payload), status_code
