import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter

# 장고 설정을 먼저 불러옵니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_server.settings')
django.setup()

# 장고 설정이 로드된 후에 다른 모듈들을 불러옵니다.
from django.core.asgi import get_asgi_application
from users.middleware import TokenAuthMiddleware
import users.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(
            users.routing.websocket_urlpatterns
        )
    ),
})