from django.db import models
from django.utils.text import slugify

class ReportSnapshot(models.Model):
    location_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    risk_scores = models.JSONField()
    ai_analysis_text = models.TextField()
    raw_data = models.JSONField()

    timestamp = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils import timezone
            timestamp_str = timezone.now().strftime('%Y-%m-%d-%H%M')
            base_slug = slugify(f"{self.location_name}-{timestamp_str}")
            self.slug = base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Report for {self.location_name} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
