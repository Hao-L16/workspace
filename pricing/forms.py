from django import forms
from django.utils import timezone

GLASGOW_LOCATIONS = [
    ("27544008", "Glasgow Airport (GLA)"),
    ("GLASGOW_CITY", "Glasgow City Centre (placeholder)"),
]

class QuoteSearchForm(forms.Form):
    pickup_entity_id = forms.ChoiceField(choices=GLASGOW_LOCATIONS, label="取车地点")
    pickup_datetime = forms.DateTimeField(
        label="取车时间",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    dropoff_datetime = forms.DateTimeField(
        label="还车时间",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    driver_age = forms.IntegerField(label="驾驶员年龄", min_value=18, max_value=90)

    def clean(self):
        cleaned = super().clean()
        pu = cleaned.get("pickup_datetime")
        do = cleaned.get("dropoff_datetime")
        if pu and do:
            if do <= pu:
                raise forms.ValidationError("还车时间必须晚于取车时间。")
            if pu < timezone.now():
                raise forms.ValidationError("取车时间不能早于当前时间。")
        return cleaned