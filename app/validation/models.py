from django.conf import settings
from django.db import models, transaction

from .rules import ValidationResult


class ValidationRun(models.Model):
    class Source(models.TextChoices):
        UPLOAD = "upload", "File upload"
        API = "api", "API"

    filename = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=10, choices=Source.choices)
    total_rows = models.PositiveIntegerField()
    valid_rows = models.PositiveIntegerField()
    invalid_rows = models.PositiveIntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Run #{self.pk} ({self.filename or self.source})"

    @property
    def status(self) -> str:
        return "passed" if self.invalid_rows == 0 else "failed"

    @classmethod
    @transaction.atomic
    def record(cls, result: ValidationResult, *, source: str, filename: str = "", user=None):
        run = cls.objects.create(
            filename=filename[:255],
            source=source,
            total_rows=result.total_rows,
            valid_rows=result.valid_rows,
            invalid_rows=result.invalid_rows,
            created_by=user,
        )
        RowError.objects.bulk_create(
            RowError(run=run, row_number=e.row, field=e.field, message=e.message)
            for e in result.errors
        )
        return run

    def to_dict(self, include_errors: bool = False) -> dict:
        data = {
            "id": self.pk,
            "filename": self.filename,
            "source": self.source,
            "status": self.status,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "created_at": self.created_at.isoformat(),
        }
        if include_errors:
            data["errors"] = [
                {"row": e.row_number, "field": e.field, "message": e.message}
                for e in self.errors.all()
            ]
        return data


class RowError(models.Model):
    run = models.ForeignKey(ValidationRun, related_name="errors", on_delete=models.CASCADE)
    row_number = models.PositiveIntegerField()
    field = models.CharField(max_length=50)
    message = models.CharField(max_length=255)

    class Meta:
        ordering = ["row_number", "id"]

    def __str__(self):
        return f"Row {self.row_number} {self.field}: {self.message}"
