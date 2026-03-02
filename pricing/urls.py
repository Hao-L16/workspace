from django.urls import path
from . import views # 如果你有视图的话

urlpatterns = [
    # 哪怕现在是空的，也必须有这个变量
    # path('', views.some_view, name='pricing_index'),
    path("search/", views.pricing_search, name="pricing_search"),
    path("results/<int:search_id>/", views.pricing_results, name="pricing_results"),
    path("history/",views.pricing_history, name = "pricing_history"),
    path("favorites/",views.pricing_favorites,name="pricing_favorites"),

]