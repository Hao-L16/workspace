from django import forms
from django.utils import timezone
from datetime import datetime
PICKUP_LOCATIONS = [
    ("GLA_PA3", "Glasgow Airport (PA3)"),
    ("G32_HAMILTON", "Glasgow Hamilton Rd (G32)"),
    ("G5_KILBIRNIE", "Glasgow Kilbirnie St (G5)"),
    ("G14_SOUTH", "Glasgow South St (G14)"),
]

class ArnoldClarkSearchForm(forms.Form):
    pickup_location = forms.ChoiceField(choices=PICKUP_LOCATIONS, label="Pick-up location")
    pickup_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Pick-up date")
    pickup_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}), label="Pick-up time")

    return_location = forms.ChoiceField(choices=PICKUP_LOCATIONS, label="Return location")
    return_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Return date")
    return_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}), label="Return time")

    def clean(self):
        cd = super().clean()
        if all(k in cd for k in ["pickup_date","pickup_time","return_date","return_time"]):
            pu = datetime.combine(cd["pickup_date"], cd["pickup_time"])
            rt = datetime.combine(cd["return_date"], cd["return_time"])
            if rt <= pu:
                raise forms.ValidationError("Return datetime must be after pick-up datetime.")
        return cd