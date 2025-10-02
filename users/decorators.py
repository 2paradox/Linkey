from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.models import User
import jwt

def login_required(func):
    def wrapper(request, *args, **kwargs):
        try:
            # 1. 요청 헤더에서 토큰 가져오기
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return JsonResponse({'message': 'TOKEN_REQUIRED'}, status=401)

            # "Bearer <token>" 형식에서 토큰 부분만 추출
            token = auth_header.split(' ')[1]
            
            # 2. 토큰 디코딩 및 검증 (settings.SECRET_KEY 사용)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # 3. 유효한 사용자 정보를 request 객체에 추가
            user = User.objects.get(id=payload['user_id'])
            request.user = user

        except jwt.exceptions.DecodeError:
            return JsonResponse({'message': 'INVALID_TOKEN'}, status=401)
        except User.DoesNotExist:
            return JsonResponse({'message': 'USER_NOT_FOUND'}, status=404)
        except IndexError:
            return JsonResponse({'message': 'INVALID_TOKEN_FORMAT'}, status=401)

        return func(request, *args, **kwargs)
    return wrapper