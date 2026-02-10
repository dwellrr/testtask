"""
Views related to Projects

Endpoints:

GET /api/projects/
POST /api/projects/ (create project + places)
GET /api/projects/{id}/
PATCH /api/projects/{id}/
DELETE /api/projects/{id}/
POST /api/projects/{id}/places (add place by external_id, validate upstream)
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

class TravelProjectViewSet(viewsets.ModelViewSet):
    queryset = TravelProject.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return TravelProjectCreateSerializer
        return TravelProjectSerializer
    
    def create(self, request, *args, **kwargs):
        in_ser = TravelProjectCreateSerializer(data=request.data)
        in_ser.is_valid(raise_exception=True)
        project = in_ser.save()

        out_ser = TravelProjectSerializer(project, context={"request": request})
        return Response(out_ser.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.places.filter(visited=True).exists():
            return Response(
                {"detail": "Cannot delete a project with any visited places."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="places")
    @transaction.atomic
    def add_place(self, request, pk=None):
        """
        POST /api/projects/{id}/places
        Body: { "external_id": 12345 }
        """
        project = self.get_object()

        if project.places.count() >= 10:
            return Response(
                {"detail": "Project cannot contain more than 10 places."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        external_id = request.data.get("external_id")
        if external_id is None:
            return Response(
                {"external_id": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            external_id = int(external_id)
        except (TypeError, ValueError):
            return Response(
                {"external_id": "Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ProjectPlace.objects.filter(project=project, external_id=external_id).exists():
            return Response(
                {"detail": "This place already exists in the project."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            assert_place_exists(external_id)
        except ExternalPlaceNotFound:
            return Response(
                {"detail": f"External place {external_id} does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ExternalAPIError as e:
            return Response(
                {"detail": f"External API error while validating {external_id}: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        place = ProjectPlace.objects.create(project=project, external_id=external_id)
        project.recompute_completion()

        return Response(ProjectPlaceSerializer(place).data, status=status.HTTP_201_CREATED)