from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class AppError(Exception):
    """Domain error with an HTTP status and machine-readable code."""

    def __init__(self, message: str, code: str = "error", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def custom_exception_handler(exc, context):
    if isinstance(exc, AppError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=exc.status_code,
        )
    response = exception_handler(exc, context)
    if response is not None:
        return response
    return Response(
        {"error": {"code": "internal_error", "message": str(exc)}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
