from django.shortcuts import render
from django.core.paginator import Paginator
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Post
from .forms import PostForm

def post_list(request):
    category = request.GET.get("category", "")
    q = request.GET.get("q", "").strip()

    posts = Post.objects.order_by("-created_at")

    if category:
        posts = posts.filter(category=category)

    if q:
        posts = posts.filter(title__icontains=q) | posts.filter(content__icontains=q)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "community/list.html", {
        "page_obj": page_obj,
        "category": category,
        "q": q,
        "categories": Post.Category.choices,
    })

def post_detail(request, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    return render(request, "community/detail.html", {"post": post})

@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.author = request.user
            p.save()
            return redirect("community_detail", post_id=p.id)
    else:
        form = PostForm()
    return render(request, "community/new.html", {"form": form})