from django import forms
from django.contrib.gis import forms as gis_forms
from .models import SuspiciousPin

class PinDropForm(gis_forms.Form):
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
    location = gis_forms.PointField(
        widget=gis_forms.OSMWidget(attrs={
            'default_lat': -26.2041,  # Johannesburg
            'default_lon': 28.0473,
            'map_width': 800,
            'map_height': 500,
        })
    )