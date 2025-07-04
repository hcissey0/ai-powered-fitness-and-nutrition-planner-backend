"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

from rest_framework import routers
from rest import views as rest_views

router = routers.DefaultRouter() 
router.register(r'users', rest_views.UserViewSet, basename='user')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', rest_views.LoginView.as_view(), name='auth-login'),
    path('api/auth/signup/', rest_views.SignUpView.as_view(), name='auth-signup'),
    path('api/', include(router.urls)),  # Include the router URLs for User and Group viewsets
]
