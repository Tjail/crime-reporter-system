# this file is social/models.py
import random
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class CrimeType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()


class AccountType(models.Model):
    CITIZEN = 'CITIZEN'
    POLICE = 'POLICE'
    SECURITY_COMPANY = 'SECURITY'
    
    ACCOUNT_TYPE_CHOICES = [
        (CITIZEN, 'Citizen'),
        (POLICE, 'Police Officer'),
        (SECURITY_COMPANY, 'Security Company'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account_type')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default=CITIZEN)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verifications_done')
    
    # Police-specific fields
    badge_number = models.CharField(max_length=50, blank=True, null=True)
    station = models.CharField(max_length=200, blank=True, null=True)
    rank = models.CharField(max_length=100, blank=True, null=True)
    
    # Security Company-specific fields
    company_name = models.CharField(max_length=200, blank=True, null=True)
    company_registration = models.CharField(max_length=100, blank=True, null=True)
    psira_number = models.CharField(max_length=100, blank=True, null=True)
    subscription_tier = models.CharField(max_length=20, choices=[
        ('BASIC', 'Basic'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ], blank=True, null=True)
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_calls_limit = models.IntegerField(default=1000)
    api_calls_used = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()}"
    
    def is_police(self):
        return self.account_type == self.POLICE and self.is_verified
    
    def is_security_company(self):
        return self.account_type == self.SECURITY_COMPANY and self.is_verified
    
    def can_view_evidence(self):
        return self.is_police()
    
    def can_mark_investigated(self):
        return self.is_police()

# Verification Request Model
class VerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('MORE_INFO', 'More Information Required'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    account_type = models.CharField(max_length=20, choices=AccountType.ACCOUNT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Verification documents
    id_document = models.FileField(upload_to='verification/id_documents/', blank=True, null=True)
    proof_document = models.FileField(upload_to='verification/proof_documents/', blank=True, null=True)
    additional_document = models.FileField(upload_to='verification/additional/', blank=True, null=True)
    
    # Request details
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_done')
    rejection_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Police verification fields
    police_badge_number = models.CharField(max_length=50, blank=True, null=True)
    police_station = models.CharField(max_length=200, blank=True, null=True)
    police_rank = models.CharField(max_length=100, blank=True, null=True)
    
    # Security company verification fields
    company_name = models.CharField(max_length=200, blank=True, null=True)
    company_registration = models.CharField(max_length=100, blank=True, null=True)
    psira_number = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()} - {self.status}"

class Post(models.Model):
    
    INVESTIGATION_STATUS = [
        ('REPORTED', 'Reported'),
        ('UNDER_INVESTIGATION', 'Under Investigation'),
        ('INVESTIGATED', 'Investigated'),
        ('CLOSED', 'Case Closed'),
    ]
    
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    terms_accepted_on = models.DateTimeField(null=True, blank=True)

    # New fields
    crime_types = models.ManyToManyField(CrimeType)
    incident_date = models.DateField(default= timezone.now)
    incident_time = models.TimeField(default= "00:00:00")
    location_city = models.CharField(max_length=100, default= "unknown")
    location_province = models.CharField(max_length=100, default= "unknown")
    location_country = models.CharField(max_length=100, default= "unknown")

    description = models.TextField(default= "No description provided" )
    evidence = models.FileField(upload_to='uploads/evidence/', blank=True, null=True)  # Only viewable by authorities

    image = models.ImageField(upload_to='uploads/post_photos', blank=True, null=True)
    tags = models.ManyToManyField('Tag', blank=True)
    
    investigation_status = models.CharField(max_length=30, choices=INVESTIGATION_STATUS, default='REPORTED')
    investigating_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='investigations')
    investigation_notes = models.TextField(blank=True, null=True)
    investigation_updated = models.DateTimeField(null=True, blank=True)
    case_number = models.CharField(max_length=50, blank=True, null=True)

    def create_tags(self):
        for word in self.description.split():
            if word.startswith('#'):
                tag, created = Tag.objects.get_or_create(name=word[1:])
                self.tags.add(tag.pk)
        self.save()


class Identifier(models.Model):
    post = models.ForeignKey(Post, related_name='identifiers', on_delete=models.CASCADE)
    identifier_type = models.CharField(max_length=50)  # e.g., Phone, ID, License
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.identifier_type}: {self.value}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True, verbose_name= 'user', related_name='profile', on_delete=models.CASCADE)
    name = models.CharField(max_length=30, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    birth_date=models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    picture = models.ImageField(upload_to='uploads/profile_pictures', default='uploads/profile_pictures/default.png', blank=True)
    
    is_verified = models.BooleanField(default=False)

class Tag(models.Model):
    name = models.CharField(max_length=255)

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='article_images/', null=True, blank=True)
    category = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class APIAccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    response_code = models.IntegerField()
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} - {self.timestamp}"

@receiver(post_save, sender=User)
def create_account_type(sender, instance, created, **kwargs):
    if created:
        AccountType.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_account_type(sender, instance, **kwargs):
    if hasattr(instance, 'account_type'):
        instance.account_type.save()


