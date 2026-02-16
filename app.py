"""
PPT 한글→영어 번역 웹 애플리케이션
Flask 메인 서버 (v4 - Cloudflare Pages 프론트엔드 지원)
"""

import os
import uuid
import json
import time
import logging
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

from ppt_handler import extract_texts, create_translated_pptx
from translator import translate_texts_batch, contains_korean

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB (대용량 PPT 지원)

# CORS 설정: Cloudflare Pages에서의 API 호출 허용
CORS(app, origins=[
    "https://ppt-translate.pages.dev",
    "http://localhost:5000",
    "http://localhost:8080",
    "http://127.0.0.1:5000",
], supports_credentials=True)

# 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/upload', methods=['POST'])
@app.route('/api/upload', methods=['POST'])
def upload_and_translate():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "파일이 업로드되지 않았습니다."}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"success": False, "error": "파일이 선택되지 않았습니다."}), 400

    if not file.filename.lower().endswith('.pptx'):
        return jsonify({
            "success": False,
            "error": "PPTX 파일만 지원합니다. (.ppt는 PowerPoint에서 .pptx로 변환 후 업로드해주세요)"
        }), 400

    # 파일 저장
    file_id = str(uuid.uuid4())[:8]
    original_name = file.filename
    safe_name = f"{file_id}_{original_name}"
    upload_path = os.path.join(UPLOAD_DIR, safe_name)
    file.save(upload_path)

    start_time = time.time()

    try:
        # 1. 텍스트 추출
        logger.info(f"[{file_id}] 텍스트 추출 시작: {original_name}")
        extracted = extract_texts(upload_path)
        extract_time = time.time() - start_time
        logger.info(f"[{file_id}] 텍스트 추출 완료: 총 {extracted['total_texts']}개, 한글 {extracted['korean_texts']}개")

        # 2. 번역 대상 텍스트 수집
        all_texts = []
        for slide in extracted["slides"]:
            for element in slide["elements"]:
                for text_info in element["texts"]:
                    all_texts.append({
                        "id": text_info["id"],
                        "text": text_info["text"],
                        "has_korean": text_info["has_korean"],
                        "slide_number": slide["slide_number"],
                        "shape": element["shape_name"],
                        "type": element["shape_type"]
                    })

        # 3. 배치 번역
        translate_start = time.time()
        logger.info(f"[{file_id}] 번역 시작: {len(all_texts)}개 텍스트")
        
        translation_results = translate_texts_batch(
            [{"id": t["id"], "text": t["text"]} for t in all_texts]
        )
        translate_time = time.time() - translate_start
        logger.info(f"[{file_id}] 번역 완료: {translate_time:.2f}초 소요")

        # 결과를 id로 인덱싱
        result_map = {r["id"]: r for r in translation_results}

        # 4. 슬라이드별 비교 데이터 + 미리보기 데이터 구성
        translations_for_ppt = {}
        comparison_data = []
        untranslated_count = 0
        translated_count = 0

        for slide in extracted["slides"]:
            slide_comparisons = {
                "slide_number": slide["slide_number"],
                "items": [],
                "shapes_visual": slide.get("shapes_visual", [])  # 미리보기용
            }

            for element in slide["elements"]:
                for text_info in element["texts"]:
                    tid = text_info["id"]
                    r = result_map.get(tid)

                    if r:
                        is_untranslated = r.get("untranslated", False)
                        if text_info["has_korean"]:
                            if not is_untranslated:
                                translations_for_ppt[tid] = r["translated"]
                                translated_count += 1
                            else:
                                untranslated_count += 1
                                logger.warning(f"[{file_id}] 미번역: '{r['original'][:30]}...'")

                        slide_comparisons["items"].append({
                            "id": tid,
                            "shape": element["shape_name"],
                            "type": element["shape_type"],
                            "original": r["original"],
                            "translated": r["translated"],
                            "word_breakdown": r.get("word_breakdown", []),
                            "translation_type": r.get("translation_type", "원문 유지"),
                            "untranslated": is_untranslated
                        })

            if slide_comparisons["items"]:
                comparison_data.append(slide_comparisons)

            # 미리보기 shapes에 번역 결과 반영
            for sv in slide_comparisons["shapes_visual"]:
                for st in sv["texts"]:
                    r = result_map.get(st["id"])
                    if r:
                        st["translated"] = r["translated"]
                        st["untranslated"] = r.get("untranslated", False)

        # 5. 번역 PPT 생성
        ppt_start = time.time()
        output_name = f"translated_{file_id}_{original_name}"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        create_translated_pptx(upload_path, translations_for_ppt, output_path)
        ppt_time = time.time() - ppt_start

        total_time = time.time() - start_time
        logger.info(f"[{file_id}] 전체 완료: {total_time:.1f}초 (추출:{extract_time:.1f}s 번역:{translate_time:.1f}s PPT:{ppt_time:.1f}s)")

        return jsonify({
            "success": True,
            "filename": output_name,
            "original_name": original_name,
            "slides": comparison_data,
            "slide_ratio": extracted.get("slide_ratio", 1.333),
            "stats": {
                "total_slides": len(extracted["slides"]),
                "total_texts": extracted["total_texts"],
                "korean_texts": extracted["korean_texts"],
                "translated_texts": translated_count,
                "untranslated_texts": untranslated_count
            },
            "timing": {
                "total_seconds": round(total_time, 1),
                "extract_seconds": round(extract_time, 1),
                "translate_seconds": round(translate_time, 1),
                "ppt_generate_seconds": round(ppt_time, 1)
            }
        })

    except Exception as e:
        logger.error(f"[{file_id}] 오류 발생: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"번역 중 오류가 발생했습니다: {str(e)}"
        }), 500


@app.route('/download/<filename>')
@app.route('/api/download/<filename>')
def download_file(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "파일을 찾을 수 없습니다."}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("  PPT 한글→영어 번역기 v4 (Cloudflare Pages 지원)")
    print("  로컬 접속: http://localhost:5000")
    print("  Cloudflare: https://ppt-translate.pages.dev")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
