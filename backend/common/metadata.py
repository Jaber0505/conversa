from rest_framework.metadata import SimpleMetadata

class HateoasMetadata(SimpleMetadata):
    """
    Étend SimpleMetadata pour exposer les infos utiles
    aux frontends (types, required, help_text).
    """
    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)
        # Exemple : on peut ajouter des actions métiers
        if hasattr(view, "extra_hateoas"):
            metadata["actions"].update(view.extra_hateoas)
        return metadata
