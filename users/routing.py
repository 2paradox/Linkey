from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # ws/chat/방이름/ 형태의 주소로 WebSocket 연결이 들어오면 ChatConsumer가 처리
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
]