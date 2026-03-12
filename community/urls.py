from django.urls import path
from . import views # 如果你有视图的话

urlpatterns = [
    # 哪怕现在是空的，也必须有这个变量
    # path('', views.some_view, name='pricing_index'),
    path("", views.post_list, name="community_list"),
    path("post/<int:post_id>/", views.post_detail, name="community_detail"),
    path("new/", views.post_create, name="community_new"),
    path("post/<int:post_id>/delete/", views.post_delete, name="community_delete"),
]