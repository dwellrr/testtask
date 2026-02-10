from django.db import transaction
from rest_framework import serializers

from .models import TravelProject, ProjectPlace, PlaceNote
from .services.external_places_client import (
    assert_place_exists,
    ExternalPlaceNotFound,
    ExternalAPIError,
)


# -------------------------
# Notes
# -------------------------

class PlaceNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceNote
        fields = ["id", "project_place", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlaceNoteCreateSerializer(serializers.ModelSerializer):
    """
    Use for POSTing notes.
    """
    class Meta:
        model = PlaceNote
        fields = ["id", "project_place", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlaceNoteUpdateSerializer(serializers.ModelSerializer):
    """
    Use for UPDATE...ing notes.
    """
    class Meta:
        model = PlaceNote
        fields = ["body"]


# -------------------------
# Places in a Project
# -------------------------

class ProjectPlaceSerializer(serializers.ModelSerializer):
    # Notes nested when retrieving a place:
    notes = PlaceNoteSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectPlace
        fields = [
            "id",
            "project",
            "external_id",
            "visited",
            "visited_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "visited_at", "created_at", "updated_at"]


class ProjectPlaceUpdateSerializer(serializers.ModelSerializer):
    """
    Only allow mutating fields required by spec.
    Notes are updated via PlaceNote endpoints.
    """
    class Meta:
        model = ProjectPlace
        fields = ["visited"]


# -------------------------
# Projects
# -------------------------

class TravelProjectSerializer(serializers.ModelSerializer):
    places = ProjectPlaceSerializer(many=True, read_only=True)

    class Meta:
        model = TravelProject
        fields = [
            "id",
            "name",
            "description",
            "start_date",
            "completed",
            "completed_at",
            "places",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "completed", "completed_at", "created_at", "updated_at"]


class TravelProjectCreateSerializer(serializers.ModelSerializer):
    """
    Create a project AND its places in one request.
    Input shape:
    {
      "name": "...",
      "description": "...",
      "start_date": "YYYY-MM-DD",
      "places": [27992, 87165]
    }
    """
    places = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        allow_empty=False,
        help_text="List of external place IDs (AIC artwork ids). Min 1, max 10.",
    )

    class Meta:
        model = TravelProject
        fields = ["id", "name", "description", "start_date", "places"]
        read_only_fields = ["id"]

    def validate_places(self, places):
        if len(places) < 1:
            raise serializers.ValidationError("Project must contain at least 1 place.")
        if len(places) > 10:
            raise serializers.ValidationError("Project cannot contain more than 10 places.")
        if len(set(places)) != len(places):
            raise serializers.ValidationError("Duplicate external_id in places array.")
        return places

    @transaction.atomic
    def create(self, validated_data):
        places = validated_data.pop("places")

        project = TravelProject.objects.create(**validated_data)

        # Validate each external id exists upstream BEFORE persisting all.
        # (If you prefer partial success, that’s a different contract.)
        for ext_id in places:
            try:
                assert_place_exists(ext_id)
            except ExternalPlaceNotFound:
                raise serializers.ValidationError(
                    {"places": f"External place {ext_id} does not exist."}
                )
            except ExternalAPIError as e:
                raise serializers.ValidationError(
                    {"places": f"External API error while validating {ext_id}: {e}"}
                )

        # Create places after validation passes for all
        ProjectPlace.objects.bulk_create(
            [ProjectPlace(project=project, external_id=ext_id) for ext_id in places]
        )

        project.recompute_completion()
        return project
