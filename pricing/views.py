from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from urllib3 import request
from .forms import ArnoldClarkSearchForm
from .models import QuoteSearch,QuoteOffer, FavoriteOffer

ONE_WAY_FEE = 20
ARNOLD_CLARK_RATES = [
    {"code": "SMALL", "name": "Small", "daily_price": 41, "transmission": "Manual"},
    {"code": "SMALL_AUTO", "name": "Smallc", "daily_price": 49, "transmission": "Automatic"},
    {"code": "MEDIUM", "name": "Medium", "daily_price": 58, "transmission": "Manual"},
    {"code": "MEDIUM_AUTO", "name": "Medium", "daily_price": 46, "transmission": "Automatic"},
    {"code": "SUV", "name": "SUV", "daily_price": 53, "transmission": "Manual"},
    {"code": "SUV_AUTO", "name": "SUV", "daily_price": 67, "transmission": "Automatic"},
    {"code": "ESTATE_AUTO", "name": "Estate", "daily_price": 58, "transmission": "Automatic"},
]
ARNOLD_CLARK_BOOKING_URL = "https://www.arnoldclarkrental.com/"
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

    # 计算租期天数（你之前已有 _calc_days 就用你的）
    days = _calc_days(qs.pickup_datetime, qs.dropoff_datetime)

    one_way = (qs.pickup_entity_id != qs.return_entity_id)
    one_way_fee = Decimal("20.00") if one_way else Decimal("0.00")

    # 1) 先计算“报价列表”（Arnold Clark）
    computed = []
    for r in ARNOLD_CLARK_RATES:
        daily = Decimal(str(r["daily_price"]))
        total = daily * Decimal(days) + one_way_fee

        computed.append({
            "provider_name": "Arnold Clark",
            "agent_id": "arnoldclark",
            "car_name": r["name"],
            "transmission": r["transmission"],
            "seats": None,
            "total_price": total,
            "currency": "GBP",
            "deeplink_url": ARNOLD_CLARK_BOOKING_URL,
            "raw_json": {
                "rate_code": r["code"],
                "daily_price": float(daily),
                "days": days,
                "one_way_fee": float(one_way_fee),
            }
        })

    # 2) 写入数据库：清理旧 offers → 重新生成（简单稳，不怕重复）
    QuoteOffer.objects.filter(search=qs).delete()
    QuoteOffer.objects.bulk_create([
        QuoteOffer(
            search=qs,
            agent_id=o["agent_id"],
            provider_name=o["provider_name"],
            car_name=o["car_name"],
            transmission=o["transmission"],
            seats=o["seats"],
            total_price=o["total_price"],
            currency=o["currency"],
            deeplink_url=o["deeplink_url"],
            raw_json=o["raw_json"],
        )
        for o in computed
    ])

    # 3) 从 DB 读 offers（用于模板渲染）
    offers_qs = QuoteOffer.objects.filter(search=qs).order_by("total_price")

    # 额外附加一些便于模板显示的数据（模型中没有这些字段）
    for offer in offers_qs:
        raw = offer.raw_json or {}
        offer.daily_price = raw.get("daily_price")
        offer.days = raw.get("days")
        offer.one_way_fee = raw.get("one_way_fee")

        # Determine image name based on size + transmission
        name = (offer.car_name or "").lower()
        trans = (offer.transmission or "").lower()

        if "estate" in name or "large" in name:
            size_key = "estate"
        elif "suv" in name:
            size_key = "suv"
        elif "medium" in name:
            size_key = "medium"
        elif "small" in name:
            size_key = "small"
        else:
            size_key = "default"

        if "auto" in trans or "automatic" in trans:
            drive_key = "auto"
        else:
            drive_key = "manual"

        if size_key == "default":
            offer.image_name = "default-car.png"
        else:
            offer.image_name = f"{size_key}-{drive_key}.png"

    # 4) 如果用户登录，取出已收藏的 offer_ids，便于按钮状态显示
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            FavoriteOffer.objects.filter(user=request.user, offer__search=qs).values_list("offer_id", flat=True)
        )

    return render(request, "pricing/results.html", {
        "search": qs,
        "offers": offers_qs,
        "favorite_ids": favorite_ids,
        "one_way_fee": one_way_fee,
        "days": days,
        "booking_url": ARNOLD_CLARK_BOOKING_URL,
    })

@login_required
def pricing_history(request):
    # 以创建时间倒序显示搜索记录（存在创建时间相同的情况时，使用ID作为次级排序）
    searches = (
        QuoteSearch.objects
        .filter(user=request.user)
        .order_by("-created_at", "-id")
        .prefetch_related("offers")
    )
    return render(request, "pricing/history.html", {"searches": searches})

@login_required
def pricing_favorites(request):
    #先占位:你后面做FavoriteOffer时再完善
    favorites = (
        FavoriteOffer.objects
        .filter(user=request.user)
        .select_related("offer", "offer__search")
        .order_by("-created_at")
    )
    return render(request, "pricing/favorites.html", {"favorites": favorites})

@login_required
def toggle_favorite_offer(request, offer_id: int):
    offer = get_object_or_404(QuoteOffer, id=offer_id)

    fav, created = FavoriteOffer.objects.get_or_create(user=request.user, offer=offer)
    if created:
        messages.success(request, "已收藏该报价。")
    else:
        fav.delete()
        messages.info(request, "已取消收藏。")

    # 回到报价结果页（更符合用户习惯）
    return redirect("pricing_results", search_id=offer.search_id)