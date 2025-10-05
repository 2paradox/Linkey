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

    image = models.ImageField(upload_to='profile_pics', default='default.jpg')




    def __str__(self):
        return self.user.username

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'From {self.sender.username} to {self.receiver.username}: {self.content[:20]}'

class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    # 한 사람이 다른 사람에게 여러 번 '좋아요'를 누를 수 없도록 제약 조건 추가
    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f'{self.from_user.username} likes {self.to_user.username}'