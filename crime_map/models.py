from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class SuspiciousPin(gis_models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = gis_models.PointField(geography=True)  # Replaces lat/long fields
    message = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)
    
    # For spatial queries
    objects = gis_models.Manager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            gis_models.Index(fields=['location']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        username = "Anonymous" if self.is_anonymous else self.user.username
        return f"Pin by {username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class HotZone(gis_models.Model):
    ALERT_LEVELS = (
        (1, 'Warning (5+ reports)'),
        (2, 'High Alert (10+ reports)'),
        (3, 'Critical (20+ reports)'),
    )
    
    center = gis_models.PointField(geography=True)
    radius = models.FloatField(default=1.5)  # in kilometers
    alert_level = models.IntegerField(choices=ALERT_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resolved = models.BooleanField(default=False)
    
    objects = gis_models.Manager()
    
    class Meta:
        ordering = ['-alert_level', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(weeks=6)  # 6 week default
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_alert_level_display()} Zone (Expires: {self.expires_at.date()})"
