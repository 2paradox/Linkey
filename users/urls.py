# users/urls.py (최종 수정본)

from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('verify-email/<str:uidb64>/<str:token>', views.verify_email, name='verify-email'),
    path('me', views.get_user_info, name='me'),
    path('check-username', views.check_username, name='check-username'),
    path('recommendations', views.recommend_users, name='recommendations'),
    path('<int:user_id>/like/', views.like_user, name='like_user'),
    path('likes-received/', views.get_likes_received, name='get_likes_received'),
    # 'chats/' 경로는 API를 위한 get_chat_list 하나만 남깁니다.
    path('chats/', views.get_chat_list, name='get_chat_list'),
]