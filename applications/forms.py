from django import forms

from .models import Application


STATUS_CHOICES = [
    ("", "Select a status"),
    ("Applied", "Applied"),
    ("Interviewing", "Interviewing"),
    ("Offer", "Offer"),
    ("Rejected", "Rejected"),
]


class ApplicationForm(forms.ModelForm):
    application_date = forms.DateField(
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES)

    class Meta:
        model = Application
        fields = ["company", "role", "application_date", "status"]


class ApplicationStatusForm(forms.ModelForm):
    """Choose a supported status without editing other application fields."""

    status = forms.ChoiceField(choices=STATUS_CHOICES)

    class Meta:
        model = Application
        fields = ["status"]
