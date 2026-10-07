from django import forms

from .models import Application


class ApplicationForm(forms.ModelForm):
    application_date = forms.DateField(
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    class Meta:
        model = Application
        fields = ["company", "role", "application_date", "status"]
        widgets = {"status": forms.TextInput(attrs={"list": "status-options"})}
