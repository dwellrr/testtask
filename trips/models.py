from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class TravelProject(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)

    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recompute_completion(self) -> None:
        """
        Project is completed if it has >= 1 place and all are visited.
        """
        qs = self.places.all()
        if not qs.exists():
            new_completed = False
        else:
            new_completed = not qs.filter(visited=False).exists()

        if new_completed and not self.completed:
            self.completed = True
            self.completed_at = timezone.now()
            self.save(update_fields=["completed", "completed_at", "updated_at"])
        elif not new_completed and self.completed:
            self.completed = False
            self.completed_at = None
            self.save(update_fields=["completed", "completed_at", "updated_at"])


class ProjectPlace(models.Model): #TODO: make a place its own class with caching so we don't pull too much from the API (for rates and stuff)

    """
    A place within a certain project
    """
    project = models.ForeignKey(
        TravelProject,
        on_delete=models.CASCADE,
        related_name="places",
    )

    external_id = models.PositiveIntegerField()  # AIC artwork id
    visited = models.BooleanField(default=False)
    visited_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "external_id"],
                name="uniq_place_per_project",
            )
        ]

    def save(self, *args, **kwargs):
        from django.utils import timezone

        if self.visited and self.visited_at is None:
            self.visited_at = timezone.now()
        if not self.visited:
            self.visited_at = None
        super().save(*args, **kwargs)

class PlaceNote(models.Model):
    """
    Notes attached to a place within a project.
    Supports history by having multiple notes per ProjectPlace.
    """
    project_place = models.ForeignKey(
        ProjectPlace,
        on_delete=models.CASCADE,
        related_name="notes",
    )

    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]