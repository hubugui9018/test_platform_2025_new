from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='ui_index'),  # UI 自动化首页
]
