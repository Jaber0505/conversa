"""
Standard pagination for all Conversa API endpoints.

Provides consistent pagination across all list endpoints using
page number pagination with configurable page size.
"""

from rest_framework.pagination import PageNumberPagination
from .constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class DefaultPagination(PageNumberPagination):
    """
    Default pagination class for all API list endpoints.

    Uses page number pagination (page=1, page=2, etc.) with configurable
    page size via query parameter.

    Configuration:
    - page_size: 20 (default items per page)
    - page_size_query_param: 'page_size' (allows client to customize)
    - max_page_size: 100 (prevents excessive page sizes)

    Usage:
        # Configured globally in settings.py:
        REST_FRAMEWORK = {
            "DEFAULT_PAGINATION_CLASS": "common.pagination.DefaultPagination",
        }

    Example requests:
        GET /api/v1/events/                  → page 1, 20 items
        GET /api/v1/events/?page=2           → page 2, 20 items
        GET /api/v1/events/?page_size=50     → page 1, 50 items
        GET /api/v1/events/?page=3&page_size=10  → page 3, 10 items

    Example response:
        {
          "count": 142,
          "next": "http://api.example.com/api/v1/events/?page=2",
          "previous": null,
          "results": [...]
        }
    """
    page_size = DEFAULT_PAGE_SIZE  # 20
    page_size_query_param = "page_size"
    max_page_size = MAX_PAGE_SIZE  # 100
