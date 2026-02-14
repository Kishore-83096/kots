from flask import current_app, request


IMAGE_URL_KEYS = {"picture_url", "profile_pic_url"}
MODULE_PREFIXES = ("/users", "/admins", "/master")


def _contains_image_urls(value):
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if (
                isinstance(key, str)
                and key in IMAGE_URL_KEYS
                and isinstance(nested_value, str)
                and nested_value.strip()
            ):
                return True
            if _contains_image_urls(nested_value):
                return True
        return False

    if isinstance(value, list):
        for item in value:
            if _contains_image_urls(item):
                return True
        return False

    return False


def apply_get_image_cache_headers(response):
    if request.method != "GET":
        return response

    if not any(request.path.startswith(prefix) for prefix in MODULE_PREFIXES):
        return response

    if response.status_code != 200 or not response.is_json:
        return response

    payload = response.get_json(silent=True)
    if not isinstance(payload, dict):
        return response

    if not _contains_image_urls(payload.get("data")):
        return response

    max_age = int(current_app.config.get("IMAGE_GET_CACHE_MAX_AGE", 300))
    stale_while_revalidate = int(
        current_app.config.get("IMAGE_GET_CACHE_STALE_WHILE_REVALIDATE", 120)
    )

    response.headers["Cache-Control"] = (
        f"private, max-age={max_age}, stale-while-revalidate={stale_while_revalidate}"
    )
    response.vary.add("Authorization")
    response.add_etag()
    response.make_conditional(request)
    return response
