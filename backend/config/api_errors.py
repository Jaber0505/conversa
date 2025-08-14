from typing import Any, Dict
import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.views import exception_handler as drf_default_handler
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("django.request")

def _normalize_errors(detail: Any) -> Any:
    """
    Transforme les erreurs DRF/Django en structure JSON simple.
    - dict/list -> inchangé (DRF ValidationError)
    - str -> {"non_field_errors": [str]}
    - autre -> stringifié
    """
    if isinstance(detail, dict) or isinstance(detail, list):
        return detail
    if isinstance(detail, str):
        return {"non_field_errors": [detail]}
    return {"non_field_errors": [str(detail)]}

def drf_exception_handler(exc, context) -> Response:
    """
    Enveloppe toutes les erreurs en JSON homogène:
    {
      "status": <HTTP status>,
      "code": "<slug court>",
      "message": "<résumé lisible>",
      "errors": {...}  # facultatif, surtout pour 400
    }
    """
    # Laisser DRF construire la réponse de base
    response = drf_default_handler(exc, context)

    # Cas courants non couverts par DRF (IntegrityError, DjangoValidationError)
    if response is None:
        if isinstance(exc, DjangoValidationError):
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "code": "validation_error",
                "message": "Les données envoyées sont invalides.",
                "errors": _normalize_errors(exc.message_dict if hasattr(exc, "message_dict") else exc.messages),
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(exc, IntegrityError):
            data = {
                "status": status.HTTP_409_CONFLICT,
                "code": "conflict",
                "message": "Conflit de données (contrainte d’unicité ou intégrité).",
            }
            return Response(data, status=status.HTTP_409_CONFLICT)
        # Fallback générique → 500
        logger.exception("Unhandled server error", exc_info=exc)
        return Response(
            {"status": 500, "code": "server_error", "message": "Erreur interne du serveur."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Post-traitement des réponses DRF pour un format homogène
    status_code = response.status_code
    detail = getattr(exc, "detail", None)

    # Déterminer un code/messsage simple selon le status
    if status_code == status.HTTP_400_BAD_REQUEST:
        code, message = "validation_error", "Les données envoyées sont invalides."
        errors = _normalize_errors(detail if isinstance(exc, DRFValidationError) else response.data)
        payload: Dict[str, Any] = {"status": status_code, "code": code, "message": message, "errors": errors}
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        payload = {"status": status_code, "code": "unauthorized", "message": "Authentification requise."}
    elif status_code == status.HTTP_403_FORBIDDEN:
        payload = {"status": status_code, "code": "forbidden", "message": "Accès refusé."}
    elif status_code == status.HTTP_404_NOT_FOUND:
        payload = {"status": status_code, "code": "not_found", "message": "Ressource introuvable."}
    elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        payload = {"status": status_code, "code": "method_not_allowed", "message": "Méthode non autorisée."}
    elif status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE:
        payload = {"status": status_code, "code": "unsupported_media_type", "message": "Type de contenu non supporté."}
    elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        payload = {"status": status_code, "code": "throttled", "message": "Trop de requêtes, réessaie plus tard."}
    else:
        # Laisser le message DRF mais dans notre enveloppe
        payload = {
            "status": status_code,
            "code": "error",
            "message": "Une erreur est survenue.",
        }

    response.data = payload
    return response
