from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class SuspiciousPin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    message = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        username = "Anonymous" if self.is_anonymous else self.user.username
        return f"Pin by {username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class HotZone(models.Model):
    ALERT_LEVELS = (
        (1, 'Warning (5+ reports)'),
        (2, 'High Alert (10+ reports)'),
        (3, 'Critical (20+ reports)'),
    )
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius = models.FloatField(default=1.5)  # in kilometers
    alert_level = models.IntegerField(choices=ALERT_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-alert_level', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(weeks=6)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_alert_level_display()} Zone (Expires: {self.expires_at.date()})"
