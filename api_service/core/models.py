from django.db import models
from django.contrib.auth.models import User


class Translation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    text = models.CharField(max_length=255)
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    translation = models.CharField(max_length=255)
    confidence = models.FloatField(default=0.0)  # 🔥 AJOUT
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.translation

    def __str__(self):
        return f"History {self.id}"