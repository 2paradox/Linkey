from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(token_key):
    try:
        if token_key is None:
            return AnonymousUser()
        
        token = AccessToken(token_key)
        user_id = token.payload['user_id']
        return User.objects.get(id=user_id)
    except (InvalidToken, User.DoesNotExist) as e:
        print(f"!!! TOKEN AUTHENTICATION ERROR: {e}")
        return AnonymousUser()
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR IN TOKEN AUTH: {e}")
        return AnonymousUser()


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]
        
        scope['user'] = await get_user(token)
        return await self.inner(scope, receive, send)