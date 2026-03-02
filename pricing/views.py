from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# Create your views here.
from .forms import QuoteSearchForm
from .models import QuoteSearch

def pricing_search(request):
    if request.method == "POST":
        form = QuoteSearchForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            qs = QuoteSearch.objects.create(
                user=request.user if request.user.is_authenticated else None,
                pickup_entity_id=cd["pickup_entity_id"],
                pickup_datetime=cd["pickup_datetime"],
                dropoff_datetime=cd["dropoff_datetime"],
                driver_age=cd["driver_age"],
                session_token="PENDING_TOKEN",  # 先占位，未来接 API 后会替换为真实 token
            )
            return redirect("pricing_results", search_id=qs.id)
    else:
        form = QuoteSearchForm()
    return render(request, "pricing/search.html", {"form": form})

def pricing_results(request, search_id: int):
    qs = get_object_or_404(QuoteSearch, id=search_id)
    return render(request, "pricing/results.html", {"search": qs})

@login_required
def pricing_history(request):
    #先占位：后面再按user过滤QuoteSearch
    searches = QuoteSearch.objects.filter(user=request.user).order_by("-created_at")
    return render(request,"pricing/history.html",{"searches":searches})

@login_required
def pricing_favorites(request):
    #先占位:你后面做FavoriteOffer时再完善
    return render(request,"pricing/favorites.html")