from django.contrib import admin
from .models import Post
# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "title", "author", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "content", "author__username")