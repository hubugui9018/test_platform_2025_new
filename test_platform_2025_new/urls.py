"""
URL configuration for test_platform_2025_new project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ui/', include('ui_automation.urls')),  # UI 自动化功能路由
    path('device/', include('device_management.urls')),  # 设备管理功能路由
    path('', views.index),  # 主页面或主页功能路由
    path('device_management/', include('device_management.urls')),
    path('element_management/', include('element_management.urls')),

]
