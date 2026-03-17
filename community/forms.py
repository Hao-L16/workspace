from django import forms
from .models import Post
from cloudinary.forms import CloudinaryFileField


class PostForm(forms.ModelForm):
    image = CloudinaryFileField(required=False)

    class Meta:
        model = Post
        fields = ["category", "title", "content", "image"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Cheap airport pickup route from Glasgow city centre"
            }),
            "category": forms.Select(attrs={
                "class": "form-select"
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe the route, issue, or useful tip in a clear way..."
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].widget.attrs.update({
            "class": "form-control"
        })
