from rest_framework.permissions import BasePermission

class IsOrganizer(BasePermission):
    """
    Autorise uniquement les utilisateurs ayant le rôle d'organisateur.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_organizer)
