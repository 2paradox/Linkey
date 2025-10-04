# users/views.py (진짜 최종 완성본)

import json
from datetime import date, timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db.models import F, Q
from django.db.models.functions import ExtractYear
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken

from .decorators import login_required
from .models import ChatMessage, Like, Profile


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
            birth_date_str = data.get('birth_date')
            gender = data.get('gender')
            preferred_gender = data.get('preferred_gender')
            age_delta_down = data.get('age_delta_down')
            age_delta_up = data.get('age_delta_up')
            major = data.get('major')
            grade = data.get('grade')

            if not all([username, password, password_confirm, name, email, birth_date_str, gender, preferred_gender, age_delta_down is not None, age_delta_up is not None, major, grade]):
                return JsonResponse({'message': 'ALL_FIELDS_REQUIRED'}, status=400)

            if password != password_confirm:
                return JsonResponse({'message': 'PASSWORDS_DO_NOT_MATCH'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'message': 'USERNAME_ALREADY_EXISTS'}, status=400)
            
            if '@' not in email:
                return JsonResponse({'message': 'INVALID_EMAIL_FORMAT'}, status=400)

            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                if existing_user.is_active:
                    return JsonResponse({'message': 'EMAIL_ALREADY_EXISTS'}, status=400)
                
                time_difference = timezone.now() - existing_user.date_joined
                if time_difference < timedelta(minutes=5):
                    return JsonResponse({'message': 'VERIFICATION_PENDING_PLEASE_WAIT'}, status=400)
                else:
                    existing_user.delete()
            
            user = User(username=username, email=email, first_name=name, is_active=False)
            user.set_password(password)
            user.save()

            Profile.objects.create(
                user=user,
                birth_date=birth_date_str,
                gender=gender,
                preferred_gender=preferred_gender,
                age_preference_down=age_delta_down,
                age_preference_up=age_delta_up,
                major=major,
                grade=grade
            )

            token_generator = PasswordResetTokenGenerator()
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            verify_url = f'http://localhost:8000/api/users/verify-email/{uidb64}/{token}'
            
            subject = '[Linkey] 회원가입 인증을 완료해주세요.'
            message = f'회원가입을 완료하려면 다음 링크를 클릭하세요: {verify_url}'
            recipient_list = [email]
            send_mail(subject, message, from_email=None, recipient_list=recipient_list)
            
            return JsonResponse({'message': 'VERIFICATION_EMAIL_SENT'}, status=201)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'INVALID_METHOD'}, status=405)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'message': 'USERNAME_AND_PASSWORD_REQUIRED'}, status=400)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    token = RefreshToken.for_user(user)
                    return JsonResponse({
                        'message': 'SUCCESS',
                        'access_token': str(token.access_token),
                    }, status=200)
                else:
                    return JsonResponse({'message': 'ACCOUNT_NOT_ACTIVATED'}, status=401)
            else:
                return JsonResponse({'message': 'INVALID_CREDENTIALS'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'INVALID_JSON'}, status=400)
    return JsonResponse({'message': 'INVALID_METHOD'}, status=405)

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        if PasswordResetTokenGenerator().check_token(user, token):
            user.is_active = True
            user.save()
            return JsonResponse({'message': 'SUCCESS_EMAIL_VERIFIED'}, status=200)
        
        return JsonResponse({'message': 'INVALID_TOKEN'}, status=400)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({'message': 'INVALID_USER'}, status=400)

def check_username(request):
    username = request.GET.get('username', None)
    if not username:
        return JsonResponse({'message': 'USERNAME_REQUIRED'}, status=400)
    is_taken = User.objects.filter(username=username).exists()
    return JsonResponse({'is_available': not is_taken})

@login_required
def get_user_info(request):
    user = request.user
    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'email': user.email
    }, status=200)

@csrf_exempt
@login_required
def like_user(request, user_id):
    if request.method == 'POST':
        to_user = get_object_or_404(User, id=user_id)
        from_user = request.user

        if from_user == to_user:
            return JsonResponse({'status': 'error', 'message': 'You cannot like yourself.'}, status=400)

        like, created = Like.objects.get_or_create(from_user=from_user, to_user=to_user)

        if not created:
            return JsonResponse({'status': 'already_liked'})

        is_mutual = Like.objects.filter(from_user=to_user, to_user=from_user).exists()

        if is_mutual:
            return JsonResponse({'status': 'mutual'})
        else:
            return JsonResponse({'status': 'liked'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
def get_likes_received(request):
    user = request.user
    likes = Like.objects.filter(to_user=user)
    users_who_liked_me = [like.from_user for like in likes]
    my_likes_sent_ids = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    
    results = []
    for u in users_who_liked_me:
        status = 'mutual' if u.id in my_likes_sent_ids else 'they_liked_me'
        results.append({
            'id': u.id,
            'username': u.username,
            'name': u.first_name,
            'major': u.profile.major if hasattr(u, 'profile') else None,
            'grade': u.profile.grade if hasattr(u, 'profile') else None,
            'like_status': status
        })
    return JsonResponse({'results': results})

@login_required
def recommend_users(request):
    try:
        user = request.user
        profile = user.profile
        today = date.today()

        users_with_age = User.objects.annotate(age=today.year - ExtractYear('profile__birth_date'))
        my_age = users_with_age.get(id=user.id).age
        my_pref_min_age = my_age + profile.age_preference_down
        my_pref_max_age = my_age + profile.age_preference_up

        base_filter = ~Q(id=user.id) & Q(is_active=True)
        my_preference_filter = Q(age__gte=my_pref_min_age) & Q(age__lte=my_pref_max_age)
        if profile.preferred_gender != 'both':
            my_preference_filter &= Q(profile__gender=profile.preferred_gender)

        mutual_filter = (
            Q(profile__age_preference_down__isnull=False) &
            Q(profile__age_preference_up__isnull=False) &
            Q(age__gte=my_age - F('profile__age_preference_up')) &
            Q(age__lte=my_age - F('profile__age_preference_down'))
        )
        if profile.gender != 'both':
            mutual_filter &= (Q(profile__preferred_gender=profile.gender) | Q(profile__preferred_gender='both'))

        # 이미 '좋아요'를 보냈거나 받은 사용자는 추천 목록에서 제외
        liked_user_ids = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
        users_who_liked_me_ids = Like.objects.filter(to_user=user).values_list('from_user_id', flat=True)
        exclude_ids = set(list(liked_user_ids) + list(users_who_liked_me_ids))

        recommended_users = users_with_age.filter(base_filter & my_preference_filter & mutual_filter).exclude(id__in=exclude_ids).distinct()
        
        results = []
        for r_user in recommended_users:
            results.append({
                'id': r_user.id,
                'username': r_user.username,
                'name': r_user.first_name,
                'major': r_user.profile.major if hasattr(r_user, 'profile') else None,
                'grade': r_user.profile.grade if hasattr(r_user, 'profile') else None,
                'like_status': 'none' # 추천 목록에서는 항상 'none'
            })
        return JsonResponse({'results': results})
    except Profile.DoesNotExist:
        return JsonResponse({'results': [], 'message': 'PROFILE_NOT_FOUND'}, status=200)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@login_required
def get_chat_list(request):
    user = request.user
    sent_to_ids = ChatMessage.objects.filter(sender=user).values_list('receiver_id', flat=True)
    received_from_ids = ChatMessage.objects.filter(receiver=user).values_list('sender_id', flat=True)
    partner_ids = set(list(sent_to_ids) + list(received_from_ids))

    chat_list = []
    for partner_id in partner_ids:
        try:
            partner = User.objects.get(id=partner_id)
            last_message_obj = ChatMessage.objects.filter(
                (Q(sender=user, receiver=partner) | Q(sender=partner, receiver=user))
            ).latest('timestamp')
            unread_count = ChatMessage.objects.filter(sender=partner, receiver=user, is_read=False).count()

            chat_list.append({
                'partner': {'id': partner.id, 'username': partner.username, 'name': partner.first_name},
                'last_message': last_message_obj.content,
                'timestamp': last_message_obj.timestamp.isoformat(),
                'unread_count': unread_count
            })
        except (User.DoesNotExist, ChatMessage.DoesNotExist):
            continue
    chat_list.sort(key=lambda x: x['timestamp'], reverse=True)
    return JsonResponse({'results': chat_list})

# --- HTML 페이지 렌더링 ---
def home(request):
    return render(request, 'index.html')

def main_page(request):
    return render(request, 'main.html')

def chat_list_page(request):
    return render(request, 'chat_list.html')

def chat_room(request, user2_id):
    return render(request, 'chat.html', {'user2_id': user2_id})