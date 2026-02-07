from http import HTTPStatus
from werkzeug.exceptions import HTTPException
from response import error_response


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        status = err.code or HTTPStatus.INTERNAL_SERVER_ERROR
        return error_response(
            status_code=status,
            message=err.name,
            user_message=err.description or "Something went wrong.",
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err):
        return error_response(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            message="Internal Server Error",
            user_message="We couldn't process your request right now. Please try again later.",
        )
