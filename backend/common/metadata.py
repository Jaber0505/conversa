"""
HATEOAS metadata for DRF API.

Extends SimpleMetadata to provide hypermedia links and enhanced
metadata for better API discoverability.
"""

from rest_framework.metadata import SimpleMetadata


class HateoasMetadata(SimpleMetadata):
    """
    Extends SimpleMetadata to expose enhanced information for frontends.

    Adds HATEOAS (Hypermedia As The Engine Of Application State) links
    to OPTIONS responses, allowing clients to discover related resources
    and available actions dynamically.

    Features:
    - Includes field types, required flags, and help text
    - Adds custom "extra_hateoas" links from views
    - Provides machine-readable API schema

    Usage:
        class EventViewSet(viewsets.ModelViewSet):
            metadata_class = HateoasMetadata

            extra_hateoas = {
                "bookings": "/api/v1/bookings/",
                "payments": "/api/v1/payments/",
            }

    Example OPTIONS response:
        {
          "name": "Event List",
          "actions": {
            "POST": {
              "theme": { "type": "string", "required": true },
              ...
            }
          },
          "related": {
            "bookings": "/api/v1/bookings/",
            "payments": "/api/v1/payments/"
          }
        }
    """
    def determine_metadata(self, request, view):
        """
        Add custom HATEOAS links to standard metadata.

        Args:
            request: HTTP request
            view: DRF view instance

        Returns:
            dict: Enhanced metadata with HATEOAS links
        """
        metadata = super().determine_metadata(request, view)

        # Add related resource links (HATEOAS) if view provides them
        # These go in a separate "related" section, not in "actions"
        if hasattr(view, "extra_hateoas"):
            metadata["related"] = view.extra_hateoas

        return metadata
