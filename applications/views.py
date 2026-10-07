from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from .forms import ApplicationForm
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
