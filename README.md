# PPT Translator 🌐

PowerPoint(PPTX) 파일의 한국어 텍스트를 영어로 자동 번역하는 웹 애플리케이션입니다.

## ✨ Features

- **원본 디자인 100% 보존** — 폰트, 색상, 레이아웃 유지
- **듀얼뷰 미리보기** — 원본 vs 번역 나란히 비교
- **번역 근거 제공** — 단어별 의미 분해, 직역/의역 판단
- **표(Table) 지원** — 표 내부 텍스트도 번역
- **미번역 감지** — 번역 실패 항목 자동 하이라이트

## 🚀 Quick Start

### 로컬 실행

```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000 접속
```

### Docker 실행

```bash
docker-compose up -d --build
# http://localhost:5111 접속
```

## 📁 Project Structure

```
├── app.py              # Flask 메인 서버
├── ppt_handler.py      # PPTX 텍스트 추출/교체
├── translator.py       # 번역 엔진 (Google Translate)
├── templates/
│   └── index.html      # 웹 UI
├── static/
│   ├── style.css
│   └── service.css
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🛠 Tech Stack

- **Backend**: Flask, python-pptx
- **Translation**: deep-translator (Google Translate 무료)
- **Frontend**: Vanilla HTML/CSS/JS
- **Deploy**: Docker
