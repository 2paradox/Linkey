# 1. 파이썬 3.11 버전을 기반으로 이미지를 만듭니다.
FROM python:3.11

# 2. 컨테이너 내부의 환경 변수를 설정합니다.
ENV PYTHONUNBUFFERED 1

# 3. 컨테이너 내부의 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# 4. requirements.txt 파일을 복사합니다.
COPY requirements.txt .

# 5. requirements.txt에 있는 라이브러리들을 설치합니다.
RUN pip install -r requirements.txt

# 6. 현재 폴더의 모든 파일을 컨테이너의 /app 폴더로 복사합니다.
COPY . .

# 7. 정적 파일들을 한 곳으로 모으는 collectstatic 명령어를 실행합니다.
RUN python manage.py collectstatic --no-input