from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import ArnoldClarkSearchForm
from .models import QuoteSearch

ONE_WAY_FEE = 20
ARNOLD_CLARK_RATES = [
    {"code": "SMALL", "name": "Smallr", "daily_price": 41, "transmission": "Manual"},
    {"code": "SMALL_AUTO", "name": "Small Automatic", "daily_price": 49, "transmission": "Automatic"},
    {"code": "MEDIUM", "name": "Medium", "daily_price": 58, "transmission": "Manual"},
    {"code": "MEDIUM_AUTO", "name": "Medium Automatic", "daily_price": 46, "transmission": "Automatic"},
    {"code": "SUV", "name": "SUV", "daily_price": 53, "transmission": "Manual"},
    {"code": "SUV_AUTO", "name": "SUV Automatic", "daily_price": 67, "transmission": "Automatic"},
    {"code": "ESTATE_AUTO", "name": "Large Estate Automatic", "daily_price": 58, "transmission": "Automatic"},
]
ARNOLD_CLARK_BOOKING_URL = "https://www.arnoldclark.com/car-hire"
def _calc_days(pickup_dt: datetime, return_dt: datetime) -> int:
    seconds = (return_dt - pickup_dt).total_seconds()
    days = int(seconds // 86400)
    if seconds % 86400 != 0:
        days += 1  # any partial day counts as 1 day
    return max(days, 1)

def pricing_search(request):
    if request.method == "POST":
        form = ArnoldClarkSearchForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            pickup_dt = datetime.combine(cd["pickup_date"], cd["pickup_time"])
            return_dt = datetime.combine(cd["return_date"], cd["return_time"])

            # Save user's input to DB (meets coursework requirement)
            qs = QuoteSearch.objects.create(
                user=request.user if request.user.is_authenticated else None,
                pickup_entity_id=cd["pickup_location"], 
                return_entity_id=cd["return_location"],  # reuse your existing field
                pickup_datetime=pickup_dt,
                dropoff_datetime=return_dt,
                driver_age=25,  # if your model requires it; or make it nullable / remove from model
            )
            return redirect("pricing_results", search_id=qs.id)
    else:
        form = ArnoldClarkSearchForm()

    return render(request, "pricing/search.html", {"form": form})

def pricing_results(request, search_id: int):
    qs = get_object_or_404(QuoteSearch, id=search_id)
    days = _calc_days(qs.pickup_datetime, qs.dropoff_datetime)
    one_way = (qs.pickup_entity_id != qs.return_entity_id)
    one_way_fee = ONE_WAY_FEE if one_way else 0
    offers = []
    for r in ARNOLD_CLARK_RATES:
        total = r["daily_price"] * days + one_way_fee
        offers.append({
            "provider": "Arnold Clark",
            "car_type": r["name"],
            "transmission": r["transmission"],
            "daily_price": r["daily_price"],
            "days": days,
            "one_way_fee": one_way_fee,
            "total_price": total,
            "currency": "GBP",
            "booking_url": ARNOLD_CLARK_BOOKING_URL,
        })

    # sort by total price
    offers.sort(key=lambda x: x["total_price"])

    return render(request, "pricing/results.html", {
        "search": qs,
        "offers": offers,
        "booking_url": ARNOLD_CLARK_BOOKING_URL,
    })

@login_required
def pricing_history(request):
    #先占位：后面再按user过滤QuoteSearch
    searches = QuoteSearch.objects.filter(user=request.user).order_by("-created_at")
    return render(request,"pricing/history.html",{"searches":searches})

@login_required
def pricing_favorites(request):
    #先占位:你后面做FavoriteOffer时再完善
    return render(request,"pricing/favorites.html")