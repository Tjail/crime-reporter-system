from .models import Post, CrimeType, Identifier, Article, AccountType, VerificationRequest
from django import forms
from django.forms import formset_factory, BaseFormSet
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class OTPVerificationForm(forms.Form):
    email = forms.EmailField()
    otp = forms.CharField(max_length=6)


class AccountTypeSelectionForm(forms.Form):
    account_type = forms.ChoiceField(
        choices=AccountType.ACCOUNT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Select Account Type"
    )

class CustomSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    account_type = forms.ChoiceField(
        choices=AccountType.ACCOUNT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='CITIZEN',
        label="Account Type"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'account_type')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            account_type = AccountType.objects.get(user=user)
            account_type.account_type = self.cleaned_data['account_type']
            account_type.save()
        return user

class PoliceVerificationForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ['police_badge_number', 'police_station', 'police_rank', 
                  'id_document', 'proof_document']
        widgets = {
            'police_badge_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your badge number'}),
            'police_station': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your station name'}),
            'police_rank': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your rank'}),
        }
        labels = {
            'id_document': 'Upload Police ID',
            'proof_document': 'Upload Station Letter/Appointment Letter',
        }

class SecurityCompanyVerificationForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ['company_name', 'company_registration', 'psira_number',
                  'id_document', 'proof_document']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company name'}),
            'company_registration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company registration number'}),
            'psira_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PSIRA registration number'}),
        }
        labels = {
            'id_document': 'Upload Company Registration Certificate',
            'proof_document': 'Upload PSIRA Certificate',
        }

class InvestigationUpdateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['investigation_status', 'case_number', 'investigation_notes']
        widgets = {
            'investigation_status': forms.Select(attrs={'class': 'form-control'}),
            'case_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Police case number'}),
            'investigation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Investigation notes (private)'}),
        }

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