from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # ws/chat/방이름/ 형태의 주소로 WebSocket 연결이 들어오면 ChatConsumer가 처리
    path('ws/chat/<int:user2_id>/', consumers.ChatConsumer.as_asgi()),
    # 새로 추가된 개인 알림 경로
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]