# PPT Translator 🌐

<p align="center">
  <img src="./actionscreen.gif" alt="PPT Translator Demo" width="800">
</p>

---

## 💡 왜 만들었나요?

한국어로 작성된 PowerPoint 자료를 영어로 번역해야 할 일이 자주 있었습니다.

매번 슬라이드를 하나씩 열어 텍스트를 복사 → 번역기에 붙여넣기 → 다시 PPT에 입력하는 과정이 **너무 비효율적**이었습니다. 특히 표, 차트, 그룹 도형 안의 텍스트까지 일일이 수작업으로 바꾸다 보면 시간도, 정확도도 떨어졌습니다.

> *"파일 하나만 올리면 디자인은 그대로 유지하면서 자동 번역되면 좋겠다"*

그래서 직접 만들었습니다. 🚀

- 📄 PPTX 파일 업로드 한 번으로 **전체 텍스트 자동 번역**
- 🎨 폰트, 색상, 레이아웃 등 **원본 서식 100% 보존**
- 📊 표(Table), 그룹 도형 안 텍스트까지 **빠짐없이 처리**
- 🔍 번역이 왜 이렇게 됐는지 **근거(단어별 분해)까지 제공**

---

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
