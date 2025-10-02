# users/models.py

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
    ]
    PREFERRED_GENDER_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
        ('both', '모두'),
    ]
    # 학과 선택지를 추가합니다.
    MAJOR_CHOICES = [
        ('chemistry', 'Chemistry'),
        ('computer_engineering', 'Computer Engineering'),
        ('electronics', 'Electronics'),
    ]
    # 기본 User 모델과 1:1로 연결합니다.
    # User가 삭제되면 Profile도 함께 삭제됩니다 (on_delete=models.CASCADE).
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # 추가할 필드들
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)

    preferred_gender = models.CharField(max_length=10, choices=PREFERRED_GENDER_CHOICES, null=True, blank=True)

    # 2. 원하는 연령 범위
    age_preference_down = models.IntegerField(null=True, blank=True) # 아래로 나이 차이
    age_preference_up = models.IntegerField(null=True, blank=True)   # 위로 나이 차이
    # 3. 학교/학과/학년
    major = models.CharField(max_length=100, choices=MAJOR_CHOICES, null=True, blank=True)
    grade = models.PositiveIntegerField(null=True, blank=True)
    def __str__(self):
        return self.user.username