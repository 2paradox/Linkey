from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('me', views.get_user_info, name='me'),
    path('verify-email/<str:uidb64>/<str:token>', views.verify_email, name='verify-email'),
    path('check-username', views.check_username, name='check-username'),
    path('recommendations', views.recommend_users, name='recommendations'),
    path('<int:user_id>/like/', views.like_user, name='like_user'),
    path('likes-received/', views.get_likes_received, name='get_likes_received'),
]