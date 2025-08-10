# config/openapi.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

class ProblemFieldSchema(serializers.Serializer):
    field = serializers.CharField()
    code = serializers.CharField()
    params = serializers.DictField(child=serializers.CharField(), required=False)

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="ValidationError",
            value={
                "type": "https://api.conversa.app/problems/validation-error",
                "title": "Validation Error",
                "status": 400,
                "detail": "Some fields are invalid.",
                "code": "VALIDATION_ERROR",
                "params": {},
                "fields": [
                    {"field": "email", "code": "invalid", "params": {}},
                    {"field": "password", "code": "min_length", "params": {"min": 8}},
                    {"field": "birth_date", "code": "AGE_MIN", "params": {}}
                ],
                "trace_id": "c4a9b6ed-1d03-4c4a-a6b0-1a8b89c5b0ad"
            },
        )
    ]
)
class ProblemSchema(serializers.Serializer):
    type = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    status = serializers.IntegerField()
    detail = serializers.CharField(required=False)
    code = serializers.CharField()
    params = serializers.DictField(required=False)
    fields = ProblemFieldSchema(many=True, required=False)
    trace_id = serializers.CharField()
