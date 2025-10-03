# backend_server/urls.py (최종 수정본)

from django.contrib import admin
from django.urls import path, include
from users.views import home, main_page, chat_room, chat_list_page
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', home, name='home'),
    path('main/', main_page, name='main'),
    path('chats/', chat_list_page, name='chat_list_page'),
    path('chat/<int:user2_id>/', chat_room, name='chat_room'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
]

# 맨 뒤의 (venv)를 삭제합니다.
urlpatterns += staticfiles_urlpatterns()