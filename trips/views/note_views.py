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