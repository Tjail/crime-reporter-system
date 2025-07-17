from django import forms
from .models import PinDrop

class PinDropForm(forms.ModelForm):
    class Meta:
        model = PinDrop
        fields = ['report_type', 'message', 'is_anonymous']
        widgets = {
            'report_type': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Provide details (optional)',
                'class': 'form-control'
            }),
        }
        labels = {
            'report_type': 'What type of incident?',
            'is_anonymous': 'Report anonymously'
        }

class QuickPinForm(forms.Form):
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())
    report_type = forms.ChoiceField(
        choices=PinDrop.REPORT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Incident Type'
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Brief description (optional)',
            'class': 'form-control'
        }),
        max_length=300
    )