import random
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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


class Post(models.Model):
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




