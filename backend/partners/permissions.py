"""Partner-specific permissions."""
from rest_framework import permissions


class IsPartnerOwnerOnly(permissions.BasePermission):
    """
    Permission class EXCLUSIVELY for partner owners.

    Business Rules:
        - User must own a partner (hasattr(user, 'owned_partner'))
        - ONLY the owner can access - even admins are blocked
        - Used for dedicated partner owner endpoints
    """

    def has_permission(self, request, view):
        """
        Check if user owns a partner.

        Args:
            request: HTTP request
            view: API view

        Returns:
            bool: True if user owns a partner
        """
        return hasattr(request.user, 'owned_partner')
