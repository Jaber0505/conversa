from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedAndActive(BasePermission):
    """
    Autorise seulement les utilisateurs authentifiés et actifs.
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "is_active", False))

class IsOwnerOrReadOnly(BasePermission):
    """
    Lecture pour tous ; écriture réservée au propriétaire (attend obj.<owner_field>).
    """
    owner_field = "organizer"  # override possible sur la vue

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, getattr(view, "owner_field", self.owner_field), None)
        return bool(request.user and request.user.is_authenticated and owner and owner == request.user)

class IsOrganizerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "organizer_id", None) == getattr(request.user, "id", None)