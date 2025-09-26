from django.urls import path
from . import views
from . import consumers
from django.urls import re_path
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.device_list, name='device_management'),  # 设备列表页
    path('add/', views.add_device, name='add_device'),  # 新增设备
    path('edit/<int:id>/', views.edit_device, name='edit_device'),  # 修改设备
    path('delete/<int:id>/', views.delete_device, name='delete_device'),  # 删除设备
    path('connect/<int:id>/', views.connect_device, name='connect_device'),  # 连接设备
    path('ws_test/', TemplateView.as_view(template_name="ws_test.html")),
    path("video_stream/", TemplateView.as_view(template_name="video_stream.html"), name="video_stream"),

    path('close_appium/', views.close_appium, name='close_appium'),  # 手动关闭appium

]
