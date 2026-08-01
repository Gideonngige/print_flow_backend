# print_flow_app/permissions.py

from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    message = "Only administrators can access this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )