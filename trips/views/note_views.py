"""
Views related to Notes on places in projects

Endpoints:

GET /api/notes/?place_id=... (optional list)
GET /api/notes/{note_id}/
PATCH /api/notes/{note_id}/ (update body)
DELETE /api/notes/{note_id}/ (optional)
"""

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import TravelProject, ProjectPlace, PlaceNote
from ..serializers import (
    TravelProjectSerializer,
    TravelProjectCreateSerializer,
    ProjectPlaceSerializer,
    ProjectPlaceUpdateSerializer,
    PlaceNoteSerializer,
    PlaceNoteCreateSerializer,
    PlaceNoteUpdateSerializer,
)
from ..services.external_places_client import (
    assert_place_exists,
    ExternalPlaceNotFound,
    ExternalAPIError,
)

class PlaceNoteViewSet(viewsets.ModelViewSet):
    """
    Optional direct note endpoints:
    - list: GET /api/notes/?place_id=...
    - retrieve: GET /api/notes/{id}/
    - patch: PATCH /api/notes/{id}/  { "body": "..." }
    - delete: DELETE /api/notes/{id}/
    """
    queryset = PlaceNote.objects.select_related("project_place", "project_place__project").all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            # We generally don't want create here because it allows choosing project_place from body.
            # Keep it for completeness, but prefer POST /places/{id}/notes.
            return PlaceNoteCreateSerializer
        if self.action in ("update", "partial_update"):
            return PlaceNoteUpdateSerializer
        return PlaceNoteSerializer

    def list(self, request, *args, **kwargs):
        place_id = request.query_params.get("place_id")
        qs = self.get_queryset()
        if place_id is not None:
            qs = qs.filter(project_place_id=place_id)
        return Response(PlaceNoteSerializer(qs, many=True).data)

    def create(self, request, *args, **kwargs):
        """
        Strongly consider disabling this route in production.
        Safer pattern: create via /places/{id}/notes so project_place is URL-bound.
        """
        serializer = PlaceNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save()
        return Response(PlaceNoteSerializer(note).data, status=status.HTTP_201_CREATED)