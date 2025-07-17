from django import forms
from .models import PinDrop

class PinDropForm(forms.Form):
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional: describe suspicious activity',
            'maxlength': '500'
        }),
        required=False
    )
    is_anonymous = forms.BooleanField(
        required=False,
        initial=False,
        label="Report anonymously"
    )
    reason = forms.ChoiceField(
        choices=PinDrop.REASON_CHOICES,
        widget=forms.RadioSelect,
        label="Reason for reporting"
    )