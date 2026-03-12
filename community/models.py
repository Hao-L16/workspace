from django.db import models
from django.conf import settings
# Create your models here.
class Post(models.Model):
    class Category(models.TextChoices):
        ROUTE = "ROUTE", "Route"
        AVOID = "AVOID", "Avoid"
        TIPS = "TIPS", "Tips"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    category = models.CharField(max_length=16, choices=Category.choices)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="post_images/", null=True, blank=True)
    def __str__(self):
        return self.title