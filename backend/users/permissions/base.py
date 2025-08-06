from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSelf(BasePermission):
    """
    Autorise uniquement l’utilisateur à accéder ou modifier ses propres données.
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsSelfOrReadOnly(BasePermission):
    """
    Lecture publique, mais modification uniquement par le propriétaire.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user


class IsAdminOrReadOnly(BasePermission):
    """
    Seuls les administrateurs peuvent modifier. Tout le monde peut lire.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsAuthenticatedAndActive(BasePermission):
    """
    Autorise uniquement les utilisateurs authentifiés **et actifs** (is_active=True).
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)