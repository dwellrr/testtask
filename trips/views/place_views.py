"""
Views related to Places of a project.

Endpoints:

GET /api/places/?project_id=... (list places for project)
GET /api/places/{place_id}/
PATCH /api/places/{place_id}/ (visited only)
GET /api/places/{place_id}/notes (list notes for place)
POST /api/places/{place_id}/notes (create note for place)
"""

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import TravelProject, ProjectPlace, PlaceNote
from ..serializers import (
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

class ProjectPlaceViewSet(viewsets.ModelViewSet):

    queryset = ProjectPlace.objects.select_related("project").prefetch_related("notes").all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return ProjectPlaceUpdateSerializer
        return ProjectPlaceSerializer

    def list(self, request, *args, **kwargs):
        project_id = request.query_params.get("project_id")
        qs = self.get_queryset()
        if project_id is not None:
            qs = qs.filter(project_id=project_id)
        return Response(ProjectPlaceSerializer(qs, many=True).data)

    def perform_update(self, serializer):
        place = serializer.save()
        place.project.recompute_completion()

    @action(detail=True, methods=["get", "post"], url_path="notes")
    def notes(self, request, pk=None):
        """
        GET  /api/places/{place_id}/notes
        POST /api/places/{place_id}/notes  { "body": "..." }

        Note: project_place is derived from the URL, not accepted from client.
        """
        place = self.get_object()

        if request.method == "GET":
            qs = place.notes.all().order_by("-created_at")
            return Response(PlaceNoteSerializer(qs, many=True).data)

        # POST
        serializer = PlaceNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        note = PlaceNote.objects.create(
            project_place=place,
            body=serializer.validated_data["body"],
        )
        return Response(PlaceNoteSerializer(note).data, status=status.HTTP_201_CREATED)