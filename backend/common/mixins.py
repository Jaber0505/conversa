from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

class HateoasOptionsMixin:
    """
    Automatically provides an enriched OPTIONS response
    with the list of available actions (POST fields, etc.)
    """
    def options(self, request, *args, **kwargs):
        metadata = self.metadata_class()
        data = metadata.determine_metadata(request, self)
        return Response(data, status=status.HTTP_200_OK)
