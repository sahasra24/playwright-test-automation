from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UploadForm
from .models import ValidationRun
from .rules import validate_records


@login_required
def dashboard(request):
    runs = ValidationRun.objects.all()[:50]
    return render(request, "validation/dashboard.html", {"runs": runs})


@login_required
def upload(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        run = ValidationRun.record(
            validate_records(form.records),
            source=ValidationRun.Source.UPLOAD,
            filename=form.cleaned_data["file"].name,
            user=request.user,
        )
        messages.success(request, f"Validated {run.total_rows} rows from {run.filename}.")
        return redirect("run-detail", pk=run.pk)
    return render(request, "validation/upload.html", {"form": form})


@login_required
def run_detail(request, pk):
    run = get_object_or_404(ValidationRun, pk=pk)
    return render(request, "validation/run_detail.html", {"run": run, "errors": run.errors.all()})
