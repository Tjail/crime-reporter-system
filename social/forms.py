from .models import Post, CrimeType, Identifier, Article
from django import forms
from django.forms import formset_factory, BaseFormSet


class OTPVerificationForm(forms.Form):
    email = forms.EmailField()
    otp = forms.CharField(max_length=6)


class PostForm(forms.ModelForm):

    agree_to_terms = forms.BooleanField(
        label="I have read and agree to the Terms and Conditions and Privacy Policy.",
        required=True,
        error_messages={'required': 'You must agree before submitting a report.'}
    )

    crime_types = forms.ModelMultipleChoiceField(
        queryset=CrimeType.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'crime-type-selector',
            'id': 'crime-types'
        }),
        required=True,
        label="Select all applicable crime types"
    )

    incident_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    incident_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    location_city = forms.CharField()
    location_province = forms.CharField()
    location_country = forms.CharField()

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Describe what happened in 250 words or more...'
        })
    )


    evidence = forms.FileField(required=False)

    class Meta:
        model = Post
        fields = [
            'crime_types', 'incident_date', 'incident_time',
            'location_city', 'location_province', 'location_country',
            'description', 'evidence'
        ]

class IdentifierForm(forms.ModelForm):
    class Meta:
        model = Identifier
        fields = ['identifier_type', 'value']
        widgets = {
            'identifier_type': forms.TextInput(attrs={'placeholder': 'e.g. Phone Number'}),
            'value': forms.TextInput(attrs={'placeholder': 'e.g. 0781234567'}),
        }


class BaseIdentifierFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        seen_values = set()
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            value = form.cleaned_data.get('value')
            if value:
                if value in seen_values:
                    raise forms.ValidationError("Duplicate identifiers are not allowed in a single report.")
                seen_values.add(value)

IdentifierFormSet = formset_factory(
    IdentifierForm,
    formset=BaseIdentifierFormSet,
    extra=1,
    can_delete=True
)

class IdentifierSearchForm(forms.Form):
    query = forms.CharField(
        label='Search Identifier',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. ID Number, Phone, License'
        })
    )



class ExploreForm(forms.Form):
    query = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': 'Explore tags'
        })
    )

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'image', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
        }