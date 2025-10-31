"""
Custom DRF permissions for Conversa API.

Provides granular access control for API endpoints beyond DRF's built-in permissions.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedAndActive(BasePermission):
    """
    Allow only authenticated and active users.

    Extends DRF's IsAuthenticated to also check the is_active flag.
    Inactive users (is_active=False) are denied access even if authenticated.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticatedAndActive]
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "is_active", False))


class IsAdminUser(BasePermission):
    """
    Allow only admin/staff users (is_staff=True or is_superuser=True).

    Grants access to users with elevated privileges. Useful for admin-only
    endpoints like audit logs, partner management, etc.

    Usage:
        class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
            permission_classes = [IsAdminUser]
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and
            u.is_authenticated and
            (getattr(u, "is_staff", False) or getattr(u, "is_superuser", False))
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Read access for all, write access only for the owner.

    Checks obj.<owner_field> against request.user. The owner_field can be
    customized per-view by setting view.owner_field.

    Default owner_field: "organizer"

    Usage:
        class EventViewSet(viewsets.ModelViewSet):
            permission_classes = [IsOwnerOrReadOnly]
            owner_field = "organizer"  # Optional override
    """
    owner_field = "organizer"  # Default owner field name

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any request (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True

        # Write permissions only for the owner
        owner = getattr(obj, getattr(view, "owner_field", self.owner_field), None)
        return bool(
            request.user and
            request.user.is_authenticated and
            owner and
            owner == request.user
        )


class IsOrganizerOrReadOnly(BasePermission):
    """
    Read access for all, write access only for the event organizer.

    Specifically designed for Event objects where the owner is called "organizer".
    Checks obj.organizer_id against request.user.id for efficiency.

    Usage:
        class EventViewSet(viewsets.ModelViewSet):
            permission_classes = [IsOrganizerOrReadOnly]
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any request
        if request.method in SAFE_METHODS:
            return True

        # Write permissions only for the organizer
        return getattr(obj, "organizer_id", None) == getattr(request.user, "id", None)


class IsOrganizerOrAdmin(BasePermission):
    """
    Read access for all, write access for organizer or admin staff.

    Allows both the event organizer and admin users (is_staff=True) to
    modify the object. Useful for event management where admins can intervene.

    Usage:
        class EventViewSet(viewsets.ModelViewSet):
            permission_classes = [IsOrganizerOrAdmin]
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any request
        if request.method in SAFE_METHODS:
            return True

        # Write permissions for staff/admins
        if getattr(request.user, "is_staff", False):
            return True

        # Write permissions for the organizer
        return request.user.id == obj.organizer_id  