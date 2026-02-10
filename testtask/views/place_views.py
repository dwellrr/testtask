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