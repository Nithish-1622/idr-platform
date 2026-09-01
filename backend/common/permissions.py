from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allows access only to users with ADMIN role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsEngineerRole(BasePermission):
    """Allows access to users with ENGINEER or ADMIN role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ["ADMIN", "ENGINEER"]
        )


class IsAnalystRole(BasePermission):
    """Allows read-only or analyst access."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ["ADMIN", "ENGINEER", "ANALYST"]
        )


class IsDeviceOrAuthenticated(BasePermission):
    """Allows registered devices or authenticated users to interact with endpoints."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
