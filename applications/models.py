from django.db import models


class Application(models.Model):
    """Map Django's model to the table used by the terminal tracker."""

    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    application_date = models.DateField()
    status = models.CharField(max_length=100, default="Applied")

    class Meta:
        db_table = "applications"
        ordering = ["id"]

    def __str__(self):
        return f"{self.company} - {self.role}"
