from django.contrib import admin
from .models import Profile # 우리가 만든 Profile 모델을 가져옵니다.

# 관리자 사이트에 Profile 모델을 등록합니다.
admin.site.register(Profile)