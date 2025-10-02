from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .decorators import login_required
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta
from datetime import date
from datetime import date
from django.db.models import Q
from .decorators import login_required
from django.db.models.functions import ExtractYear

import json


@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            password_confirm = data.get('password_confirm')
            name = data.get('name')
            email = data.get('email')
            birth_date = data.get('birth_date')
            gender = data.get('gender')
            preferred_gender = data.get('preferred_gender')
            min_age_preference = data.get('min_age_preference')
            max_age_preference = data.get('max_age_preference')
            major = data.get('major')
            grade = data.get('grade')

            if not all([username, password, password_confirm, name, email, birth_date, gender, preferred_gender, min_age_preference, max_age_preference, university, major, grade]):
                return JsonResponse({'message': 'ALL_FIELDS_REQUIRED'}, status=400)

            if password != password_confirm:
                return JsonResponse({'message': 'PASSWORDS_DO_NOT_MATCH'}, status=400)
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'message': 'USERNAME_ALREADY_EXISTS'}, status=400)
            
            # '@' 포함 여부 검사는 여기에 추가하면 더 좋습니다.
            if '@' not in email:
                return JsonResponse({'message': 'INVALID_EMAIL_FORMAT'}, status=400)

            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                # 1. 이미 존재하는 활성 유저인 경우
                if existing_user.is_active:
                    return JsonResponse({'message': 'EMAIL_ALREADY_EXISTS'}, status=400)
                
                # 2. 5분이 지나지 않은 비활성 유저인 경우
                time_difference = timezone.now() - existing_user.date_joined
                if time_difference < timedelta(minutes=5):
                    return JsonResponse({'message': 'VERIFICATION_PENDING_PLEASE_WAIT'}, status=400)
                
                # 3. 5분이 지난 비활성 유저(유령 계정)인 경우, 삭제하고 계속 진행
                else:
                    existing_user.delete()

            ALLOWED_DOMAINS = ["vt.edu", "gmail.com"]
            domain = email.split('@')[-1]

            if domain not in ALLOWED_DOMAINS:
                return JsonResponse({'message': 'UNAUTHORIZED_EMAIL_DOMAIN'}, status=400)

            try:
                existing_user = User.objects.get(username=email)
                
                # 1. 이미 존재하는 활성 유저인 경우
                if existing_user.is_active:
                    return JsonResponse({'message': 'EMAIL_ALREADY_EXISTS'}, status=400)
                
                # 2. 비활성 유저인 경우, 생성 시간 확인
                time_difference = timezone.now() - existing_user.date_joined
                if time_difference < timedelta(minutes=5):
                    # 2-1. 5분이 지나지 않았다면, 재가입 방지
                    return JsonResponse({'message': 'VERIFICATION_PENDING_PLEASE_WAIT'}, status=400)
                else:
                    # 2-2. 5분이 지났다면, 기존 비활성 계정 삭제 후 계속 진행
                    existing_user.delete()

            except User.DoesNotExist:
                # 사용자가 존재하지 않으면 그냥 통과
                pass

            
            # --- 여기서부터 로직 변경 ---
            user = User(
                username=username,
                email=email,
                first_name=name,
                is_active=False
            )
            user.set_password(password)
            user.save()

            Profile.objects.create(
                user=user,
                birth_date=birth_date,
                gender=gender,
                preferred_gender=preferred_gender,
                age_preference_down=data.get('age_delta_down'),
                age_preference_up=data.get('age_delta_up'),
                university=university,
                major=major,
                grade=grade
            )

            # 1. 인증 링크에 포함될 토큰 생성
            token_generator = PasswordResetTokenGenerator()
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            verify_url = f'http://127.0.0.1:8000/api/users/verify-email/{uidb64}/{token}'

            # 2. 인증 이메일 발송 (message 부분 수정)
            subject = '[나의 앱] 회원가입 인증을 완료해주세요.'
            message = f'회원가입을 완료하려면 다음 링크를 클릭하세요: {verify_url}'
            from_email = 'noreply@my-app.com'
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list)

            # 3. 성공 응답 메시지 변경
            return JsonResponse({'message': 'VERIFICATION_EMAIL_SENT'}, status=201)

        except Exception as e: # 더 넓은 범위의 예외 처리
            return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'INVALID_METHOD'}, status=405)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username') # 'email' 대신 'username'을 받습니다.
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'message': 'USERNAME_AND_PASSWORD_REQUIRED'}, status=400)

            # 장고의 내장 함수 authenticate를 사용해 사용자 인증
            # username으로 email을 사용했으므로, username 필드에 email 값을 전달합니다.
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # --- 토큰 생성 로직으로 변경 ---
                if user.is_active:
                    token = RefreshToken.for_user(user)
                    return JsonResponse({
                        'message': 'SUCCESS',
                        'access_token': str(token.access_token),
                    }, status=200)
                else:
                    return JsonResponse({'message': 'ACCOUNT_NOT_ACTIVATED'}, status=401)
            else:
                # 인증에 실패했을 경우 (사용자가 없거나, 비밀번호가 틀림)
                return JsonResponse({'message': 'INVALID_CREDENTIALS'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'INVALID_JSON'}, status=400)

    return JsonResponse({'message': 'INVALID_METHOD'}, status=405)

@login_required # <-- 데코레이터 적용!
def get_user_info(request):
    # 데코레이터가 request.user에 사용자 정보를 넣어줬으므로 바로 사용 가능
    user = request.user 
    return JsonResponse({
        'id': user.id,
        'email': user.email,
        'username': user.username
    }, status=200)

def verify_email(request, uidb64, token):
    try:
        # 1. uidb64를 디코딩해서 사용자 ID를 얻음
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # 2. 토큰이 유효한지 확인
        token_generator = PasswordResetTokenGenerator()
        if token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return JsonResponse({'message': 'SUCCESS_EMAIL_VERIFIED'}, status=200)
        
        return JsonResponse({'message': 'INVALID_TOKEN'}, status=400)

    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({'message': 'INVALID_USER'}, status=400)

def check_username(request):
    # GET 요청의 쿼리 파라미터에서 username을 가져옵니다.
    username = request.GET.get('username', None)
    if username is None:
        return JsonResponse({'message': 'USERNAME_REQUIRED'}, status=400)

    is_taken = User.objects.filter(username=username).exists()
    
    # is_taken이 True이면 (이미 존재하면) is_available은 False가 됩니다.
    return JsonResponse({'is_available': not is_taken})

@login_required
def recommend_users(request):
    user = request.user
    profile = user.profile
    today = date.today()

    # 1. 모든 사용자의 '나이'를 실시간으로 계산하여 주석(annotate)으로 추가
    #    이렇게 하면 데이터베이스 단에서 효율적으로 나이를 비교할 수 있습니다.
    users_with_age = User.objects.annotate(
        birth_year=ExtractYear('profile__birth_date')
    ).annotate(
        age=today.year - ExtractYear('profile__birth_date')
    )

    # 2. 현재 로그인한 유저의 나이와 선호도
    my_age = users_with_age.get(id=user.id).age
    my_pref_min_age = my_age + profile.age_preference_down
    my_pref_max_age = my_age + profile.age_preference_up

    # 3. 필터링
    # - 기본 조건: 나 자신 제외, 같은 대학, 활성 계정
    base_filter = ~Q(id=user.id) & Q(is_active=True)
    
    # - 나의 선호도 조건: 상대방의 나이가 나의 선호 범위에 있어야 함
    my_preference_filter = Q(age__gte=my_pref_min_age) & Q(age__lte=my_pref_max_age)
    if profile.preferred_gender != 'both':
        my_preference_filter &= Q(profile__gender=profile.preferred_gender)

    # - 상대방의 선호도 조건 (상호 매칭)
    #   (상대방의 나이 + 상대방의 아래 나이차 <= 나의 나이 <= 상대방의 나이 + 상대방의 위 나이차)
    #   이 부분은 복잡한 F() 표현식을 사용합니다.
    from django.db.models import F
    mutual_filter = Q(profile__age_preference_down__isnull=False) & Q(profile__age_preference_up__isnull=False)
    mutual_filter &= Q(age__gte=my_age - F('profile__age_preference_up'))
    mutual_filter &= Q(age__lte=my_age - F('profile__age_preference_down'))

    if profile.gender != 'both':
         mutual_filter &= (Q(profile__preferred_gender=profile.gender) | Q(profile__preferred_gender='both'))

    # 모든 필터를 합쳐서 최종 쿼리 실행
    recommended_users = users_with_age.filter(base_filter & my_preference_filter & mutual_filter)
    
    # 4. 결과 데이터 가공 (이전과 동일)
    results = [{'username': r_user.username, 'name': r_user.first_name, 'major': r_user.profile.major, 'grade': r_user.profile.grade} for r_user in recommended_users]

    return JsonResponse({'results': results})