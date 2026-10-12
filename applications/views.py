from django.contrib import messages
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from .forms import ApplicationForm, ApplicationStatusForm
from .models import Application


SORT_OPTIONS = {
    "date_desc": ("Applied: newest first", ("-application_date", "pk")),
    "date_asc": ("Applied: oldest first", ("application_date", "pk")),
    "company_asc": ("Company: A–Z", (Lower("company").asc(), "pk")),
    "company_desc": ("Company: Z–A", (Lower("company").desc(), "pk")),
    "role_asc": ("Role: A–Z", (Lower("role").asc(), "pk")),
    "role_desc": ("Role: Z–A", (Lower("role").desc(), "pk")),
    "status_asc": ("Status: A–Z", (Lower("status").asc(), "pk")),
    "status_desc": ("Status: Z–A", (Lower("status").desc(), "pk")),
}


@require_safe
def application_list(request):
    selected_sort = request.GET.get("sort", "date_desc")
    if selected_sort not in SORT_OPTIONS:
        selected_sort = "date_desc"
    ordering = SORT_OPTIONS[selected_sort][1]
    return render(request, "applications/list.html", {
        "applications": Application.objects.order_by(*ordering),
        "selected_sort": selected_sort,
        "sort_options": [(value, option[0]) for value, option in SORT_OPTIONS.items()],
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
