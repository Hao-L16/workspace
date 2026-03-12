from django.conf import settings
from django.db import models

class QuoteSearch(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        READY = "READY"
        FAILED = "FAILED"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quote_searches",
    )

    market = models.CharField(max_length=10, default="UK")
    locale = models.CharField(max_length=20, default="en-GB")
    currency = models.CharField(max_length=10, default="GBP")

    pickup_entity_id = models.CharField(max_length=32)
    return_entity_id = models.CharField(max_length=32)
    pickup_datetime = models.DateTimeField()
    dropoff_datetime = models.DateTimeField()

    driver_age = models.PositiveSmallIntegerField()

    included_agent_ids = models.JSONField(null=True, blank=True)  # e.g. ["vipd","sixt"]

    session_token = models.CharField(max_length=256, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Search#{self.id} {self.pickup_entity_id} {self.pickup_datetime:%Y-%m-%d}"


class QuoteOffer(models.Model):
    search = models.ForeignKey(QuoteSearch, on_delete=models.CASCADE, related_name="offers")

    agent_id = models.CharField(max_length=64, null=True, blank=True)
    provider_name = models.CharField(max_length=128, null=True, blank=True)

    car_name = models.CharField(max_length=128, null=True, blank=True)
    transmission = models.CharField(max_length=32, null=True, blank=True)
    seats = models.PositiveSmallIntegerField(null=True, blank=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="GBP")

    deeplink_url = models.URLField(null=True, blank=True)

    raw_json = models.JSONField()  # store raw offer for debugging/mapping
    fetched_at = models.DateTimeField(auto_now_add=True)


class FavoriteOffer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_offers")
    offer = models.ForeignKey(QuoteOffer, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "offer"], name="uniq_user_offer_fav")
        ]