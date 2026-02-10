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