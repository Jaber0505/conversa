# backend/audit/models.py
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    method      = models.CharField(max_length=8)
    path        = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField()
    ip          = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.CharField(max_length=255, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["path"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.method} {self.path} {self.status_code}"
