from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from .forms import ApplicationForm, ApplicationStatusForm
from .models import Application


@require_safe
def application_list(request):
    return render(request, "applications/list.html", {
        "applications": Application.objects.all(),
    })


@require_http_methods(["GET", "POST"])
def application_create(request):
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Application saved.")
            return redirect("applications:list")
    else:
        form = ApplicationForm(initial={
            "application_date": timezone.localdate(), "status": "Applied",
        })
    return render(request, "applications/form.html", {"form": form})


@require_http_methods(["GET", "POST"])
def application_update_status(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == "POST":
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            updated_application = form.save(commit=False)
            updated_application.save(update_fields=["status"])
            messages.success(request, "Application status updated.")
            return redirect("applications:list")
    else:
        form = ApplicationStatusForm(instance=application)
    return render(request, "applications/status_form.html", {
        "form": form, "application": application,
    })
