# languages/views/language.py
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from languages.models import Language
from languages.serializers.language import LanguageSerializer, LanguageOptionSerializer

from users.permissions import IsAdminOrReadOnly

class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    
    queryset = Language.objects.all()
    lookup_field = "code"

    def get_serializer_class(self):
        if self.action == "list" and self.request and self.request.query_params.get("locale"):
            return LanguageOptionSerializer
        return LanguageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.query_params.get("q") or "").strip()
        is_active = self.request.query_params.get("is_active")
        if is_active in ("true", "false"):
            qs = qs.filter(is_active=(is_active == "true"))
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(names__icontains=q))
        return qs

    @action(detail=False, methods=["get"], url_path="dictionary")
    def dictionary(self, request):
        """
        Sans ?locale → { code: {fr,en,nl,...}, ... }
        Avec ?locale=fr → { code: "Libellé en fr", ... }
        """
        locale = (request.query_params.get("locale") or "").strip().lower()
        items = self.get_queryset().values("code", "names")
        if locale:
            data = {it["code"]: (it["names"].get(locale) or it["names"].get("fr") or it["code"]) for it in items}
        else:
            data = {it["code"]: it["names"] for it in items}
        return Response(data)
