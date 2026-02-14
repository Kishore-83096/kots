from flask import request


FRONTEND_ASSET_EXTENSIONS = (
    ".js",
    ".css",
    ".mjs",
    ".map",
    ".woff2",
    ".woff",
    ".ttf",
    ".eot",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
)

API_PATH_PREFIXES = ("/users", "/admins", "/master")
API_EXACT_PATHS = {"/", "/health"}


def _is_api_request_path(path):
    if path in API_EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in API_PATH_PREFIXES)


def apply_frontend_asset_cache_headers(response):
    if request.method != "GET":
        return response

    if response.status_code != 200:
        return response

    path = request.path.lower()
    if _is_api_request_path(path):
        return response

    # Keep app shell revalidated so deploys are picked up quickly.
    if path.endswith("/index.html") or path == "/index.html":
        response.headers["Cache-Control"] = "no-cache"
        response.add_etag()
        response.make_conditional(request)
        return response

    # Long cache for versioned/static assets.
    if path.endswith(FRONTEND_ASSET_EXTENSIONS):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        response.add_etag()
        response.make_conditional(request)
        return response

    # SPA route fallback (HTML served at non-file path).
    if response.mimetype == "text/html":
        response.headers["Cache-Control"] = "no-cache"
        response.add_etag()
        response.make_conditional(request)

    return response
