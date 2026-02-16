# PPT Translator - Docker Image
# Python 3.13 슬림 이미지 (용량 최적화)
FROM python:3.13-slim

# 한글 인코딩 지원
ENV LANG=C.UTF-8

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 먼저 복사 (Docker 캐시 최적화)
# NOTE: requirements.txt는 server/ 폴더에 위치 (Cloudflare Pages 빌드 충돌 방지)
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY app.py .
COPY ppt_handler.py .
COPY translator.py .
COPY templates/ templates/
COPY static/ static/

# uploads/outputs 디렉토리 생성
RUN mkdir -p uploads outputs

# 포트 노출
EXPOSE 5000

# 서버 실행
CMD ["python", "app.py"]
