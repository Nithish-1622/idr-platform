import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """
    Standardized DRF Exception Handler.
    Ensures all error responses strictly follow the contract format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": {...}
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        code = getattr(exc, "default_code", "INVALID_REQUEST")
        if isinstance(code, str):
            code = code.upper()
        else:
            code = "INVALID_REQUEST"

        message = str(getattr(exc, "detail", exc))
        if isinstance(response.data, dict) and "detail" in response.data:
            message = str(response.data["detail"])

        details = {}
        if isinstance(response.data, dict):
            details = {k: v for k, v in response.data.items() if k != "detail"}
        elif isinstance(response.data, list):
            details = {"errors": response.data}

        formatted_response = {
            "error": {"code": code, "message": message, "details": details}
        }
        response.data = formatted_response
    else:
        # Unhandled server error
        logger.error(f"Unhandled Exception: {exc}", exc_info=True)
        response = Response(
            {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred.",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
