#This file is crime_map/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class PinDrop(models.Model):
    REPORT_TYPE_CHOICES = [
        ('suspicious', 'Suspicious Activity'),
        ('petty', 'Petty Crime'),
        ('felony', 'Felony Crime'),
        ('other', 'Other Incident'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    message = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=True)
    requires_followup = models.BooleanField(default=False)
    
    
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['created_at']),
            models.Index(fields=['report_type']),
        ]
        
    def __str__(self):
        return f"{self.get_report_type_display()} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_display_name(self):
        """Always return Anonymous for privacy"""
        return "Anonymous User"

class HotZone(models.Model):
    ALERT_LEVELS = (
        (1, 'Warning (5+ reports)'),
        (2, 'High Alert (10+ reports)'),
        (3, 'Critical (20+ reports)'),
    )
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius = models.FloatField(default=1.5)
    alert_level = models.IntegerField(choices=ALERT_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-alert_level', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(weeks=6)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_alert_level_display()} Zone (Expires: {self.expires_at.date()})"
