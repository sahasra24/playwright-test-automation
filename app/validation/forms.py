from django import forms
from django.conf import settings

from .rules import SchemaError, parse_csv


class UploadForm(forms.Form):
    file = forms.FileField(label="CSV file")

    def clean_file(self):
        upload = self.cleaned_data["file"]
        if not upload.name.lower().endswith(".csv"):
            raise forms.ValidationError("Only .csv files are accepted.")
        if upload.size > settings.VALIDATOR_MAX_UPLOAD_BYTES:
            raise forms.ValidationError("File is larger than the 2 MB limit.")
        try:
            self.records = parse_csv(upload.read(), settings.VALIDATOR_MAX_ROWS)
        except SchemaError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return upload
