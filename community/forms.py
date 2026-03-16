from django import forms
from .models import Post
from cloudinary.forms import CloudinaryFileField

class PostForm(forms.ModelForm):
    image = CloudinaryFileField(required=False)
    
    class Meta:
        model = Post
        fields = ["category", "title", "content", "image"]